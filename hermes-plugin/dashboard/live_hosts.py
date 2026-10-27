"""Company OS live host map: every fleet host and what runs under it.

Read-only. Joins sources that already exist on the controller host:

- fleet registry   /workspace/.files-k3s/config/fleet/nodes.yaml (scripts/fleet)
- fleet health     ~/.local/state/fleet/health/<node>.json (`fleet health` timer)
- fleet inventory  newest operations/fleet/inventory-*.json
- tailscale        `tailscale status --json`
- k3s              `kubectl --kubeconfig ~/.kube/k3s.yaml get nodes,pods`
- local processes  Hermes profiles/gateways, z0live, Dash, Tern daemon/remote serve
- shadow network   ~/.z0int shadow decision/receipt ledgers (tail only)
- z0archy          generated/graph.json (declared world model of kvnloo/z0)
- burn-pace        `burn-pace --json` (frontier subscription pace)
- Kerdoios         ~/.cache/kerdoios/inventory.json (provider offers)

Boundary: infrastructure only. Chats, sessions, approvals and agent steering
belong to Dash; this module never reads session titles or transcripts.

Nothing here writes, schedules or dispatches. `local=True` keeps real names for
the owner's own loopback view; `local=False` replaces every name, address,
title and pod with an opaque alias, which is what public exports get.
"""
from __future__ import annotations

import glob
import hashlib
import json
import os
import re
import shutil
import sqlite3
import subprocess
import time
from pathlib import Path
from typing import Any

MAX_BYTES = 1048576
MAX_ROWS = 64
NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9._@:+/ -]{0,95}")
SAFE_TOKEN = re.compile(r"[a-z0-9][a-z0-9_.-]{0,31}")
CANONICAL_ROLES = ("voice_intake", "first_mate", "hitl", "linear", "hermes_kanban",
                   "third_mate", "oss_lane", "second_mate")


def _now() -> float:
    return time.time()


def alias(v: Any) -> str | None:
    if v is None or v == "":
        return None
    return "ref-" + hashlib.sha256(str(v).encode()).hexdigest()[:16]


def _name(v: Any) -> str | None:
    """A display name for the owner's local view: bounded, printable, no control bytes."""
    if not isinstance(v, str):
        return None
    v = v.strip()
    return v if NAME.fullmatch(v) else (v[:96].encode("ascii", "replace").decode() if v else None)


def _num(v: Any) -> float | int | None:
    return v if type(v) in (int, float) and v == v and abs(v) < 2**53 else None


def source(status: str, observed_at: float | None = None, **extra: Any) -> dict[str, Any]:
    age = max(0.0, _now() - observed_at) if observed_at else None
    fresh = "unknown" if age is None else "fresh" if age <= 300 else "stale"
    return {"status": status, "checked_at": _now(), "observed_at": observed_at, "age_s": age,
            "freshness": fresh, **extra}


def _run(argv: list[str], timeout: float = 3.0, env: dict[str, str] | None = None) -> tuple[str | None, str | None]:
    if not shutil.which(argv[0]):
        return None, "missing"
    try:
        proc = subprocess.run(argv, capture_output=True, text=True, timeout=timeout, check=False,
                              env={**os.environ, **(env or {})})
    except (OSError, subprocess.TimeoutExpired) as exc:
        return None, type(exc).__name__
    if proc.returncode != 0:
        return None, f"exit:{proc.returncode}"
    if len(proc.stdout) > MAX_BYTES:
        return None, "oversize"
    return proc.stdout, None


def _json_cmd(argv: list[str], timeout: float = 3.0, env: dict[str, str] | None = None) -> tuple[Any, str | None]:
    out, err = _run(argv, timeout, env)
    if err:
        return None, err
    try:
        return json.loads(out or ""), None
    except ValueError:
        return None, "invalid_json"


def _read_json(path: Path) -> Any:
    with open(path, "rb") as f:
        raw = f.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise ValueError("oversize")
    return json.loads(raw)


# ---------------------------------------------------------------- fleet sources

