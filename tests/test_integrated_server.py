"""One-process integrated launcher: production router, fixed chooser proxy."""
import hashlib
import json
import os
import select
import subprocess
import sys
from pathlib import Path
import pytest
from test_design_chooser import read, ARTIFACTS, API

ROOT = Path(__file__).resolve().parents[1]



def test_integrated_server_serves_owned_backend_and_preserves_collision_owner(integrated_server):
    receipt = integrated_server
    origin = receipt['url'].split('/design-chooser/')[0]
    status, raw, _ = read(origin+API+'snapshot')
    assert status == 200
    snapshot = json.loads(raw)
    assert snapshot['implementation']['content_sha256'] == hashlib.sha256((ROOT/'hermes-plugin/dashboard/plugin_api.py').read_bytes()).hexdigest()
    assert {'z0_bridge', 'z0_evaluation', 'hermes_cluster'} <= snapshot['sources'].keys()
    assert snapshot['economics']['observed_cost_usd'] is None
    assert read(origin+'/design-chooser/inspection-model.mjs')[1] == (ROOT/'plugin/inspection-model.mjs').read_bytes()
    collision = subprocess.run([sys.executable, str(ROOT/'scripts/integrated_chooser.py'), '--port', str(receipt['port'])],capture_output=True,timeout=10)
    assert collision.returncode != 0
    assert read(receipt['url'])[0] == 200
    assert read(origin+API+'snapshot', method='POST')[0] == 405
    assert read(origin+API+'snapshot?url=elsewhere')[0] == 404
    assert read(origin+API+'snapshot', headers={'Host':'attacker.invalid'})[0] == 403
    (ARTIFACTS/'integrated-api-receipt.json').write_text(json.dumps({'launch':receipt,'snapshot':snapshot,'collision_exit':collision.returncode},indent=2))
