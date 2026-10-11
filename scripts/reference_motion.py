#!/usr/bin/env python3
"""Owned loopback reference-motion endpoint; no telemetry, mutations or proxy."""
import argparse,json,os,signal,re
from http.server import ThreadingHTTPServer
from video_replica import Handler as StaticHandler,ROOT

class Handler(StaticHandler):
    def do_GET(self):
        if self.path.split('?',1)[0] in ('/motion-reference','/motion-reference/'):
            self.path=self.path.replace('/motion-reference','/video-replica',1)
        if self.path.split('?',1)[0]=='/video-replica/assets/reference.mp4':
            target=ROOT/'web/video-replica/assets/reference.mp4';size=target.stat().st_size
            start,end=0,size-1;range_header=self.headers.get('Range')
            if range_header:
                match=re.fullmatch(r'bytes=(\d+)-(\d*)',range_header)
                if not match:return self.send_error(416)
                start=int(match[1]);end=min(int(match[2]),size-1) if match[2] else size-1
                if start>end:return self.send_error(416)
            self.send_response(206 if range_header else 200)
            self.send_header('Content-Type','video/mp4');self.send_header('Accept-Ranges','bytes')
            self.send_header('Content-Length',str(end-start+1));self.send_header('Cache-Control','no-store')
            self.send_header('X-Content-Type-Options','nosniff')
            if range_header:self.send_header('Content-Range',f'bytes {start}-{end}/{size}')
            self.end_headers()
            try:
                with target.open('rb') as f:
                    f.seek(start);remaining=end-start+1
                    while remaining:
                        block=f.read(min(65536,remaining))
                        if not block:break
                        self.wfile.write(block);remaining-=len(block)
            except (BrokenPipeError,ConnectionResetError):pass
            return
        return super().do_GET()

def make_server(port=0):return ThreadingHTTPServer(('127.0.0.1',port),Handler)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--port',type=int,default=0);args=p.parse_args()
    if not 0<=args.port<=65535:p.error('Invalid port')
    def stop(*_):raise KeyboardInterrupt
    signal.signal(signal.SIGTERM,stop)
    try:
        with make_server(args.port) as server:
            print(json.dumps({'pid':os.getpid(),'url':f'http://127.0.0.1:{server.server_port}/motion-reference','root':str(ROOT),'mode':'reference-fixture-only'}),flush=True)
            server.serve_forever(poll_interval=.2)
    except KeyboardInterrupt:pass
