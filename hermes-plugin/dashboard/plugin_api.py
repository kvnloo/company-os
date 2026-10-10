"""Company OS local projection backend.

Mounted by Hermes at /api/plugins/company-os/. Read-only: existing z0 GET
contracts, optional capacity, process/Kubernetes and host metadata. Missing
control/episode, economics and memory contracts remain explicit gaps.
"""
from __future__ import annotations

import hashlib
import http.client
import ipaddress
import re
from urllib.parse import urlsplit
import json
import math
import stat
import itertools
from datetime import datetime
import os
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any

from fastapi import APIRouter

router = APIRouter()

SCHEMA = "company_os.snapshot.v1"
CAPACITY_SCHEMA = "z0.capacity.snapshot.v1"

KNOWN_AGENTS = ("hermes", "omp", "dsh", "omo", "codex", "claude", "opencode", "pi")


def _now() -> float:
    return time.time()


MAX_BYTES = 524288
MAX_ROWS = 64
PROVIDERS = ("groq", "cerebras", "openai", "anthropic", "google", "gemini", "nous", "grok", "xai", "openrouter", "local")
STATUSES = ("ok", "unknown", "unavailable", "degraded", "online", "offline", "ready", "blocked", "running", "waiting", "completed", "failed", "stale")


def _number(v):
    return v if type(v) in (int, float) and math.isfinite(v) and 0 <= v <= 2**53 else None


def _stamp(v):
    if isinstance(v, str) and len(v) <= 40:
        try:
            d = datetime.fromisoformat(v.replace("Z", "+00:00"))
            v = d.timestamp() if d.tzinfo else None
        except ValueError:
            return None
    n = _number(v)
    return n if n is not None and 0 < n < 1e11 else None


def _enum(*allowed):
    return lambda v: v if isinstance(v, str) and v in allowed else None


def _alias(v):
    # IDs and labels are not trusted public text. Stable opaque aliases retain
    # joins without exporting labels, paths, prompts, or secret-like values.
    if not (isinstance(v, str) and 0 < len(v) <= 256 or type(v) is int and 0 <= v <= 2**53):
        return None
    return "ref-" + hashlib.sha256(str(v).encode()).hexdigest()[:16]


def _project(value, schema, depth=0) -> Any:
    """Closed recursive shape; no unknown keys or arbitrary string values."""
    if depth > 8:
        return None
    if isinstance(schema, dict):
        src = value if isinstance(value, dict) else {}
        return {k: _project(src.get(k), rule, depth + 1) for k, rule in schema.items()}
    if isinstance(schema, list):
        return [_project(v, schema[0], depth + 1) for v in value[:MAX_ROWS]] if isinstance(value, list) else []
    return schema(value)


def _freshness(observed):
    if observed is None:
        return "unknown"
    age = _now() - observed
    return "invalid" if age < -5 else "stale" if age > 30 else "fresh"


def _source(status: str, **extra: Any) -> dict[str, Any]:
    observed = _stamp(extra.pop("observed_at", None))
    return {"status": status, "checked_at": _now(), "observed_at": observed,
            "age_s": max(0, _now() - observed) if observed is not None and observed <= _now() + 5 else None,
            "freshness": _freshness(observed), "source_version": None,
            "producer_revision": None, **extra}


def _read_bounded(path):
    fd = os.open(path, os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW)
    with os.fdopen(fd, "rb") as f:
        info = os.fstat(f.fileno())
        if not stat.S_ISREG(info.st_mode) or info.st_size > MAX_BYTES:
            raise ValueError("invalid_source_file")
        raw = f.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise ValueError("source_too_large")
    return raw