def fleet_registry() -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    path = Path(os.environ.get("COMPANY_OS_FLEET_REGISTRY", "/workspace/.files-k3s/config/fleet/nodes.yaml"))
    try:
        import yaml  # type: ignore
        reg = yaml.safe_load(path.read_text()[:MAX_BYTES]) or {}
        nodes = {}
        for name, n in (reg.get("nodes") or {}).items():
            if not isinstance(n, dict):
                continue
            android = n.get("android") if isinstance(n.get("android"), dict) else {}
            nodes[str(name)] = {"role": n.get("role"), "kind": n.get("kind", "linux"),
                                "tailnet_ip": n.get("tailnet_ip"), "arch": n.get("arch"),
                                "classes": [str(c) for c in n.get("classes") or []][:8],
                                "taints": [str(c) for c in n.get("taints") or []][:4],
                                "aliases": [str(c) for c in n.get("aliases") or []][:4],
                                "model": n.get("model"), "android_ip": android.get("adb_host")}
        reg = reg if isinstance(reg, dict) else {}
        candidates = {str(k): (v or {}).get("note") for k, v in (reg.get("candidates") or {}).items()}
        return {"nodes": nodes, "candidates": candidates}, source("ok", path.stat().st_mtime, path_kind="fleet_registry")
    except FileNotFoundError:
        return {"nodes": {}, "candidates": {}}, source("unavailable", reason="registry_missing")
    except Exception:
        return {"nodes": {}, "candidates": {}}, source("degraded", reason="registry_unreadable")


def fleet_health() -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    root = Path(os.environ.get("COMPANY_OS_FLEET_HEALTH", str(Path.home() / ".local/state/fleet/health")))
    out: dict[str, dict[str, Any]] = {}
    newest = None
    for path in sorted(root.glob("*.json"))[:MAX_ROWS]:
        if path.name == "state.json":
            continue
        try:
            row = _read_json(path)
        except Exception:
            continue
        if isinstance(row, dict) and isinstance(row.get("node"), str):
            out[row["node"]] = row
            ts = _num(row.get("ts"))
            newest = max(newest or 0, ts or 0) or newest
    if not out:
        return {}, source("unavailable", reason="no_health_files")
    return out, source("ok", newest, coverage="fleet health timer, every 2 minutes")


def fleet_inventory() -> tuple[dict[str, Any], dict[str, Any]]:
    pattern = os.environ.get("COMPANY_OS_FLEET_INVENTORY",
                             "/mnt/zer0models/workspace/zer0/data/operations/fleet/inventory-*.json")
    paths = sorted(glob.glob(pattern))
    if not paths:
        return {"devices": {}, "not_on_tailnet": []}, source("unavailable", reason="inventory_missing")
    try:
        data = _read_json(Path(paths[-1]))
        devices = {d.get("hostname"): d for d in data.get("devices", []) if isinstance(d, dict) and d.get("hostname")}
        return {"devices": devices, "not_on_tailnet": data.get("not_on_tailnet") or []}, \
            source("ok", os.stat(paths[-1]).st_mtime, coverage="dated owner inventory snapshot (static facts)")
    except Exception:
        return {"devices": {}, "not_on_tailnet": []}, source("degraded", reason="inventory_unreadable")


def tailscale() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    data, err = _json_cmd(["tailscale", "status", "--json"], 3.0)
    if err or not isinstance(data, dict):
        return [], source("unavailable", reason=err or "invalid")
    rows = []
    peers = [("self", data.get("Self") or {})] + [("peer", p) for p in (data.get("Peer") or {}).values()]
    for kind, p in peers[:MAX_ROWS]:
        if not isinstance(p, dict):
            continue
        ips = [ip for ip in p.get("TailscaleIPs") or [] if isinstance(ip, str) and ip.count(".") == 3]
        rows.append({"self": kind == "self", "hostname": p.get("HostName"), "os": p.get("OS"),
                     "ip": ips[0] if ips else None, "online": p.get("Online") is True,
                     "active": p.get("Active") is True, "relay": p.get("Relay") or None,
                     "direct": bool(p.get("CurAddr")), "last_seen": p.get("LastSeen"),
                     "rx": _num(p.get("RxBytes")), "tx": _num(p.get("TxBytes"))})
    return rows, source("ok", _now(), coverage="tailnet membership and reachability")


def kubeconfig() -> str | None:
    value = os.environ.get("COMPANY_OS_KUBECONFIG")
    if value:
        return value
    k3s = Path.home() / ".kube/k3s.yaml"
    return str(k3s) if k3s.is_file() else None


