#!/usr/bin/env python3
"""Owned local chooser + production CompanyOS router; no Hermes/profile startup."""
import argparse
from contextlib import contextmanager
import importlib.util
import json
import os
from pathlib import Path
import signal
import socket
import threading
import time

from fastapi import FastAPI
import uvicorn
from design_chooser import make_server

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ARTIFACTS = Path('/workspace/zer0/data/operations/company-os-recovery/integrated')


@contextmanager
def integrated_server(port=0, artifacts=DEFAULT_ARTIFACTS):
    """Reserve both owned listeners atomically; reap the private API on every exit."""
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        sock.listen(128)
        backend = f'http://127.0.0.1:{sock.getsockname()[1]}'
        # A public-port collision fails before importing/starting any collector.
        with make_server(port, upstream=backend, artifacts=artifacts) as chooser:
            spec = importlib.util.spec_from_file_location('company_os_integrated_api', ROOT/'hermes-plugin/dashboard/plugin_api.py')
            assert spec and spec.loader
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
            app.include_router(module.router, prefix='/api/plugins/company-os')
            api = uvicorn.Server(uvicorn.Config(app, log_level='warning', access_log=False,
                                               lifespan='off', timeout_graceful_shutdown=10))
            thread = threading.Thread(target=api.run, kwargs={'sockets':[sock]}, name='company-os-owned-api')
            thread.start()
            try:
                deadline = time.monotonic()+10
                while not api.started:
                    if not thread.is_alive() or time.monotonic() >= deadline:
                        raise RuntimeError('owned backend failed bounded startup')
                    time.sleep(.02)
                yield chooser, backend
            finally:
                api.should_exit = True
                thread.join(15)
                if thread.is_alive():
                    api.force_exit = True
                    thread.join(5)
                if thread.is_alive():
                    raise RuntimeError('owned backend failed shutdown')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=0)
    parser.add_argument('--artifacts', type=Path, default=DEFAULT_ARTIFACTS)
    args = parser.parse_args()
    if not 0 <= args.port <= 65535:
        parser.error('--port must be between 0 and 65535')
    def stop(_signum, _frame):
        raise KeyboardInterrupt
    signal.signal(signal.SIGTERM, stop)
    try:
        with integrated_server(args.port, args.artifacts) as (server, backend):
            print(json.dumps({'url':f'http://127.0.0.1:{server.server_port}/design-chooser/',
                              'pid':os.getpid(), 'port':server.server_port, 'backend':backend,
                              'mode':'integrated-read-only-chooser', 'root':str(ROOT),
                              'artifacts':str(args.artifacts)}), flush=True)
            server.serve_forever(poll_interval=.2)
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main()
