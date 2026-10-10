"""Owned integrated runtime for live browser/API tests. No shared restart."""
import json
import os
import select
import subprocess
import sys
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]

@pytest.fixture(scope='module')
def integrated_server():
    from test_design_chooser import ARTIFACTS, API, read
    runner = ROOT / 'scripts/integrated_chooser.py'
    assert runner.is_file(), 'integrated launcher must own its production backend and chooser'
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    log = (ARTIFACTS / 'integrated-server-stderr.log').open('w')
    process = subprocess.Popen([sys.executable, str(runner), '--port', '0', '--artifacts', str(ARTIFACTS)],
                               stdout=subprocess.PIPE, stderr=log, text=True, env={**os.environ, 'PYTHONDONTWRITEBYTECODE':'1'})
    try:
        assert process.stdout is not None
        assert select.select([process.stdout], [], [], 20)[0], 'bounded startup'
        receipt = json.loads(process.stdout.readline())
        assert receipt['pid'] == process.pid
        assert read(receipt['url'])[0] == 200
        yield receipt
    finally:
        process.terminate()
        process.communicate(timeout=30)
        log.close()
        assert process.returncode == 0
    for origin in (receipt['url'].split('/design-chooser/')[0], receipt['backend']):
        import urllib.error, urllib.request
        with pytest.raises(urllib.error.URLError):
            urllib.request.urlopen(origin+API+'snapshot', timeout=2)