def k3s() -> tuple[dict[str, Any], dict[str, Any]]:
    cfg = kubeconfig()
    base = ["kubectl"] + (["--kubeconfig", cfg] if cfg else [])
    nodes_raw, nerr = _json_cmd(base + ["get", "nodes", "-o", "json", "--request-timeout=3s"], 4.0)
    pods_raw, perr = _json_cmd(base + ["get", "pods", "-A", "-o", "json", "--request-timeout=3s"], 4.0)
    if nerr:
        return {"nodes": [], "pods": [], "cluster": None}, source("unavailable", reason=f"kubectl:{nerr}")
    def ready(status: dict[str, Any]) -> bool | None:
        for c in status.get("conditions") or []:
            if isinstance(c, dict) and c.get("type") == "Ready":
                return c.get("status") == "True"
        return None
    nodes = []
    for item in (nodes_raw or {}).get("items", [])[:MAX_ROWS]:
        meta, st = item.get("metadata") or {}, item.get("status") or {}
        labels = meta.get("labels") or {}
        addrs = {a.get("type"): a.get("address") for a in st.get("addresses") or [] if isinstance(a, dict)}
        roles = sorted(k.split("/", 1)[1] for k in labels if k.startswith("node-role.kubernetes.io/"))
        cap = st.get("capacity") or {}
        nodes.append({"name": meta.get("name"), "ready": ready(st), "roles": roles or ["worker"],
                      "ip": addrs.get("InternalIP"), "version": (st.get("nodeInfo") or {}).get("kubeletVersion"),
                      "unschedulable": bool((item.get("spec") or {}).get("unschedulable")),
                      "gpu": cap.get("nvidia.com/gpu"),
                      "classes": sorted(k.split("class-", 1)[1] for k, v in labels.items() if "z0.dev/class-" in k and v == "true")})
    pods = []
    for item in (pods_raw or {}).get("items", [])[:256]:
        meta, st, spec = item.get("metadata") or {}, item.get("status") or {}, item.get("spec") or {}
        cs = st.get("containerStatuses") or []
        pods.append({"namespace": meta.get("namespace"), "name": meta.get("name"), "node": spec.get("nodeName"),
                     "phase": st.get("phase"), "ready": sum(1 for c in cs if c.get("ready")), "containers": len(cs),
                     "restarts": sum(_num(c.get("restartCount")) or 0 for c in cs)})
    cluster = "k3s" if cfg and cfg.endswith("k3s.yaml") else "current-context"
    status = "ok" if not perr and all(n["ready"] for n in nodes) else "degraded"
    return {"nodes": nodes, "pods": pods, "cluster": cluster}, \
        source(status, _now(), reason=None if status == "ok" else (f"pods:{perr}" if perr else "node_not_ready"),
               coverage=f"{cluster} nodes and pods (all namespaces)")


# ---------------------------------------------------------------- local processes

def _procs() -> list[dict[str, Any]]:
    """Process facts extracted by fixed rule. argv/env are parsed here and never returned."""
    rows = []
    for pid in os.listdir("/proc"):
        if not pid.isdigit():
            continue
        try:
            with open(f"/proc/{pid}/cmdline", "rb") as f:
                argv = [a.decode(errors="replace") for a in f.read(8192).split(b"\0") if a]
            with open(f"/proc/{pid}/stat", "rb") as f:
                stat = f.read().decode(errors="replace")
        except OSError:
            continue
        if not argv:
            continue
        rows.append({"pid": int(pid), "argv": argv, "start": stat})
    return rows


def _hermes_home_of(pid: int) -> str | None:
    try:
        with open(f"/proc/{pid}/environ", "rb") as f:
            for entry in f.read(262144).split(b"\0"):
                if entry.startswith(b"HERMES_HOME="):
                    return entry[12:].decode(errors="replace")
    except OSError:
        return None
    return None


def hermes_root() -> Path:
    return Path(os.environ.get("COMPANY_OS_HERMES_ROOT", str(Path.home() / ".hermes")))


def hermes_profiles() -> dict[str, Path]:
    root = hermes_root()
    out = {"default": root}
    for p in sorted((root / "profiles").glob("*"))[:MAX_ROWS]:
        if p.is_dir() and SAFE_TOKEN.fullmatch(p.name) and p.name not in out:
            out[p.name] = p
    return out


def _profile_for(home: str | None, profiles: dict[str, Path]) -> str | None:
    if not home:
        return None
    try:
        real = os.path.realpath(home)
    except OSError:
        return None
    for name, path in profiles.items():
        if os.path.realpath(path) == real:
            return name
    return "other"


HERMES_VERBS = ("gateway", "dashboard", "chat", "acp", "mcp", "kanban", "cron", "serve")


