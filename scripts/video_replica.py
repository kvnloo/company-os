#!/usr/bin/env python3
"""Serve only the owned reference study; no telemetry, proxy, or mutation API."""
import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import json
import mimetypes
import os
import signal
from urllib.parse import urlsplit, unquote

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT/'web/video-replica'

class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def do_GET(self):
        path = unquote(urlsplit(self.path).path)
        if path in ('/video-replica', '/video-replica/'):
            target = WEB/'index.html'
        elif path.startswith('/video-replica/'):
            target = (WEB/path.removeprefix('/video-replica/')).resolve()
            if not target.is_relative_to(WEB.resolve()):
                return self.send_error(404)
        else:
            return self.send_error(404)
        if not target.is_file():
            return self.send_error(404)
        data = target.read_bytes()
        self.send_response(200)
        self.send_header('Content-Type', mimetypes.guess_type(target)[0] or 'application/octet-stream')
        self.send_header('Content-Length', str(len(data)))
        self.send_header('Cache-Control','no-store')
        self.send_header('X-Content-Type-Options','nosniff')
        self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'; connect-src 'none'; frame-ancestors 'none'")
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self): self.send_error(405)
    def do_PUT(self): self.send_error(405)
    def do_DELETE(self): self.send_error(405)
    def do_PATCH(self): self.send_error(405)


def make_server(port=0):
    return ThreadingHTTPServer(('127.0.0.1', port), Handler)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port',type=int,default=0)
    args=parser.parse_args()
    if not 0<=args.port<=65535: parser.error('Invalid port')
    def stop(*_args): raise KeyboardInterrupt
    signal.signal(signal.SIGTERM,stop)
    try:
        with make_server(args.port) as server:
            print(json.dumps({'url':f'http://127.0.0.1:{server.server_port}/video-replica','pid':os.getpid(),'root':str(ROOT),'mode':'reference-fixture-only'}),flush=True)
            server.serve_forever(poll_interval=.2)
    except KeyboardInterrupt:
        pass

if __name__=='__main__': main()
