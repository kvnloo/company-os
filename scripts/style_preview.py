#!/usr/bin/env python3
"""Serve only the static CompanyOS style preview on loopback; never opens a GUI.

No plugin loading, profile changes, filesystem browsing, APIs or telemetry.
Use --port 0 (default) for an OS-assigned port; occupied explicit ports fail.
"""
import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import signal
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1] / 'web'
ASSETS = {
    '/style-preview/': ('style-preview/index.html', 'text/html; charset=utf-8'),
    '/hud-v3.css': ('hud-v3.css', 'text/css; charset=utf-8'),
    '/style-preview/preview.js': ('style-preview/preview.js', 'text/javascript; charset=utf-8'),
    '/style-preview/mark.svg': ('style-preview/mark.svg', 'image/svg+xml'),
    '/fonts/ibm-plex-mono-regular.ttf': ('fonts/ibm-plex-mono-regular.ttf', 'font/ttf'),
    '/fonts/ibm-plex-sans-regular.ttf': ('fonts/ibm-plex-sans-regular.ttf', 'font/ttf'),
}
CSP = "default-src 'self'; script-src 'self'; style-src 'self'; font-src 'self'; img-src 'self'; connect-src 'none'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'; form-action 'none'"


class PreviewHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = urlsplit(self.path).path
        if path in ('/', '/style-preview'):
            self.send_response(303)
            self.send_header('Location', '/style-preview/')
            self.send_header('Content-Length', '0')
            self.end_headers()
            return
        asset = ASSETS.get(path)
        if asset is None:
            self.send_error(404)
            return
        file, content_type = asset
        data = (ROOT / file).read_bytes()
        self.send_response(200)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(data)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('Content-Security-Policy', CSP)
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Referrer-Policy', 'no-referrer')
        self.end_headers()
        if self.command != 'HEAD':
            self.wfile.write(data)

    do_HEAD = do_GET

    def reject_mutation(self):
        self.send_error(405, 'Static preview: GET and HEAD only')

    do_POST = do_PUT = do_PATCH = do_DELETE = do_OPTIONS = reject_mutation

    def log_message(self, format, *args):
        pass


def make_server(port=0):
    return ThreadingHTTPServer(('127.0.0.1', port), PreviewHandler)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=0)
    args = parser.parse_args()
    if not 0 <= args.port <= 65535:
        parser.error('--port must be between 0 and 65535')
    with make_server(args.port) as server:
        def stop(_signum, _frame):
            raise KeyboardInterrupt
        signal.signal(signal.SIGTERM, stop)
        print(json.dumps({'url': f'http://127.0.0.1:{server.server_port}/style-preview/',
                          'port': server.server_port, 'pid': os.getpid(),
                          'mode': 'static-style-preview', 'root': str(ROOT)}), flush=True)
        try:
            server.serve_forever(poll_interval=.2)
        except KeyboardInterrupt:
            pass


if __name__ == '__main__':
    main()