def local_processes(peers_by_ip: dict[str, str]) -> tuple[dict[str, Any], dict[str, Any]]:
    profiles = hermes_profiles()
    hermes: list[dict[str, Any]] = []
    harness: list[dict[str, Any]] = []
    tern = {"daemon": 0, "windows": 0, "remote_serve": 0, "remote_clients": []}
    agents: dict[str, int] = {}
    try:
        procs = _procs()
    except OSError:
        return {}, source("unavailable", reason="proc_unreadable")
    for p in procs:
        argv, pid = p["argv"], p["pid"]
        exe = os.path.basename(argv[0])
        joined = " ".join(argv[:16])
        if exe == "hermes" or "hermes_cli" in joined:
            verb = next((a for a in argv[1:12] if a in HERMES_VERBS), None)
            if verb is None and exe != "hermes":
                continue
            prof = _profile_for(_hermes_home_of(pid), profiles)
            hermes.append({"pid": pid, "profile": prof, "verb": verb or "chat"})
        elif exe == "tern" or argv[0].endswith("/tern"):
            rest = argv[1:3]
            if rest[:1] == ["daemon"]:
                tern["daemon"] += 1
            elif rest == ["remote", "serve"]:
                tern["remote_serve"] += 1
            elif rest == ["remote", "login"]:
                ip = argv[argv.index("--from") + 1] if "--from" in argv[:-1] else None
                tern["remote_clients"].append(peers_by_ip.get(ip or "", "unknown device"))
            elif rest[:1] in (["serve"], ["shot"], ["ctl"]):
                continue
            else:
                tern["windows"] += 1
        elif "z0live" in joined:
            what = "desktop host" if "hermes_host.py" in joined else "serve" if " serve" in joined else None
            if what:
                harness.append({"kind": "z0live", "name": f"z0live {what}", "pid": pid})
        elif "/products/dash/" in joined and ("expo" in joined or "bridge" in joined):
            harness.append({"kind": "dash", "name": "Dash " + ("bridge" if "bridge" in joined else "Expo dev server"), "pid": pid})
        elif exe == "llama-server":
            harness.append({"kind": "llm", "name": "llama-server (local model)", "pid": pid})
        elif "z0int.intelligence_service" in joined:
            harness.append({"kind": "z0", "name": "z0 cognition service", "pid": pid})
        elif "tencentdb-memory-gateway" in joined and exe == "docker":
            harness.append({"kind": "memory", "name": "TencentDB memory gateway", "pid": pid})
        else:
            for agent in ("omp", "codex", "claude", "opencode", "dsh", "pi"):
                if exe == agent:
                    agents[agent] = agents.get(agent, 0) + 1
    by_profile: dict[str, dict[str, Any]] = {}
    for h in hermes:
        prof = by_profile.setdefault(h["profile"] or "unknown", {"profile": h["profile"] or "unknown", "verbs": {}, "pids": []})
        prof["verbs"][h["verb"]] = prof["verbs"].get(h["verb"], 0) + 1
        prof["pids"].append(h["pid"])
    return {"hermes": sorted(by_profile.values(), key=lambda r: r["profile"]), "harness": harness,
            "tern": tern, "agents": agents, "profiles": sorted(profiles)}, \
        source("ok", _now(), coverage="process presence on this host; argv/env parsed by fixed rule, never exported")


# ---------------------------------------------------------------- capacity

def burn_pace() -> tuple[dict[str, Any] | None, dict[str, Any]]:
    data, err = _json_cmd(["burn-pace", "--json"], 6.0)
    if err or not isinstance(data, dict):
        return None, source("unavailable", reason=err or "invalid")
    lanes = {}
    for k, v in (data.get("lanes") or {}).items():
        if isinstance(v, dict):
            lanes[str(k)[:24]] = {f: v.get(f) for f in ("weekly_used_pct", "hours_to_reset", "pace_ratio", "band",
                                                        "max_workflow_agents", "effort", "offload")}
    z = data.get("z0_factory") or {}
    return {"posture": z.get("posture"), "action": z.get("action"), "prefer": z.get("prefer"),
            "avoid": z.get("avoid"), "lanes": lanes, "free_lane": bool(data.get("free_lane"))}, \
        source("ok", _now(), coverage="frontier subscription pace (weekly % used), not tokens")


def kerdoios() -> tuple[dict[str, Any] | None, dict[str, Any]]:
    path = Path(os.environ.get("COMPANY_OS_KERDOIOS_INVENTORY", str(Path.home() / ".cache/kerdoios/inventory.json")))
    try:
        data = _read_json(path)
    except FileNotFoundError:
        return None, source("unavailable", reason="not_observed")
    except Exception:
        return None, source("degraded", reason="unreadable")
    offers = data.get("offers") if isinstance(data, dict) else None
    if not isinstance(offers, list):
        return None, source("degraded", reason="unsupported_shape")
    providers: dict[str, dict[str, Any]] = {}
    for o in offers[:256]:
        if not isinstance(o, dict):
            continue
        p = providers.setdefault(str(o.get("provider"))[:32], {"offers": 0, "local": 0, "free": 0})
        p["offers"] += 1
        p["local"] += 1 if o.get("local") else 0
        econ = o.get("economics") or {}
        p["free"] += 1 if econ.get("input_token_price") == 0 and econ.get("output_token_price") == 0 else 0
    saved = data.get("saved_at")
    try:
        from datetime import datetime
        observed = datetime.fromisoformat(saved).timestamp() if isinstance(saved, str) else None
    except ValueError:
        observed = None
    src = source("ok", observed, coverage="Kerdoios offer inventory (claims, not measured quota)")
    if src["freshness"] != "fresh":
        src["status"] = "stale"
    return {"offers": len(offers), "providers": providers}, src


