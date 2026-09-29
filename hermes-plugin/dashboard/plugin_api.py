"""Company OS local projection backend.

Mounted by Hermes at /api/plugins/company-os/. Read-only by design: it reads
local z0/Kerdoios/Tokenomics/AgentsView/Kubernetes state and emits a sanitized
projection. It never returns prompts, tool bodies, credentials, or raw memory.
"""
from __future__ import annotations

import json
import os
import shutil
import sqlite3
import subprocess
import time
from pathlib import Path
from typing import Any

from fastapi import APIRouter

router = APIRouter()

SCHEMA = "company_os.snapshot.v1"
HERMES_HOME = Path(os.environ.get("HERMES_HOME", "~/.hermes")).expanduser()
Z0_HOME = Path(os.environ.get("Z0INT_HOME", "~/.z0int")).expanduser()
MAX_EVENTS = 40
KNOWN_AGENTS = ("hermes", "omp", "dsh", "omo", "codex", "claude", "opencode", "pi")


def _now() -> float:
    return time.time()


def _read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _tail_jsonl(path: Path, limit: int = 1000) -> list[dict[str, Any]]:
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()[-limit:]
    except OSError:
        return []
    out: list[dict[str, Any]] = []
    for line in lines:
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(row, dict):
            out.append(row)
    return out


def _source(status: str, **extra: Any) -> dict[str, Any]:
    return {"status": status, **extra}


