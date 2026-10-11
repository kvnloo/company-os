"""HTTP contract for the isolated motion lab; no production listeners touched."""
import importlib.util
from pathlib import Path
import threading
import unittest
import urllib.request
from urllib.error import HTTPError

ROOT = Path(__file__).resolve().parents[1]

class MotionServerTests(unittest.TestCase):
    def test_owned_loopback_route_and_reference(self):
        self.assertTrue((ROOT/'scripts/motion_lab.py').exists(), 'motion lab server must exist')
        spec = importlib.util.spec_from_file_location('motion_lab', ROOT/'scripts/motion_lab.py')
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with module.make_server(0) as server:
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            base = f'http://127.0.0.1:{server.server_port}'
            try:
                with urllib.request.urlopen(base+'/motion-lab', timeout=5) as response:
                    self.assertEqual(response.status, 200)
                    self.assertIn(b'CompanyOS', response.read())
                with urllib.request.urlopen(base+'/video-replica', timeout=5) as response:
                    self.assertEqual(response.status, 200)
                    self.assertIn("frame-ancestors 'self'", response.headers['Content-Security-Policy'])
                for path, method, code in [('/api/arbitrary','GET',404),('/motion-lab','POST',405),('/motion-lab/%2e%2e/README.md','GET',404)]:
                    with self.assertRaises(HTTPError) as error:
                        urllib.request.urlopen(urllib.request.Request(base+path, method=method),timeout=5)
                    self.assertEqual(error.exception.code,code)
                    error.exception.close()
            finally:
                server.shutdown()
                thread.join(3)

    def test_proxy_is_fixed_get_only_and_preserves_source_bytes(self):
        from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
        spec=importlib.util.spec_from_file_location('motion_lab',ROOT/'scripts/motion_lab.py')
        assert spec and spec.loader
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        received=[]
        payload=b'{"fixture":true,"zero":0,"null":null,"false":false}'
        mode={'status':200}
        class Fixture(BaseHTTPRequestHandler):
            def log_message(self, format, *args): pass
            def do_GET(self):
                received.append({'path':self.path,'cookie':self.headers.get('Cookie'),'authorization':self.headers.get('Authorization')})
                self.send_response(mode['status']);self.send_header('Content-Type','application/json')
                if mode['status']==302:self.send_header('Location','http://127.0.0.1:1/not-allowed')
                self.end_headers();self.wfile.write(payload)
        with ThreadingHTTPServer(('127.0.0.1',0),Fixture) as upstream:
            uthread=threading.Thread(target=upstream.serve_forever,daemon=True);uthread.start()
            with module.make_server(0,upstream=f'http://127.0.0.1:{upstream.server_port}') as server:
                thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
                base=f'http://127.0.0.1:{server.server_port}'
                try:
                    request=urllib.request.Request(base+'/api/plugins/company-os/snapshot',headers={'Cookie':'fixture-only','Authorization':'fixture-only'})
                    with urllib.request.urlopen(request,timeout=5) as response:self.assertEqual(response.read(),payload)
                    self.assertEqual(received,[{'path':'/api/plugins/company-os/snapshot','cookie':None,'authorization':None}])
                    for path,method,headers,code in [('/api/plugins/company-os/snapshot?url=elsewhere','GET',{},404),('/api/plugins/company-os/snapshot','POST',{},405),('/api/plugins/company-os/snapshot','GET',{'Origin':'https://example.invalid'},403),('/motion-lab','GET',{'Host':'example.invalid'},403)]:
                        with self.assertRaises(HTTPError) as error:urllib.request.urlopen(urllib.request.Request(base+path,method=method,headers=headers),timeout=5)
                        self.assertEqual(error.exception.code,code);error.exception.close()
                    self.assertEqual(len(received),1)
                    for status,expected in [(403,403),(401,401),(302,502)]:
                        mode['status']=status
                        with self.assertRaises(HTTPError) as error:urllib.request.urlopen(base+'/api/plugins/company-os/snapshot',timeout=5)
                        self.assertEqual(error.exception.code,expected);error.exception.close()
                    self.assertEqual(len(received),4)
                    with self.assertRaises(OSError): module.make_server(server.server_port)
                finally:server.shutdown();thread.join(3)
            upstream.shutdown();uthread.join(3)

if __name__ == '__main__': unittest.main()