# ---------------------------------------------------------------- shadow network

SHADOW_LEDGERS = {
    # harness -> ledger written by that harness's z0 shadow slot (closed vocabulary, hashed ids)
    "omp": "state/omp/shadow_decisions.jsonl",
    "claude-code": "state/claude-code/shadow_decisions.jsonl",
    "dsh": "state/dsh/shadow_decisions.jsonl",
    "cognition": "shadow/cognition-shadow.jsonl",
    "jev": "shadow/jev-fly.jsonl",
    "preflight": "shadow/preflight.jsonl",
}
TAIL_BYTES = 262144


def _tail_jsonl(path: Path, limit: int = TAIL_BYTES) -> list[dict[str, Any]]:
    with open(path, "rb") as f:
        f.seek(0, os.SEEK_END)
        size = f.tell()
        f.seek(max(0, size - limit))
        raw = f.read(limit)
    lines = raw.split(b"\n")
    if size > limit:
        lines = lines[1:]  # first line is partial
    rows = []
    for line in lines:
        try:
            row = json.loads(line)
        except ValueError:
            continue
        if isinstance(row, dict):
            rows.append(row)
    return rows


def _ts(row: dict[str, Any]) -> float | None:
    v = _num(row.get("ts"))
    if v:
        return float(v)
    day = row.get("day")
    if isinstance(day, str):
        try:
            from datetime import datetime, timezone
            return datetime.strptime(day, "%Y-%m-%d").replace(tzinfo=timezone.utc).timestamp()
        except ValueError:
            return None
    return None


def shadow_network() -> tuple[dict[str, Any], dict[str, Any]]:
    """Per-lane shadow decisions from the last ~256 KB of each ledger.

    Shadow means the challenger observed and decided but did not act. Counts are
    over the tail window only; `window_rows` says how many rows that covered.
    """
    root = Path(os.environ.get("Z0INT_HOME", str(Path.home() / ".z0int")))
    lanes, newest = [], None
    for lane, rel in SHADOW_LEDGERS.items():
        path = root / rel
        try:
            mtime = path.stat().st_mtime
            rows = _tail_jsonl(path)
        except OSError:
            lanes.append({"lane": lane, "status": "unavailable", "reason": "not_observed"})
            continue
        stamps = [t for t in (_ts(r) for r in rows) if t]
        last = max(stamps) if stamps else mtime
        newest = max(newest or 0, last)
        day = [r for r in rows if (_ts(r) or 0) > last - 86400]
        challengers: dict[str, int] = {}
        outcome: dict[str, int] = {}
        tiers: dict[str, int] = {}
        for r in day:
            ch = r.get("challenger") if isinstance(r.get("challenger"), dict) else {}
            name = ch.get("model") or ch.get("id") or (r.get("fly") or {}).get("source") or r.get("route")
            if isinstance(name, str) and SAFE_TOKEN.fullmatch(name.lower()[:32]):
                challengers[name.lower()[:32]] = challengers.get(name.lower()[:32], 0) + 1
            d = r.get("decision") if isinstance(r.get("decision"), dict) else None
            key = ("abstained" if d.get("abstained") else "invalid" if d.get("invalid_call") else "decided") if d else \
                (r.get("status") if isinstance(r.get("status"), str) and SAFE_TOKEN.fullmatch(r["status"]) else None)
            if lane == "jev":
                key = "disagree" if r.get("disagree") else "agree" if "disagree" in r else "scored"
            if key:
                outcome[key] = outcome.get(key, 0) + 1
            esc = r.get("escalation") if isinstance(r.get("escalation"), dict) else None
            if esc and isinstance(esc.get("tier"), str) and SAFE_TOKEN.fullmatch(esc["tier"]):
                tiers[esc["tier"]] = tiers.get(esc["tier"], 0) + 1
            if lane == "preflight" and isinstance(r.get("route"), str) and SAFE_TOKEN.fullmatch(r["route"]):
                tiers[r["route"]] = tiers.get(r["route"], 0) + 1
        age = _now() - last
        lanes.append({"lane": lane, "status": "fresh" if age < 3600 else "stale", "last_at": last, "age_s": age,
                      "window_rows": len(rows), "last_24h_of_ledger": len(day),
                      "challengers": dict(sorted(challengers.items(), key=lambda kv: -kv[1])[:4]),
                      "outcomes": outcome, "tiers": tiers})
    live = [l for l in lanes if l.get("status") == "fresh"]
    status = "ok" if live else "stale" if newest else "unavailable"
    return {"lanes": lanes, "acting": None,
            "acting_reason": "no promotion ledger exported; every lane shown is shadow (observe-only)"}, \
        source(status, newest, coverage="tail of each shadow ledger; counts cover the newest 24 h present in the tail")


