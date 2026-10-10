"""Isolated reference replica: a static, non-authoritative endpoint."""
import importlib.util
import threading
import unittest
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import HTTPError

ROOT = Path(__file__).resolve().parents[1]

class ReplicaServerTest(unittest.TestCase):
    def test_native_replica_is_served_without_backend(self):
        path = ROOT/'scripts/video_replica.py'
        self.assertTrue(path.exists(), 'Standalone replica server is missing')
        spec = importlib.util.spec_from_file_location('video_replica', path)
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with module.make_server(0) as server:
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                origin = f'http://127.0.0.1:{server.server_port}'
                body = urlopen(origin+'/video-replica').read().decode()
                self.assertIn('Reference fixture', body)
                self.assertIn('replica-frame', body)
                self.assertIn('1496', body)
                with self.assertRaises(HTTPError) as error:
                    urlopen(origin+'/api/plugins/company-os/snapshot')
                self.assertEqual(error.exception.code, 404)
                error.exception.close()
                with self.assertRaises(HTTPError) as error:
                    urlopen(Request(origin+'/video-replica',method='POST',data=b'{}'))
                self.assertEqual(error.exception.code, 405)
                error.exception.close()
            finally:
                server.shutdown()
                thread.join(2)

if __name__ == '__main__':
    unittest.main()
