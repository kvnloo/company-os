#!/usr/bin/env python3
"""Isolated read-only motion lab. No collector, dynamic proxy or mutation route."""
import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import mimetypes
import os
from pathlib import Path
import re
import signal
from typing import cast
import urllib.error
import urllib.request
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = Path('/workspace/zer0/data/operations/company-os-recovery/motion-prototypes')
API_PATHS = frozenset(('/api/plugins/company-os/snapshot', '/api/plugins/company-os/health'))
CAPTURES = frozenset(('baseline.png', 'trace.png', 'focus.png', 'compare.png', 'motion-tour.webm', 'gallery.json'))
CSP = "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'; connect-src 'self'; frame-src 'self'; frame-ancestors 'self'; object-src 'none'; base-uri 'none'; form-action 'none'"

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


def make_server(port=0, *, upstream='http://127.0.0.1:18747', artifacts=ARTIFACTS):
    if not re.fullmatch(r'http://127\.0\.0\.1:[0-9]{1,5}', upstream) or not 1 <= int(upstream.rsplit(':',1)[1]) <= 65535:
        raise ValueError('upstream must be an exact loopback origin')
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
    # Closed set, no arbitrary filesystem paths. Preserve the baseline bytes.
    assets = {}
    for folder in ('motion-lab', 'video-replica'):
        for path in (ROOT/'web'/folder).rglob('*'):
            if path.is_file() and not path.is_symlink() and path.suffix in ('.html','.css','.js','.mjs','.woff2','.png','.jpg'):
                assets['/'+path.relative_to(ROOT/'web').as_posix()] = path
    for folder in ('motion-lab','video-replica'):
        assets['/'+folder] = assets['/'+folder+'/'] = ROOT/'web'/folder/'index.html'

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, format, *args): pass
        def reply(self, code, data=b'', mime='application/json; charset=utf-8'):
            self.send_response(code)
            for key,value in {'Content-Type':mime,'Content-Length':str(len(data)),'Cache-Control':'no-store','Content-Security-Policy':CSP,'X-Content-Type-Options':'nosniff','Referrer-Policy':'no-referrer','Permissions-Policy':'camera=(), microphone=(), geolocation=()'}.items():
                self.send_header(key,value)
            self.end_headers()
            try: self.wfile.write(data)
            except (BrokenPipeError,ConnectionResetError): pass
        def do_GET(self):
            authority=f'127.0.0.1:{cast(ThreadingHTTPServer,self.server).server_port}'
            if self.headers.get('Host') != authority or self.headers.get('Origin',f'http://{authority}') != f'http://{authority}' or self.headers.get('Sec-Fetch-Site') == 'cross-site':
                return self.reply(403,b'{"error":"same-origin loopback only"}')
            parsed=urlsplit(self.path)
            if parsed.netloc or parsed.scheme:
                return self.reply(404)
            if parsed.path in API_PATHS:
                if parsed.query: return self.reply(404)
                try:
                    request=urllib.request.Request(upstream+parsed.path,method='GET',headers={'Accept':'application/json'})
                    with opener.open(request,timeout=20) as response:
                        data=response.read(2*1024*1024+1)
                        if len(data)>2*1024*1024 or response.headers.get_content_type()!='application/json':
                            raise ValueError('unexpected upstream')
                        json.loads(data)
                    return self.reply(200,data)
                except urllib.error.HTTPError as error:
                    status=error.code
                    error.close()
                    if status in (401,403):
                        return self.reply(status,b'{"error":"source access denied"}')
                    return self.reply(502,b'{"error":"read-only source unavailable"}')
                except (OSError,ValueError):
                    return self.reply(502,b'{"error":"read-only source unavailable"}')
            if parsed.path.startswith('/motion-lab/captures/'):
                name=parsed.path.removeprefix('/motion-lab/captures/')
                path=artifacts/name
                if name not in CAPTURES or not path.is_file() or path.is_symlink(): return self.reply(404)
            else:
                path=assets.get(parsed.path)
                if not path or not path.is_file(): return self.reply(404)
            return self.reply(200,path.read_bytes(),mimetypes.guess_type(path)[0] or 'application/octet-stream')
        def reject(self): self.reply(405,b'{"error":"GET only; view-only lab"}')
        do_POST=do_PUT=do_PATCH=do_DELETE=do_OPTIONS=do_HEAD=reject
    return ThreadingHTTPServer(('127.0.0.1',port),Handler)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port',type=int,default=0)
    parser.add_argument('--upstream',default='http://127.0.0.1:18747')
    parser.add_argument('--artifacts',type=Path,default=ARTIFACTS)
    args=parser.parse_args()
    if not 0<=args.port<=65535: parser.error('invalid port')
    def stop(*_): raise KeyboardInterrupt
    signal.signal(signal.SIGTERM,stop)
    try:
        with make_server(args.port,upstream=args.upstream,artifacts=args.artifacts) as server:
            print(json.dumps({'url':f'http://127.0.0.1:{server.server_port}/motion-lab','pid':os.getpid(),'root':str(ROOT),'upstream':args.upstream,'mode':'view-only-motion-lab'}),flush=True)
            server.serve_forever(poll_interval=.2)
    except KeyboardInterrupt: pass

if __name__=='__main__': main()