# ---------------------------------------------------------------- z0archy world model

Z0ARCHY_RAW = "https://raw.githubusercontent.com/kvnloo/z0archy/main/generated/graph.json"
WORLD_TYPES = ("component", "harness")


def z0archy_world() -> tuple[dict[str, Any] | None, dict[str, Any]]:
    """Declared structure: z0archy's compiled graph of kvnloo/z0, reduced to components + harnesses.

    Reads COMPANY_OS_Z0ARCHY_GRAPH (default ~/.cache/company-os/z0archy-graph.json).
    When the cache is missing or older than a day, refreshes it with one bounded
    public GET of z0archy's generated graph; a failed refresh keeps the old copy.
    """
    path = Path(os.environ.get("COMPANY_OS_Z0ARCHY_GRAPH", str(Path.home() / ".cache/company-os/z0archy-graph.json")))
    refresh = os.environ.get("COMPANY_OS_Z0ARCHY_REFRESH", "1") == "1"
    try:
        stale = _now() - path.stat().st_mtime > 86400
    except OSError:
        stale = True
    if stale and refresh:
        try:
            import urllib.request
            with urllib.request.urlopen(Z0ARCHY_RAW, timeout=5) as r:
                raw = r.read(4 * MAX_BYTES + 1)
            if len(raw) <= 4 * MAX_BYTES and json.loads(raw).get("schemaVersion"):
                path.parent.mkdir(parents=True, exist_ok=True)
                tmp = path.with_suffix(".tmp")
                tmp.write_bytes(raw)
                tmp.replace(path)
        except Exception:
            pass
    try:
        with open(path, "rb") as f:
            g = json.loads(f.read(4 * MAX_BYTES))
    except (OSError, ValueError):
        return None, source("unavailable", reason="graph_not_cached")
    nodes = {}
    for n in g.get("nodes") or []:
        if isinstance(n, dict) and n.get("type") in WORLD_TYPES:
            a = n.get("attributes") or {}
            nodes[n["id"]] = {"id": n["id"], "type": n["type"], "label": n.get("label"),
                              "kind": a.get("kind"), "status": a.get("status"), "repo": a.get("repo"),
                              "summary": (a.get("summary") or "").strip()[:240] or None}
    edges = []
    for e in g.get("edges") or []:
        if isinstance(e, dict) and e.get("source") in nodes and e.get("target") in nodes:
            edges.append({"type": e.get("type"), "source": e["source"], "target": e["target"]})
    snap = g.get("snapshot") or {}
    generated = snap.get("generatedAt")
    try:
        from datetime import datetime
        observed = datetime.fromisoformat(generated.replace("Z", "+00:00")).timestamp() if isinstance(generated, str) else None
    except ValueError:
        observed = None
    src = source("ok", observed, coverage="declared truth (kvnloo/z0 via z0archy); components and harnesses only",
                 truth_class=snap.get("truthClass"), schema_version=g.get("schemaVersion"))
    src["freshness"] = "declared"
    return {"nodes": list(nodes.values()), "edges": edges[:256], "generated_at": generated,
            "source": snap.get("source")}, src


# ---------------------------------------------------------------- join

def _health_status(h: dict[str, Any] | None) -> str:
    if not h:
        return "unknown"
    if h.get("paused"):
        return "paused"
    return "ok" if h.get("healthy") else "degraded"


