"""Mutation controls on disposable copies; never rewrite the owned source tree."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
API = 'hermes-plugin/dashboard/plugin_api.py'
UI = 'plugin/plugin.js'
BROWSER = 'hermes-plugin/dashboard/dist/index.js'
PYTEST = [sys.executable, '-m', 'pytest', 'tests', '-q', '--tb=short']
NODE = ['node', '--experimental-vm-modules', '--test', 'tests/test_ui.mjs']
CONTROLS = [
    ('process-substring', API, 'name = aliases.get(comm.lower())',
     'name = next((v for k,v in aliases.items() if k in comm.lower()), None)', PYTEST,
     'test_process_presence_parses_multiword_comm_and_rejects_substrings'),
    ('privacy-pass-through', API, 'return {k: _project(src.get(k), rule, depth + 1) for k, rule in schema.items()}',
     'return src', PYTEST, 'test_capacity_recursive_privacy_bounds_and_freshness'),
    ('source-failure-propagates', API, 'return fallback, _source("unavailable", reason="source_failed")',
     'raise', PYTEST, 'test_snapshot_and_health_isolate_failure_and_do_not_read_unqualified_data'),
    ('null-is-zero', UI, "const numeric = v => typeof v === 'number' && Number.isFinite(v) && v >= 0",
     'const numeric = v => Number.isFinite(Number(v)) && Number(v) >= 0', NODE,
     'production numeric/time formatters'),
    ('browser-not-registered', BROWSER, 'window.__HERMES_PLUGINS__.register(ID,',
     '((...args) => undefined)(ID,', NODE, 'shipped browser entry registers'),
]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--artifacts', required=True, type=Path)
    args = parser.parse_args()
    args.artifacts.mkdir(parents=True, exist_ok=True)
    tracked = subprocess.check_output(['git', 'ls-files', '-z', '--cached', '--others', '--exclude-standard'], cwd=ROOT).decode().split('\0')
    paths = [p for p in set(tracked) if p and (ROOT / p).is_file()]
    before = {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in paths}
    results = []
    for name, filename, old, new, command, test_name in CONTROLS:
        with tempfile.TemporaryDirectory(prefix='cos-mut-', dir=os.environ['TMPDIR']) as temp:
            dest = Path(temp)
            for relative in paths:
                target = dest / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(ROOT / relative, target)
            target = dest / filename
            original = target.read_text()
            assert original.count(old) == 1, name
            target.write_text(original.replace(old, new))
            run = subprocess.run(command, cwd=dest, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=30)
            (args.artifacts / (name + '.log')).write_text(run.stdout)
            caught = run.returncode == 1 and test_name in run.stdout
            results.append({'name': name, 'file': filename, 'test': test_name, 'command': command,
                            'exit_code': run.returncode, 'caught': caught})
    assert before == {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in paths}, 'owned source changed'
    (args.artifacts / 'mutation-receipt.json').write_text(json.dumps(results, indent=2))
    print(json.dumps(results, indent=2))
    assert all(r['caught'] for r in results), 'surviving/inconclusive mutant'


if __name__ == '__main__':
    main()