def _run_json(argv: list[str], timeout: float = 2.0) -> tuple[Any, str | None]:
    try:
        proc = subprocess.run(argv, capture_output=True, text=True, timeout=timeout, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return None, type(exc).__name__
    if proc.returncode != 0:
        return None, f"exit:{proc.returncode}"
    try:
        return json.loads(proc.stdout), None
    except json.JSONDecodeError:
        return None, "invalid_json"


def _k8s() -> tuple[dict[str, Any], dict[str, Any]]:
    if not shutil.which("kubectl"):
        return {"available": False, "pods": [], "nodes": []}, _source("unavailable", reason="kubectl_missing")

    pods_raw, pods_err = _run_json(["kubectl", "get", "pods", "-A", "-o", "json"])
    nodes_raw, nodes_err = _run_json(["kubectl", "get", "nodes", "-o", "json"])
    pods: list[dict[str, Any]] = []
    for item in (pods_raw or {}).get("items", []):
        meta = item.get("metadata") or {}
        status = item.get("status") or {}
        spec = item.get("spec") or {}
        cs = status.get("containerStatuses") or []
        pods.append({
            "namespace": meta.get("namespace"),
            "name": meta.get("name"),
            "phase": status.get("phase"),
            "node": spec.get("nodeName"),
            "ready": sum(1 for c in cs if c.get("ready")),
            "containers": len(cs),
            "restarts": sum(int(c.get("restartCount") or 0) for c in cs),
            "created_at": meta.get("creationTimestamp"),
        })
    nodes: list[dict[str, Any]] = []
    for item in (nodes_raw or {}).get("items", []):
        meta = item.get("metadata") or {}
        status = item.get("status") or {}
        ready = next((c.get("status") for c in status.get("conditions", []) if c.get("type") == "Ready"), None)
        nodes.append({
            "name": meta.get("name"),
            "ready": ready == "True",
            "cpu": (status.get("capacity") or {}).get("cpu"),
            "memory": (status.get("capacity") or {}).get("memory"),
        })
    status = "ok" if pods_err is None and nodes_err is None else "degraded"
    return {"available": True, "pods": pods, "nodes": nodes}, _source(
        status, pods_error=pods_err, nodes_error=nodes_err, observed_at=_now()
    )


def _process_fleet() -> list[dict[str, Any]]:
    try:
        proc = subprocess.run(
            ["ps", "-eo", "pid=,comm=,etimes="],
            capture_output=True, text=True, timeout=1.0, check=False
        )
    except (OSError, subprocess.TimeoutExpired):
        return []
    if proc.returncode != 0:
        return []
    rows: list[dict[str, Any]] = []
    for raw in proc.stdout.splitlines():
        parts = raw.split()
        if len(parts) < 3:
            continue
        pid, comm, age = parts[0], parts[1], parts[2]
        low = comm.lower()
        if not any(name in low for name in KNOWN_AGENTS):
            continue
        rows.append({"pid": int(pid), "name": comm, "age_s": int(age), "status": "running"})
    return rows[:100]


def _z0_control() -> tuple[dict[str, Any] | None, dict[str, Any]]:
    override = os.environ.get("COMPANY_OS_Z0_SNAPSHOT")
    path = Path(override).expanduser() if override else Z0_HOME / "state" / "control_snapshot.json"
    data = _read_json(path)
    if isinstance(data, dict):
        return data, _source("ok", path=str(path), observed_at=path.stat().st_mtime)
    return None, _source("missing", path=str(path))


def _receipt_paths() -> list[Path]:
    override = os.environ.get("COMPANY_OS_RECEIPTS")
    if override:
        return [Path(p).expanduser() for p in override.split(os.pathsep) if p]
    root = Z0_HOME / "receipts"
    try:
        return sorted(root.glob("*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True)[:12]
    except OSError:
        return []


def _receipt_rows() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    paths = [p for p in _receipt_paths() if p.is_file()]
    rows: list[dict[str, Any]] = []
    for path in paths:
        for row in _tail_jsonl(path, 500):
            row = dict(row)
            row["_source_file"] = path.name
            rows.append(row)
    rows.sort(key=lambda r: float(r.get("recorded_at") or r.get("timestamp") or 0), reverse=True)
    return rows[:1500], _source("ok" if paths else "missing", files=[p.name for p in paths])


def _event(row: dict[str, Any]) -> dict[str, Any]:
    extra = row.get("extra") if isinstance(row.get("extra"), dict) else {}
    provider = row.get("provider") or extra.get("provider")
    model = row.get("model") or extra.get("model")
    status = extra.get("status") or row.get("status")
    verified = row.get("verified_success")
    if verified is None:
        verified = extra.get("verified_success")
    return {
        "ts": row.get("recorded_at") or row.get("timestamp"),
        "trace_id": row.get("trace_id") or extra.get("caller_trace_id"),
        "harness": row.get("harness_id") or extra.get("harness"),
        "capability": row.get("capability_id") or row.get("function") or extra.get("function"),
        "provider": provider,
        "model": model,
        "status": status,
        "verified": verified,
        "source": row.get("_source_file"),
        "governed": bool(extra.get("authority_dispatch_id") or extra.get("admission_token") or str(row.get("trace_id") or "").startswith("dispatch-")),
    }


def _economics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    input_tokens = output_tokens = cached_tokens = actual_tokens = 0
    cost = 0.0
    verified = 0
    measured = 0
    governed = 0
    for row in rows:
        extra = row.get("extra") if isinstance(row.get("extra"), dict) else {}
        def num(key: str) -> float:
            value = row.get(key)
            if value is None:
                value = extra.get(key)
            try:
                return float(value or 0)
            except (TypeError, ValueError):
                return 0.0
        input_tokens += int(num("input_tokens"))
        output_tokens += int(num("output_tokens"))
        cached_tokens += int(num("cached_input_tokens"))
        actual_tokens += int(num("actual_tokens"))
        cost += num("actual_cost") or num("cost_usd") or num("provider_reported_cost_usd")
        if row.get("verified_success") is True or extra.get("verified_success") is True:
            verified += 1
        if row.get("measurement_state") == "complete" or extra.get("measurement_state") == "complete":
            measured += 1
        if extra.get("authority_dispatch_id") or extra.get("admission_token"):
            governed += 1
    return {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cached_input_tokens": cached_tokens,
        "actual_tokens": actual_tokens or (input_tokens + output_tokens),
        "observed_cost_usd": round(cost, 6),
        "verified_events": verified,
        "measurement_complete_events": measured,
        "governed_events": governed,
        "sampled_events": len(rows),
    }


def _quota() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    path = Path(os.environ.get(
        "COMPANY_OS_KERDOIOS_LEDGER",
        str(HERMES_HOME / "cache" / "kerdoios" / "quota_ledger.json")
    )).expanduser()
    data = _read_json(path)
    if not isinstance(data, dict):
        return [], _source("missing", path=str(path))
    out: list[dict[str, Any]] = []
    entries = data.get("entries") or []
    if isinstance(entries, dict):
        entries = list(entries.values())
    for entry in entries if isinstance(entries, list) else []:
        if not isinstance(entry, dict):
            continue
        out.append({
            "provider": entry.get("provider"),
            "model": entry.get("model"),
            "updated_at": entry.get("updated_at"),
            "quota": entry.get("quota") if isinstance(entry.get("quota"), dict) else {},
        })
    return out, _source("ok", path=str(path), entries=len(out), observed_at=data.get("saved_at"))


def _agentsview() -> tuple[dict[str, Any], dict[str, Any]]:
    home = Path(os.environ.get("AGENTSVIEW_HOME", "~/.agentsview")).expanduser()
    configured = os.environ.get("COMPANY_OS_AGENTSVIEW_DB")
    db = Path(configured).expanduser() if configured else None
    if db is None and home.is_file() and home.suffix == ".db":
        db = home
    if db is None and home.is_dir():
        candidates = list(home.glob("*.db")) + list(home.glob("**/sessions.db"))
        db = candidates[0] if candidates else None
    state = {
        "cli": bool(shutil.which("agentsview")),
        "home_exists": home.exists(),
        "home_symlink": home.is_symlink(),
        "database": str(db) if db else None,
        "sessions": None,
        "messages": None,
    }
    if db and db.is_file():
        try:
            conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True, timeout=0.5)
            names = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            if "sessions" in names:
                state["sessions"] = int(conn.execute("SELECT COUNT(*) FROM sessions").fetchone()[0])
            if "messages" in names:
                state["messages"] = int(conn.execute("SELECT COUNT(*) FROM messages").fetchone()[0])
            conn.close()
            return state, _source("ok", observed_at=db.stat().st_mtime)
        except (sqlite3.Error, OSError) as exc:
            return state, _source("degraded", reason=type(exc).__name__)
    status = "degraded" if state["cli"] or state["home_exists"] else "unavailable"
    return state, _source(status)


def _fleet(control: dict[str, Any] | None, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if control and isinstance(control.get("fleet"), list):
        return control["fleet"][:200]
    latest: dict[str, dict[str, Any]] = {}
    for row in rows:
        event = _event(row)
        tid = event.get("trace_id")
        if not tid or tid in latest:
            continue
        latest[str(tid)] = event
    derived = list(latest.values())[:100]
    processes = _process_fleet()
    seen = {str(x.get("harness") or x.get("name") or "").lower() for x in derived}
    for proc in processes:
        if proc["name"].lower() not in seen:
            derived.append(proc)
    return derived[:200]


def build_snapshot() -> dict[str, Any]:
    control, z0_source = _z0_control()
    rows, receipt_source = _receipt_rows()
    capacity, quota_source = _quota()
    memory, memory_source = _agentsview()
    k8s, k8s_source = _k8s()
    events = [_event(r) for r in rows[:MAX_EVENTS]]
    sources = {
        "z0": z0_source,
        "receipts": receipt_source,
        "kerdoios": quota_source,
        "memory": memory_source,
        "k8s": k8s_source,
    }
    overall = "ok" if all(v["status"] == "ok" for v in sources.values()) else "degraded"
    return {
        "schema": SCHEMA,
        "generated_at": _now(),
        "status": overall,
        "sources": sources,
        "fleet": _fleet(control, rows),
        "capacity": capacity,
        "economics": _economics(rows),
        "memory": memory,
        "k8s": k8s,
        "flow": events,
        "control": {
            "available": control is not None,
            "schema": control.get("schema") if control else None,
        },
    }


@router.get("/snapshot")
async def snapshot():
    return build_snapshot()


@router.get("/health")
async def health():
    snap = build_snapshot()
    return {"schema": SCHEMA, "status": snap["status"], "sources": snap["sources"]}
