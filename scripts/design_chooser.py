#!/usr/bin/env python3
"""Local CompanyOS chooser. Fixed GET passthrough, no producer or profile writes."""
import argparse
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import re
import signal
import urllib.error
import urllib.request
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1] / 'web'
DEFAULT_ARTIFACTS = Path('/workspace/zer0/data/operations/company-os-recovery/design-chooser')
API_PATHS = frozenset(('/api/plugins/company-os/snapshot', '/api/plugins/company-os/health'))
MAX_BYTES = 2 * 1024 * 1024
GALLERY_FILES = tuple(f'{layout}-{theme}.png' for layout in ('spatial', 'balanced', 'dense') for theme in ('dark', 'light'))
CSP = "default-src 'self'; script-src 'self'; style-src 'self'; font-src 'self'; img-src 'self'; connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'; form-action 'none'"
ASSETS = {
    '/design-chooser/': ('design-chooser/index.html', 'text/html; charset=utf-8'),
    '/design-chooser/chooser.css': ('design-chooser/chooser.css', 'text/css; charset=utf-8'),
    '/design-chooser/chooser.js': ('design-chooser/chooser.js', 'text/javascript; charset=utf-8'),
    '/hud-v3.css': ('hud-v3.css', 'text/css; charset=utf-8'),
    '/style-preview/mark.svg': ('style-preview/mark.svg', 'image/svg+xml'),
    '/fonts/ibm-plex-mono-regular.ttf': ('fonts/ibm-plex-mono-regular.ttf', 'font/ttf'),
    '/fonts/ibm-plex-sans-regular.ttf': ('fonts/ibm-plex-sans-regular.ttf', 'font/ttf'),
}


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def make_server(port=0, *, upstream='http://127.0.0.1:18743', artifacts=DEFAULT_ARTIFACTS):
    if not re.fullmatch(r'http://127\.0\.0\.1:[0-9]{1,5}', upstream) or not 1 <= int(upstream.rsplit(':', 1)[1]) <= 65535:
        raise ValueError('upstream must be an exact http://127.0.0.1:PORT origin')
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())

    class Handler(BaseHTTPRequestHandler):
        def reply(self, status, body=b'', content_type='application/json; charset=utf-8'):
            self.send_response(status)
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Length', str(len(body)))
            self.send_header('Cache-Control', 'no-store')
            self.send_header('Content-Security-Policy', CSP)
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.send_header('Referrer-Policy', 'no-referrer')
            self.end_headers()
            if self.command != 'HEAD':
                try:
                    self.wfile.write(body)
                except (BrokenPipeError, ConnectionResetError):
                    pass

        def do_GET(self):
            authority = f'127.0.0.1:{self.server.server_address[1]}'
            if self.headers.get('Host') != authority or self.headers.get('Origin', f'http://{authority}') != f'http://{authority}' or self.headers.get('Sec-Fetch-Site') == 'cross-site':
                self.reply(403, b'{"error":"same-origin loopback only"}')
                return
            parsed = urlsplit(self.path)
            path = parsed.path
            if parsed.query and path in API_PATHS:
                self.reply(404)
                return
            if path in API_PATHS:
                if self.command != 'GET':
                    self.reject_mutation()
                    return
                try:
                    # Never relay client cookies, auth, proxy settings or redirects.
                    request = urllib.request.Request(upstream + path, method='GET', headers={'Accept': 'application/json'})
                    with opener.open(request, timeout=20) as response:
                        data = response.read(MAX_BYTES + 1)
                        if len(data) > MAX_BYTES or response.headers.get_content_type() != 'application/json':
                            raise ValueError('unexpected upstream response')
                        json.loads(data)  # validate JSON without rewriting source bytes
                    self.reply(200, data)
                except (OSError, ValueError, urllib.error.URLError):
                    self.reply(502, b'{"error":"read-only source unavailable","last_known":false}')
                return
            if path in ('/', '/design-chooser'):
                self.send_response(303)
                self.send_header('Location', '/design-chooser/')
                self.send_header('Content-Length', '0')
                self.end_headers()
                return
            if path == '/design-chooser/gallery.json':
                images = []
                for name in GALLERY_FILES:
                    file = artifacts / name
                    if not file.is_file() or file.is_symlink():
                        continue
                    data = file.read_bytes()
                    images.append({'file': name, 'layout': name.split('-')[0], 'theme': name.split('-')[1].split('.')[0],
                                   'captured_at': file.stat().st_mtime, 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()})
                self.reply(200, json.dumps({'scope': 'captured-views-not-current-telemetry', 'images': images}).encode())
                return
            if path.startswith('/design-chooser/gallery/'):
                name = path.removeprefix('/design-chooser/gallery/')
                file = artifacts / name
                if name in GALLERY_FILES and file.is_file() and not file.is_symlink():
                    self.reply(200, file.read_bytes(), 'image/png')
                else:
                    self.reply(404)
                return
            if path == '/design-chooser/inspection-model.mjs':
                self.reply(200, (ROOT.parent / 'plugin/inspection-model.mjs').read_bytes(), 'text/javascript; charset=utf-8')
                return
            asset = ASSETS.get(path)
            if asset:
                file, content_type = asset
                try:
                    self.reply(200, (ROOT / file).read_bytes(), content_type)
                except OSError:
                    self.reply(404)
                return
            self.reply(404)

        do_HEAD = do_GET

        def reject_mutation(self):
            self.reply(405, b'{"error":"read-only: GET only for API"}')

        do_POST = do_PUT = do_PATCH = do_DELETE = do_OPTIONS = reject_mutation

        def log_message(self, format, *args):
            pass

    return ThreadingHTTPServer(('127.0.0.1', port), Handler)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=0)
    parser.add_argument('--upstream', default='http://127.0.0.1:18743')
    parser.add_argument('--artifacts', type=Path, default=DEFAULT_ARTIFACTS)
    args = parser.parse_args()
    if not 0 <= args.port <= 65535:
        parser.error('--port must be between 0 and 65535')
    with make_server(args.port, upstream=args.upstream, artifacts=args.artifacts) as server:
        def stop(_signum, _frame):
            raise KeyboardInterrupt
        signal.signal(signal.SIGTERM, stop)
        print(json.dumps({'url': f'http://127.0.0.1:{server.server_port}/design-chooser/', 'pid': os.getpid(),
                          'port': server.server_port, 'upstream': args.upstream, 'mode': 'read-only-design-chooser',
                          'root': str(ROOT), 'artifacts': str(args.artifacts)}), flush=True)
        try:
            server.serve_forever(poll_interval=.2)
        except KeyboardInterrupt:
            pass


if __name__ == '__main__':
    main()
