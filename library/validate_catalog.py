#!/usr/bin/env python3
"""Dependency-free static validator for CompanyOS's declarative UI catalogs.

This checks *catalog metadata*, not data availability, screen pixels, live
Hermes installation, permissions, or model-generated view correctness.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PHASES = {"P0", "P1", "P2", "P3"}
AVAILABILITY = {"pr3_draft_projection", "needs_adapter", "fixture_only"}
SCENE_READINESS = {"draft-pr3-data", "needs-source-join", "fixture-only"}
REGIONS = {"header", "center", "left", "right", "overlay"}


def fail(message: str) -> None:
    raise ValueError(message)


def load(name: str) -> dict:
    with (ROOT / name).open(encoding="utf-8") as stream:
        result = json.load(stream)
    if not isinstance(result, dict):
        fail(f"{name}: root must be an object")
    return result


def validate() -> tuple[int, int]:
    components_doc = load("components.v1.json")
    dashboards_doc = load("dashboards.v1.json")
    if components_doc.get("schema") != "companyos.component_catalog.v1":
        fail("wrong component schema")
    if dashboards_doc.get("schema") != "companyos.dashboard_catalog.v1":
        fail("wrong dashboard schema")

    comps = components_doc.get("components")
    scenes = dashboards_doc.get("scenes")
    if not isinstance(comps, list) or not isinstance(scenes, list):
        fail("components and scenes must be arrays")
    component_ids: set[str] = set()
    phase_counts: dict[str, int] = {}
    for c in comps:
        if not isinstance(c, dict):
            fail("component must be object")
        ident = c.get("id")
        if not isinstance(ident, str) or not ident or ident in component_ids:
            fail(f"missing or duplicate component id: {ident!r}")
        component_ids.add(ident)
        phase = c.get("phase")
        if phase not in PHASES:
            fail(f"{ident}: invalid phase")
        phase_counts[phase] = phase_counts.get(phase, 0) + 1
        if c.get("availability") not in AVAILABILITY:
            fail(f"{ident}: unrecognized availability")
        if c.get("mutation_authority") != "none":
            fail(f"{ident}: catalog must not own executable authority")
        for key in ("question", "truth_guard", "source_contract"):
            if not isinstance(c.get(key), str) or not c[key].strip():
                fail(f"{ident}: {key} required")
        if c["availability"] != "pr3_draft_projection" and c.get("source_path") is not None:
            fail(f"{ident}: unimplemented source must not invent a live data path")
        if not isinstance(c.get("allowed_interactions"), list):
            fail(f"{ident}: interactions must be a list")
        if c.get("detail_levels") != ["glance", "focus", "evidence"]:
            fail(f"{ident}: semantic zoom must preserve evidence tier")
    if phase_counts.get("P0") != 6:
        fail(f"expected 6 P0 component candidates, found {phase_counts.get('P0')}")

    scene_ids: set[str] = set()
    p0_scenes = 0
    for scene in scenes:
        if not isinstance(scene, dict):
            fail("dashboard must be object")
        ident = scene.get("id")
        if not isinstance(ident, str) or not ident or ident in scene_ids:
            fail(f"missing or duplicate dashboard id: {ident!r}")
        scene_ids.add(ident)
        if scene.get("phase") not in PHASES or scene.get("readiness") not in SCENE_READINESS:
            fail(f"{ident}: unrecognized phase/readiness")
        if scene["phase"] == "P0":
            p0_scenes += 1
        regions = scene.get("regions")
        if not isinstance(regions, dict) or set(regions) != REGIONS:
            fail(f"{ident}: missing/extra layout region")
        for region, children in regions.items():
            if not isinstance(children, list):
                fail(f"{ident}.{region} must be list")
            for child in children:
                if child not in component_ids:
                    fail(f"{ident}.{region}: unknown component {child!r}")
        if not isinstance(scene.get("truth_rule"), str) or not scene["truth_rule"]:
            fail(f"{ident}: truth rule required")
        if scene.get("readiness") == "fixture-only" and scene.get("phase") != "P3":
            fail(f"{ident}: fixture-only scene must not appear production ready")
    if p0_scenes != 2:
        fail(f"expected 2 P0 scenes, found {p0_scenes}")
    return len(comps), len(scenes)


if __name__ == "__main__":
    try:
        n_components, n_scenes = validate()
    except (ValueError, OSError, json.JSONDecodeError) as error:
        print(f"catalog FAIL: {error}", file=sys.stderr)
        sys.exit(1)
    print(f"catalog OK: {n_components} component definitions / {n_scenes} scenes; static only")