def build(local: bool = True, z0_service: dict[str, Any] | None = None) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=6) as pool:
        slow = {name: pool.submit(fn) for name, fn in (("ts", tailscale), ("kube", k3s), ("pace", burn_pace))}
        reg, reg_src = fleet_registry()
        health, health_src = fleet_health()
        inv, inv_src = fleet_inventory()
        kerd, kerd_src = kerdoios()
        shadow, shadow_src = shadow_network()
        ts, ts_src = slow["ts"].result()
        kube, kube_src = slow["kube"].result()
        pace, pace_src = slow["pace"].result()
    peers_by_ip = {r["ip"]: r["hostname"] for r in ts if r.get("ip")}
    procs, proc_src = local_processes(peers_by_ip)

    self_row = next((r for r in ts if r["self"]), None)
    self_name = os.uname().nodename
    names: list[str] = []
    for n in list(reg["nodes"]) + list(health) + [k["name"] for k in kube["nodes"]]:
        if n and n not in names:
            names.append(n)
    ip_of = {n: (reg["nodes"].get(n) or {}).get("tailnet_ip") for n in names}
    claimed_ips: set[str] = set()
    hosts = []
    for n in names:
        r = reg["nodes"].get(n) or {}
        h = health.get(n)
        probe = (h or {}).get("probe") or {}
        node = next((k for k in kube["nodes"] if k["name"] == n or (ip_of[n] and k["ip"] == ip_of[n])), None)
        ip = ip_of[n] or (node or {}).get("ip")
        tsr = next((t for t in ts if ip and t["ip"] == ip), None) or next((t for t in ts if t["hostname"] == n), None)
        android = next((t for t in ts if r.get("android_ip") and t["ip"] == r["android_ip"]), None)
        for t in (tsr, android):
            if t and t["ip"]:
                claimed_ips.add(t["ip"])
        inv_row = inv["devices"].get(n) or {}
        is_self = n == self_name or bool(self_row and tsr and tsr["self"])
        pods = [p for p in kube["pods"] if node and p["node"] == node["name"]]
        power = probe.get("power") or {}
        batt = (power.get("batteries") or [{}])[0] if power.get("batteries") else {}
        disk = probe.get("disk_root") or {}
        host = {
            "name": n, "self": is_self,
            "kind": "phone" if r.get("kind") == "phone" else "server" if r.get("role") == "server" else "worker" if r.get("role") else "node",
            "role": r.get("role"), "registry_role": inv_row.get("role"), "model": r.get("model"),
            "arch": r.get("arch"), "classes": r.get("classes") or [], "taints": r.get("taints") or [],
            "aliases": r.get("aliases") or [], "hardware": {"cpu": inv_row.get("cpu"), "gpu": inv_row.get("gpu"),
                                                            "ram_gb": inv_row.get("ram_gb"), "os": inv_row.get("os")},
            "online": tsr["online"] if tsr else None,
            "tailnet": {"ip": ip, "hostname": (tsr or {}).get("hostname"), "online": (tsr or {}).get("online"),
                        "path": "self" if tsr and tsr["self"] else "direct" if tsr and tsr["direct"] else (f"relay {tsr['relay']}" if tsr and tsr["relay"] else None),
                        "last_seen": (tsr or {}).get("last_seen"),
                        "android": {"hostname": android["hostname"], "online": android["online"]} if android else None},
            "health": {"status": _health_status(h), "reasons": (h or {}).get("reasons") or [],
                       "warnings": (h or {}).get("warnings") or [], "strikes": (h or {}).get("strikes"),
                       "action": (h or {}).get("action"), "observed_at": _num((h or {}).get("ts"))},
            "resources": {"ncpu": probe.get("ncpu"), "load1": probe.get("load1"), "mem_total_mb": probe.get("mem_total_mb"),
                          "mem_available_mb": probe.get("mem_available_mb"), "disk_free_gb": disk.get("free_gb"),
                          "disk_total_gb": disk.get("total_gb"), "max_temp_c": probe.get("max_temp_c"),
                          "battery_pct": batt.get("pct"), "on_ac": power.get("on_ac")},
            "services": probe.get("services") or {},
            "supervisor_session": probe.get("supervisor_session"),
            "tern_doctor": probe.get("tern_doctor") or (h or {}).get("tern_doctor"),
            "k3s": ({"node": node["name"], "ready": node["ready"], "roles": node["roles"], "version": node["version"],
                     "unschedulable": node["unschedulable"], "gpu": node["gpu"], "classes": node["classes"],
                     "pods": [{"namespace": p["namespace"], "name": p["name"], "phase": p["phase"],
                               "ready": f"{p['ready']}/{p['containers']}", "restarts": p["restarts"]} for p in pods[:24]],
                     "pods_total": len(pods)} if node else None),
            "harnesses": [], "roles": [],
        }
        # What actually runs under the host. Only this host's processes are observable here.
        if is_self:
            for prof in procs.get("hermes", []):
                verbs = ", ".join(f"{v}×{c}" if c > 1 else v for v, c in sorted(prof["verbs"].items()))
                host["harnesses"].append({"kind": "hermes", "name": f"Hermes · {prof['profile']}", "detail": verbs,
                                          "status": "running", "profile": prof["profile"]})
            grouped: dict[str, dict[str, Any]] = {}
            for item in procs.get("harness", []):
                g = grouped.setdefault(item["name"], {"kind": item["kind"], "name": item["name"], "status": "running", "count": 0})
                g["count"] += 1
            for g in grouped.values():
                g["detail"] = f"{g['count']} processes" if g["count"] > 1 else None
                host["harnesses"].append(g)
            t = procs.get("tern") or {}
            if t.get("daemon") or t.get("windows") or t.get("remote_serve"):
                clients = sorted(set(t.get("remote_clients") or []))
                host["harnesses"].append({"kind": "tern", "name": "Tern", "status": "running",
                                          "detail": f"daemon {t.get('daemon', 0)} · windows {t.get('windows', 0)} · remote serve {t.get('remote_serve', 0)}"
                                                    + (f" · attached: {', '.join(clients)}" if clients else "")})
            for agent, count in sorted((procs.get("agents") or {}).items()):
                host["harnesses"].append({"kind": "agent", "name": agent, "status": "running", "detail": f"{count} process" + ("es" if count > 1 else "")})
            if z0_service and isinstance(z0_service.get("health"), dict):
                for hz in host["harnesses"]:
                    if hz["kind"] == "z0":
                        hz["detail"] = "healthz ok" if z0_service["health"].get("ok") else "healthz failing"
        else:
            svc = host["services"]
            if svc.get("tern-remote"):
                host["harnesses"].append({"kind": "tern", "name": "Tern remote serve", "status": svc["tern-remote"],
                                          "detail": f"tern doctor {host['tern_doctor']}" if host["tern_doctor"] else None})
            if svc.get("fleet-supervise"):
                host["harnesses"].append({"kind": "fleet", "name": "fleet supervisor", "status": svc["fleet-supervise"],
                                          "detail": f"session {host['supervisor_session']}" if host["supervisor_session"] else None})
            if svc.get("k3s") or svc.get("k3s-agent"):
                host["harnesses"].append({"kind": "k3s", "name": "k3s agent", "status": svc.get("k3s") or svc.get("k3s-agent"), "detail": None})
        # Canonical roles this host wears, from live evidence only.
        if r.get("role") in ("server", "worker") or node:
            host["roles"].append("second_mate")
        if is_self and any(hz.get("verb") == "gateway" or "gateway" in (hz.get("detail") or "") for hz in host["harnesses"]):
            host["roles"].append("first_mate")
        if is_self and any(hz["kind"] == "z0live" for hz in host["harnesses"]):
            host["roles"].append("voice_intake")
        if any(p["namespace"] == "z0" for p in pods):
            host["roles"].append("oss_lane")
        hosts.append(host)

    others = []
    for t in ts:
        if t["ip"] in claimed_ips or t["self"]:
            continue
        others.append({"name": t["hostname"], "os": t["os"], "online": t["online"], "last_seen": t["last_seen"],
                       "path": "direct" if t["direct"] else (f"relay {t['relay']}" if t["relay"] else None)})
    candidates = [{"name": k, "note": v} for k, v in reg["candidates"].items()]
    data = {"hosts": hosts, "other_devices": others[:MAX_ROWS], "candidates": candidates[:16],
            "cluster": {"kind": kube["cluster"], "nodes": len(kube["nodes"]),
                        "ready": sum(1 for n in kube["nodes"] if n["ready"]), "pods": len(kube["pods"]),
                        "unplaced_pods": [{"namespace": p["namespace"], "name": p["name"], "phase": p["phase"]}
                                          for p in kube["pods"] if not p["node"]][:8]},
            "shadow_network": shadow,
            "frontier": pace, "kerdoios": kerd, "view": "local" if local else "public"}
    sources = {"fleet_registry": reg_src, "fleet_health": health_src, "fleet_inventory": inv_src,
               "tailscale": ts_src, "k3s": kube_src, "local_processes": proc_src, "shadow_network": shadow_src,
               "burn_pace": pace_src, "kerdoios": kerd_src}
    return (data if local else redact(data)), sources


