"""Diagnostic browser gate using the installed Hermes registry/SDK sources.
No full Hermes startup (which can bootstrap credentials/runtimes), profile edits,
or GUI auto-open. A small owned FastAPI server mounts the production router.
"""
import argparse
import importlib.util
import json
from pathlib import Path
import subprocess


from fastapi import FastAPI
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

ROOT = Path(__file__).resolve().parents[1]


def make_app(assets):
    spec = importlib.util.spec_from_file_location('company_os_diagnostic', ROOT / 'hermes-plugin/dashboard/plugin_api.py')
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
    app.include_router(module.router, prefix='/api/plugins/company-os')
    app.mount('/dashboard-plugins/company-os', StaticFiles(directory=ROOT / 'hermes-plugin/dashboard'), name='company-os')
    @app.get('/api/dashboard/plugins')
    def manifests():
        return [json.loads((ROOT / 'hermes-plugin/dashboard/manifest.json').read_text())]
    @app.get('/company-os-network')
    def page():
        return HTMLResponse('<!doctype html><html><head><meta charset="utf-8"><title>CompanyOS isolated diagnostic</title></head><body><div id="root"></div><script src="/diagnostic-host.js"></script></body></html>', headers={'Cache-Control': 'no-store'})
    @app.get('/diagnostic-host.js')
    def host_bundle():
        return FileResponse(assets / 'diagnostic-host.js', media_type='text/javascript')
    return app


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--hermes-root', required=True, type=Path)
    parser.add_argument('--artifacts', required=True, type=Path)
    parser.add_argument('--port', type=int, default=0)
    parser.add_argument('--test-browser', action='store_true')
    parser.add_argument('--chromium', default='/usr/bin/chromium')
    args = parser.parse_args()
    if args.test_browser:
        import sys
        subprocess.run([sys.executable, str(ROOT / 'scripts/test-inspector.py'),
                        '--hermes-root', str(args.hermes_root), '--artifacts', str(args.artifacts),
                        '--port', str(args.port), '--chromium', args.chromium], check=True)
        return
    args.artifacts.mkdir(parents=True, exist_ok=True)
    subprocess.run(['node', str(ROOT / 'scripts/build-diagnostic.mjs'), str(args.hermes_root), str(args.artifacts)], check=True)
    import socket
    sock = socket.socket()
    sock.bind(('127.0.0.1', args.port))
    port = sock.getsockname()[1]
    sock.listen(128)
    app = make_app(args.artifacts)
    server = uvicorn.Server(uvicorn.Config(app, log_level='warning', lifespan='off'))
    url = f'http://127.0.0.1:{port}'
    print(json.dumps({'url': url + '/company-os-network', 'api': url + '/api/plugins/company-os/snapshot', 'mode': 'isolated-diagnostic'}), flush=True)
    server.run(sockets=[sock])


if __name__ == '__main__':
    main()