def _run_json(argv: list[str], timeout: float = 2.0) -> tuple[Any, str | None]:
    try:
        proc = subprocess.run(argv, capture_output=True, text=True, timeout=timeout, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return None, type(exc).__name__
    if proc.returncode != 0:
        return None, f"exit:{proc.returncode}"
    try:
        if len(proc.stdout) > MAX_BYTES:
            return None, "oversize"
        return json.loads(proc.stdout), None
    except (ValueError, UnicodeError, RecursionError):
        return None, "invalid_json"


def _k8s() -> tuple[dict[str, Any], dict[str, Any]]:
    if not shutil.which("kubectl"):
        return {"available": False, "ready": None, "pods": [], "nodes": []}, _source("unavailable", reason="kubectl_missing")
    pods_raw, pods_err = _run_json(["kubectl", "get", "pods", "-A", "-o", "json", "--request-timeout=2s"])
    nodes_raw, nodes_err = _run_json(["kubectl", "get", "nodes", "-o", "json", "--request-timeout=2s"])
    def items(raw):
        return raw.get("items", []) if isinstance(raw, dict) and isinstance(raw.get("items"), list) else []
    def ready(status):
        conditions = status.get("conditions", [])
        if not isinstance(conditions, list):
            return None
        v = next((c.get("status") for c in conditions[:MAX_ROWS] if isinstance(c, dict) and c.get("type") == "Ready"), None)
        return True if v == "True" else False if v == "False" else None
    pods, nodes = [], []
    for item in items(pods_raw)[:MAX_ROWS]:
        if not isinstance(item, dict):
            continue
        meta, status = item.get("metadata") or {}, item.get("status") or {}
        cs = status.get("containerStatuses") or []
        counts = [_number(c.get("restartCount")) if isinstance(c, dict) else None for c in cs[:MAX_ROWS]]
        restarts = sum(v for v in counts if v is not None) if counts and all(v is not None for v in counts) and len(cs) <= MAX_ROWS else None
        pods.append({"name": _alias(meta.get("name")), "namespace": _alias(meta.get("namespace")),
                     "phase": _enum("Running", "Pending", "Succeeded", "Failed", "Unknown")(status.get("phase")),
                     "workload_ready": ready(status), "ready": sum(c.get("ready") is True for c in cs[:MAX_ROWS] if isinstance(c, dict)),
                     "containers": len(cs), "restarts": restarts})
    for item in items(nodes_raw)[:MAX_ROWS]:
        if not isinstance(item, dict):
            continue
        nodes.append({"name": _alias((item.get("metadata") or {}).get("name")), "ready": ready(item.get("status") or {})})
    health = bool(nodes) and all(n["ready"] is True for n in nodes) and all(p["phase"] == "Succeeded" or p["workload_ready"] is True for p in pods)
    truncated = len(items(pods_raw)) > MAX_ROWS or len(items(nodes_raw)) > MAX_ROWS
    ok = not pods_err and not nodes_err and health and not truncated
    data = {"available": not pods_err and not nodes_err, "ready": health if not pods_err and not nodes_err and not truncated else None,
            "pods": pods, "nodes": nodes, "coverage": {"scope": "current_kube_context", "limit_per_kind": MAX_ROWS, "truncated": truncated}}
    return data, _source("ok" if ok else "degraded", observed_at=_now(),
                         reason=None if ok else "workloads_unready_or_inventory_incomplete", coverage=data["coverage"],
                         source_version="sha256:" + hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest())


def _process_fleet() -> list[dict[str, Any]]:
    try:
        proc = subprocess.run(
            ["ps", "-eo", "pid=,comm=,etimes="],
            capture_output=True, text=True, timeout=1.0, check=False
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise RuntimeError("process_source_unavailable") from exc
    if proc.returncode != 0 or len(proc.stdout) > MAX_BYTES:
        raise RuntimeError("process_source_unavailable")
    rows: list[dict[str, Any]] = []
    # comm may contain spaces (Linux PR_SET_NAME). Parse the numeric edges;
    # never inspect argv, which can contain prompts and credentials.
    aliases = {name: name for name in KNOWN_AGENTS}
    aliases["omp daemon brok"] = "omp"
    for raw in proc.stdout.splitlines():
        parts = raw.strip().split(maxsplit=1)
        if len(parts) != 2:
            continue
        edge = parts[1].rsplit(maxsplit=1)
        if len(edge) != 2:
            continue
        pid, (comm, age) = parts[0], edge
        name = aliases.get(comm.lower())
        if not name or len(pid) > 10 or len(age) > 12 or not pid.isdecimal() or not age.isdecimal() or int(pid) <= 0:
            continue
        rows.append({"pid": int(pid), "name": name, "harness": name,
                     "age_s": int(age), "status": "observed", "governed": None,
                     "host_id": "local", "session_id": None, "trace_id": None,
                     "capability": None, "heartbeat_at": None,
                     "observed_at": _now(), "coverage": "process_presence_only"})
    return rows[:100]


def _safe_capacity_quota(value: Any) -> dict[str, Any]:
    dimension = {"remaining": _number, "limit": _number, "reset_at": _stamp}
    schema = {k: _number for k in ("remaining_free_quota", "remaining_tokens", "remaining", "day_tokens_remaining", "limit", "daily_limit", "day_tokens_limit")}
    schema.update(reset_at=_stamp, dimensions={k: dimension for k in ("tokens", "requests", "rpm", "tpm", "rpd", "tpd")})
    out = _project(value, schema)
    for row in (out, *out["dimensions"].values()):
        if row.get("reset_at") is not None and row["reset_at"] <= _now():
            for key in row:
                if "remaining" in key:
                    row[key] = None
    return out


def _safe_capacity_resources(value: Any) -> dict[str, Any]:
    schema = {k: _number for k in ("cpu_logical", "ram_total_bytes", "ram_available_bytes", "storage_total_bytes", "storage_free_bytes", "gpu_count")}
    schema["gpus"] = [{"id": _alias, "name": _alias, "memory_total_bytes": _number,
                       "memory_free_bytes": _number, "utilization_pct": _number}]
    return _project(value, schema)


def _sanitize_capacity_snapshot(data: Any) -> dict[str, Any] | None:
    if not isinstance(data, dict) or data.get("schema") != CAPACITY_SCHEMA:
        return None
    common = {"status": _enum(*STATUSES), "observed_at": _stamp}
    boolean = lambda v: v if type(v) is bool else None
    schema = {
        "generated_at": _stamp, "observed_at": _stamp,
        "sources": {k: common for k in ("tern", "kerdoios", "k8s")},
        "hosts": [{**common, "host_id": _alias, "label": _alias,
                   "mode": _enum("local", "ssh", "kubernetes", "remote"),
                   "rtt_ms": _number, "resources": _safe_capacity_resources}],
        "sessions": [{**common, "session_id": _alias, "host_id": _alias,
                      "name": _alias, "runtime": _enum(*KNOWN_AGENTS),
                      "current": boolean, "locked": boolean, "tab_count": _number,
                      "rtt_ms": _number}],
        "offers": [{**common, "offer_id": _alias, "origin": _enum("provider", "host"),
                    "provider": _enum(*PROVIDERS), "model": _alias, "actor_id": _alias,
                    "host_id": _alias, "health": _enum(*STATUSES),
                    "resources": _safe_capacity_resources, "quota": _safe_capacity_quota,
                    "price": _number, "predicted_cost": _number, "burn_rate": _number,
                    "time_to_exhaustion": _number, "time_to_reset": _number, "reset_at": _stamp}],
        "leases": [{**common, "placement_id": _alias, "demand_id": _alias,
                    "offer_id": _alias, "selected_offer_id": _alias,
                    "lease_expires_at": _stamp, "policy_revision": _alias}],
    }
    out = _project(data, schema)
    out["schema"] = CAPACITY_SCHEMA
    for row in out["sessions"]:
        row.update(session_sticky=True, migration_allowed=False)
    for name in ("hosts", "sessions", "offers", "leases"):
        for row in out[name]:
            row["freshness"] = _freshness(row.get("observed_at"))
            if row["freshness"] != "fresh":
                row["status"] = "stale" if row["freshness"] == "stale" else "unknown"
                if "health" in row:
                    row["health"] = "unknown"
                if "quota" in row:
                    q = row["quota"]
                    for dim in (q, *q["dimensions"].values()):
                        for key in dim:
                            if "remaining" in key:
                                dim[key] = None
    out["summary"] = {k: len(out[k]) for k in ("hosts", "sessions", "offers", "leases")}
    out["coverage"] = {"limit_per_kind": MAX_ROWS, "scope": "optional_unqualified_capacity",
                       "truncated": any(isinstance(data.get(k), list) and len(data[k]) > MAX_ROWS for k in out["summary"])}
    return out


def _z0_capacity() -> tuple[dict[str, Any] | None, dict[str, Any]]:
    root = Path(os.environ.get("Z0INT_HOME", "~/.z0int")).expanduser()
    path = Path(os.environ.get("COMPANY_OS_Z0_CAPACITY_SNAPSHOT", str(root / "state/capacity_snapshot.json"))).expanduser()
    try:
        raw = _read_bounded(path)
        data = _sanitize_capacity_snapshot(json.loads(raw))
        if data is None:
            raise ValueError("unsupported_schema")
    except FileNotFoundError:
        return None, _source("unavailable", reason="not_observed", optional=True)
    except (OSError, ValueError, UnicodeError, RecursionError):
        return None, _source("degraded", reason="invalid_capacity_source", optional=True)
    return data, _source("degraded", observed_at=data["observed_at"], optional=True,
                         schema=CAPACITY_SCHEMA, source_version="sha256:" + hashlib.sha256(raw).hexdigest(),
                         reason="producer_qualification_unknown", coverage=data["coverage"])


def _economics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    # Raw decisions/outcome revisions are not a Tokenomics read contract.
    # Unknown is not measured zero. Do not invent accounting or join semantics.
    return {**dict.fromkeys(("input_tokens", "output_tokens", "cached_input_tokens",
                            "actual_tokens", "observed_cost_usd", "verified_events",
                            "measurement_complete_events", "governed_events")),
            "status": "unknown", "reason": "tokenomics_read_contract_missing"}


def _fleet(control: dict[str, Any] | None, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    # No qualified control/episode read contract has been established. Historical
    # receipts (including nested outcomes and ts) must stay with the source owner.
    return _process_fleet()


READ_ROUTES = {
    "health": "/healthz", "readiness": "/readyz", "providers": "/v1/providers",
    "metrics": "/metrics", "outcome_coverage": "/v1/observe/outcome/coverage",
    "bridge_capabilities": "/v1/bridge/capabilities",
    "randomized_evidence": "/v1/observe/outcome/randomized-evidence",
}
SOURCE_NAMES = {"health": "z0_health", "readiness": "z0_readiness", "providers": "z0_providers", "metrics": "z0_metrics", "outcome_coverage": "z0_outcomes"}
SOURCE_NAMES["bridge_capabilities"] = "z0_bridge"
SOURCE_NAMES["randomized_evidence"] = "z0_evaluation"
SOURCE_SCOPES = {
    "health": "service_process_only", "readiness": "dispatch_readiness_only",
    "providers": "service_provider_admission_not_quota", "metrics": "service_process_counters_not_economics",
    "outcome_coverage": "agentweb_registered_expectations_only",
    "bridge_capabilities": "advertised_protocol_not_consumer_use",
    "randomized_evidence": "agentweb_registered_experiments_only",
}
WINDOWS = ("1h", "24h", "7d")
COVERAGE_REASONS = ("not_required", "insufficient_mature_sample", "joined_coverage_below_threshold",
                    "complete_coverage_below_threshold", "early_or_invalid_observation_present")
REVIEW_REASONS = ("outcome_coverage_gate_closed", "invalid_or_noncausal_assignment_present",
                  "varying_assignment_probability_not_supported", "unit_assigned_to_multiple_arms",
                  "candidate_treatment_not_stable", "reference_treatment_not_stable", "minimum_live_sample_not_met",
                  "candidate_minimum_sample_not_met", "reference_minimum_sample_not_met")


def _ratio(value):
    n = _number(value)
    return n if n is not None and n <= 1 else None


def _safe_outcome_coverage(data):
    if data.get("schema") != "z0int.agentweb_outcome_coverage.v1":
        raise ValueError("unsupported_coverage_schema")
    boolean = lambda v: v if type(v) is bool else None
    window = {**{k: _number for k in ("registered", "eligible", "observed", "complete", "partial", "missing", "early_or_invalid")},
              "coverage": _ratio, "complete_coverage": _ratio, "passes": boolean,
              "reasons": [_enum(*COVERAGE_REASONS)]}
    return {"schema": "z0int.agentweb_outcome_coverage.v1", **_project(data, {
        "as_of": _stamp, "expectations": _number, "observations": _number, "orphan_observations": _number,
        "required_windows": [_enum(*WINDOWS)], "by_window": {w: window for w in WINDOWS},
        "policy": {"min_eligible_per_window": _number, "min_coverage": _ratio, "min_complete_coverage": _ratio},
        "promotion_gate": {"eligible": boolean, "causal_quality_proven": boolean, "necessary_not_sufficient": boolean,
                           "reasons": [_enum("no_required_expectations", *(f"{w}:{r}" for w in WINDOWS for r in COVERAGE_REASONS))]}})}


def _get_readonly(origin, path):
    if path not in (*READ_ROUTES.values(), "/api/v1/cluster/status"):
        raise ValueError("route_not_allowed")
    conn = http.client.HTTPConnection(origin.hostname, origin.port or 80, timeout=2)
    try:
        # No proxy, auth, cookies, redirects, retries, POST, or inference routes.
        conn.request("GET", path, headers={"Accept": "application/json, text/plain"})
        response = conn.getresponse()
        raw = response.read(MAX_BYTES + 1)
        if len(raw) > MAX_BYTES:
            raise ValueError("response_too_large")
        return raw, response.status
    finally:
        conn.close()


def _safe_metrics(text, limit: int | None = MAX_ROWS):
    # Only owner-defined metric names and typed labels, never arbitrary labels.
    names = {"z0intelligence_" + n for n in (
        "dispatch_active", "dispatch_peak", "dispatch_new_total", "dispatch_replayed_total",
        "dispatch_ok_total", "dispatch_failed_total", "dispatch_seconds_sum", "dispatch_finished_total",
        "admitted_connections_total", "rejected_connections_total",
        "provider_inflight", "provider_cap", "provider_capped_total", "provider_ratelimited_total",
        "provider_unhealthy", "provider_error_total", "provider_latency_seconds_count", "provider_latency_seconds_sum")}
    rows = []
    for line in text.splitlines():
        match = re.fullmatch(r'([a-z0-9_]+)(?:\{provider="([a-z]+)"(?:,status="([0-9]{1,3})")?\})? ([0-9.eE+\-]+)', line)
        if not match:
            continue
        name, provider, status, value = match.groups()
        if name not in names or provider is not None and provider not in PROVIDERS:
            continue
        try:
            value = _number(float(value))
        except ValueError:
            continue
        rows.append({"metric": name, "provider": provider, "http_status": int(status) if status else None, "value": value})
    return rows[:limit]


def _safe_live(kind, raw):
    if kind == "metrics":
        return _safe_metrics(raw.decode("utf-8"))
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise ValueError("invalid_response")
    boolean = lambda v: v if type(v) is bool else None
    if kind == "randomized_evidence":
        if data.get("schema") != "z0int.agentweb_randomized_outcome_evidence.v1" or not isinstance(data.get("experiments"), dict):
            raise ValueError("unsupported_evaluation_schema")
        out = _project(data, {"as_of": _stamp, "review_ready_any": boolean, "human_review_required": boolean,
                             "auto_promotion_allowed": boolean, "causal_quality_proven": boolean,
                             "policy": {"min_total_live_units": _number, "min_complete_units_per_arm": _number}})
        out["schema"] = "z0int.agentweb_randomized_outcome_evidence.v1"
        out["experiments"] = [
            {"experiment_ref": _alias(key), **_project(row, {
                "registered_assignments": _number, "valid_randomized_assignments": _number,
                "assignment_probability": _ratio, "arms": {a: {"units": _number} for a in ("candidate", "reference")},
                "review_ready": boolean, "human_review_required": boolean, "auto_promotion_allowed": boolean,
                "causal_quality_proven": boolean, "reasons": [_enum(*REVIEW_REASONS)]})}
            for key, row in itertools.islice(data["experiments"].items(), MAX_ROWS)]
        out["coverage"] = {"scope": SOURCE_SCOPES[kind], "limit_per_kind": MAX_ROWS,
                           "returned": len(out["experiments"]), "total": len(data["experiments"]),
                           "truncated": len(data["experiments"]) > MAX_ROWS,
                           "omitted": "metric_effects_treatment_hashes_and_free_text"}
        return out
    if kind == "bridge_capabilities":
        if data.get("schema") != "agentweb.z0.bridge.capabilities.v1":
            raise ValueError("unsupported_bridge_schema")
        out = {"schema": "agentweb.z0.bridge.capabilities.v1", "execution_permission": False,
                **_project(data, {
                    "bridge_protocol_versions": [_enum("agentweb.z0.bridge.v1")],
                    "active_dispatch_supported": boolean,
                    "transport": {**{k: _number for k in ("max_request_bytes", "max_active", "socket_backlog", "overload_status", "retry_after_seconds")},
                                  "queue_policy": _enum("reject_excess"), "overload_execution": _enum("not_started")},
                    "endpoints": [{"path": _enum("/v1/plan", "/v1/intelligence", "/v1/experimental/choice", "/v1/experimental/noul"),
                                   "kind": _enum("plan", "dispatch", "decide"), "modes": [_enum("shadow", "active")],
                                   "physical_execution": boolean, "experimental": boolean}],
                })}
        total = len(data["endpoints"]) if isinstance(data.get("endpoints"), list) else None
        out["coverage"] = {"scope": SOURCE_SCOPES[kind], "limit_per_kind": MAX_ROWS,
                           "returned": len(out["endpoints"]), "total": total,
                           "truncated": total > MAX_ROWS if total is not None else None,
                           "omitted": "unknown_enums_and_unallowlisted_fields"}
        return out
    if kind == "health":
        if type(data.get("ok")) is not bool:
            raise ValueError("invalid_health")
        return _project(data, {"ok": boolean})
    if kind == "readiness":
        if type(data.get("ok")) is not bool:
            raise ValueError("invalid_readiness")
        return {**_project(data, {"ok": boolean, "authority_protocol_version": _number,
                                 "aodl_admission_ready": boolean, "governed_remote_enabled": boolean,
                                 "governed_remote_ready": boolean, "max_active": _number}),
                "scope": "dispatch_readiness_not_model_or_deployment_acceptance"}
    if kind == "providers":
        providers = data.get("providers")
        if not isinstance(providers, dict):
            raise ValueError("invalid_providers")
        return [{"provider": p, **_project(providers[p], {
            "cap": _number, "inflight": _number, "available": boolean, "unhealthy": boolean,
            "cooldown_until": _number, "last_http_status": _number,
            "reason": _enum("healthy", "eligible_unprobed", "unmeasured_cap", "cap_zero", "account_blocked", "funds_exhausted", "cooldown", "inflight_cap")}),
            "quota": {}, "model": None} for p in PROVIDERS if p in providers]
    return _safe_outcome_coverage(data)


def _z0_live():
    try:
        origin = urlsplit(os.environ.get("COMPANY_OS_Z0_URL", "http://127.0.0.1:11501"))
        if origin.scheme != "http" or origin.hostname != "127.0.0.1" or origin.username or origin.password or origin.path or origin.query or origin.fragment:
            raise ValueError("invalid_loopback_origin")
        _ = origin.port
    except ValueError:
        return {}, {"z0_service": _source("unavailable", reason="invalid_loopback_origin")}
    data, sources = {}, {}
    for kind, path in READ_ROUTES.items():
        name = SOURCE_NAMES[kind]
        try:
            raw, status = _get_readonly(origin, path)
            if status != 200 and not (status == 503 and kind in ("health", "readiness")):
                raise ValueError("unexpected_http_status")
            value = _safe_live(kind, raw)
            data[kind] = value
            ok = status == 200 and (not isinstance(value, dict) or value.get("ok") is not False)
            coverage: dict[str, Any] = value.get("coverage", {"scope": SOURCE_SCOPES[kind]}) if isinstance(value, dict) else {"scope": SOURCE_SCOPES[kind]}
            if kind == "metrics":
                total = len(_safe_metrics(raw.decode("utf-8"), limit=None))
                coverage.update(returned=len(value), total=total, limit_per_kind=MAX_ROWS, truncated=total > MAX_ROWS,
                                omitted="unallowlisted_metric_names_labels_and_malformed_lines")
            elif kind == "providers":
                total = len(json.loads(raw)["providers"])
                coverage.update(returned=len(value), total=total, truncated=len(value) < total, omitted="unallowlisted_provider_names")
            sources[name] = _source("ok" if ok else "degraded", http_status=status,
                assessed_at=value.get("as_of") if isinstance(value, dict) else None,
                source_version="sha256:" + hashlib.sha256(raw).hexdigest(),
                coverage=coverage, endpoint=path)
        except Exception:
            sources[name] = _source("unavailable", reason="read_failed", endpoint=path, coverage=SOURCE_SCOPES[kind])
    return data, sources


def _collect(fn, fallback):
    try:
        return fn()
    except Exception:
        # Exception messages may contain paths, payloads or credentials.
        return fallback, _source("unavailable", reason="source_failed")


def _cluster_live():
    """Optional existing Hermes aggregate only; never config/tasks/auth routes."""
    path = "/api/v1/cluster/status"
    coverage = {"scope": "hermes_cluster_registry_only", "unreported_task_states": "unknown",
                "independent_outcomes": "not_reported", "task_process_authority_join": "not_reported"}
    value = os.environ.get("COMPANY_OS_CLUSTER_URL")
    if not value:
        return None, _source("unavailable", reason="not_configured", optional=True, endpoint=path, coverage=coverage)
    try:
        origin = urlsplit(value)
        if origin.scheme != "http" or origin.username or origin.password or origin.path or origin.query or origin.fragment:
            raise ValueError("invalid_local_origin")
        address = ipaddress.ip_address(origin.hostname or "")
        _ = origin.port
        if address.version != 4:
            raise ValueError("invalid_local_origin")
        if not address.is_loopback:
            # Some existing services bind only the host's tailnet interface.
            # Verify actual local ownership; private ranges alone are not enough.
            interfaces, error = _run_json(["ip", "-json", "-4", "addr", "show"])
            local = {row.get("local") for interface in interfaces or [] for row in interface.get("addr_info", [])} if not error else set()
            if str(address) not in local:
                raise ValueError("invalid_local_origin")
    except (ValueError, TypeError, AttributeError):
        return None, _source("unavailable", reason="invalid_local_origin", endpoint=path, coverage=coverage)
    try:
        raw, status = _get_readonly(origin, path)
        data = json.loads(raw)
        if status != 200 or not isinstance(data, dict) or data.get("version") != "python-1.0.0" or not isinstance(data.get("tasks_by_status"), dict):
            raise ValueError("unsupported_cluster_shape")
        projected = {"cluster_ref": _alias(data.get("cluster_id")), "version": "python-1.0.0",
                     **_project(data, {**{k: _number for k in ("node_count", "online_nodes", "task_count", "uptime_seconds")},
                                       "tasks_by_status": {k: _number for k in ("pending", "ready", "running", "completed", "failed")}})}
        return projected, _source("ok", http_status=status, endpoint=path, coverage=coverage,
                                  source_version="sha256:" + hashlib.sha256(raw).hexdigest())
    except Exception:
        return None, _source("unavailable", reason="read_failed_or_unsupported_shape", endpoint=path, coverage=coverage)


def _host_metadata():
    disks = {}
    for label, path in (("home", Path.home()), ("data", Path(os.environ.get("COMPANY_OS_DATA_ROOT", "/mnt/zer0models")))):
        try:
            usage = shutil.disk_usage(path)
            pct = usage.free / usage.total * 100 if usage.total else None
            disks[label] = {"total_bytes": usage.total, "free_bytes": usage.free,
                            "free_pct": round(pct, 2) if pct is not None else None,
                            "status": "unknown" if pct is None else "critical" if pct < 2 else "warning" if pct < 10 else "ok"}
        except OSError:
            disks[label] = {"status": "unavailable", "free_pct": None}
    root = Path.home() / ".config/environment.d"
    try:
        # Metadata only, bounded; filenames and file contents never leave here.
        paths = list(itertools.islice(root.glob("*.conf"), 257))
        truncated = len(paths) > 256
        unsafe = sum(bool(p.stat().st_mode & 0o022) for p in paths[:256])
        security = {"status": "critical" if unsafe else "unknown" if truncated else "ok",
                    "unsafe_count": unsafe, "truncated": truncated}
    except OSError:
        security = {"status": "unknown", "unsafe_count": None, "truncated": None}
    data = {"disks": disks, "security": security}
    status = "ok" if security["status"] == "ok" and all(d["status"] == "ok" for d in disks.values()) else "degraded"
    return data, _source(status, observed_at=_now(), coverage="disk_and_permission_metadata_only")


def build_snapshot() -> dict[str, Any]:
    capacity_plane, capacity_source = _collect(_z0_capacity, None)
    k8s, k8s_source = _collect(_k8s, {"available": False, "pods": [], "nodes": []})
    fleet, process_source = _collect(lambda: (_process_fleet(), _source("ok", observed_at=_now(), coverage="process_presence_only")), [])
    service, service_sources = _z0_live()
    cluster, cluster_source = _collect(_cluster_live, None)
    host_meta, host_source = _collect(_host_metadata, {"security": {"status": "unknown"}, "disks": {}})
    process_source["source_version"] = "sha256:" + hashlib.sha256(json.dumps(fleet, sort_keys=True).encode()).hexdigest() if process_source.get("status") == "ok" else None
    sources = {
        **service_sources,
        "hermes_cluster": cluster_source,
        "host_metadata": host_source,
        "processes": process_source, "z0_capacity": capacity_source, "k8s": k8s_source,
        "z0": _source("unavailable", reason="control_episode_read_contract_missing"),
        "tokenomics": _source("unavailable", reason="tokenomics_read_contract_missing"),
        "memory": _source("unavailable", reason="archive_runtime_not_qualified"),
    }
    return {
        "schema": SCHEMA, "generated_at": _now(), "status": "degraded",
        "implementation": {"content_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                           "profile_ref": _alias(os.environ.get("HERMES_HOME")), "scope": "server_process_profile"},
        "sources": sources, "fleet": fleet, "capacity": service.get("providers", []), "capacity_plane": capacity_plane,
        "z0_service": service,
        "hermes_cluster": cluster,
        "economics": _economics([]), "memory": {"runtime_usable": None}, "k8s": k8s,
        **host_meta, "flow": [],
        "control": {"available": False, "schema": None, "stages": [],
                    "reason": "control_episode_read_contract_missing"},
        "coverage": {"scope": "local_partial", "fleet_limit": 100,
                     "fleet_truncated": len(fleet) == 100,
                     "gaps": ["host_session_trace_task_join", "authority_stage_receipts",
                              "tokenomics_canonical_window", "remote_hosts", "archive_runtime",
                              "memory_harness_binding_unqualified", "independent_behavior_qualification",
                              "receipt_integrity_not_deployment", "shadow_activation_unproven"],
                     "next_action": "qualify_existing_source_owned_read_contract"},
    }


@router.get("/snapshot")
def snapshot():
    return build_snapshot()


@router.get("/health")
def health():
    snap = build_snapshot()
    return {"schema": SCHEMA, "status": snap["status"], "sources": snap["sources"]}