def redact(data: dict[str, Any]) -> dict[str, Any]:
    """Public export: opaque aliases for names, no addresses, titles or pod names."""
    out = json.loads(json.dumps(data))
    for h in out["hosts"]:
        h["name"] = alias(h["name"])
        h["model"] = None
        h["aliases"] = []
        h["tailnet"].update(ip=None, hostname=alias(h["tailnet"].get("hostname")), last_seen=None)
        if h["tailnet"].get("android"):
            h["tailnet"]["android"]["hostname"] = alias(h["tailnet"]["android"]["hostname"])
        for hz in h["harnesses"]:
            hz["detail"] = None
            hz.pop("pid", None)
            if hz.get("profile"):
                hz["name"] = "Hermes · " + str(alias(hz["profile"]))
                hz["profile"] = alias(hz["profile"])
        if h["k3s"]:
            h["k3s"]["node"] = alias(h["k3s"]["node"])
            for p in h["k3s"]["pods"]:
                p["name"], p["namespace"] = alias(p["name"]), alias(p["namespace"])
    out["other_devices"] = [{"name": alias(d["name"]), "online": d["online"]} for d in out["other_devices"]]
    out["candidates"] = [{"name": alias(c["name"]), "note": None} for c in out["candidates"]]
    out["cluster"]["unplaced_pods"] = [{"namespace": alias(p["namespace"]), "name": alias(p["name"]), "phase": p["phase"]}
                                       for p in out["cluster"]["unplaced_pods"]]
    return out
