import sys,threading
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.error import HTTPError
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from reference_motion import make_server,ROOT

def test_source_video_supports_seekable_ranges():
    source=ROOT/'web/video-replica/assets/reference.mp4'
    with source.open('rb') as f:expected=f.read(64)
    with make_server(0) as server:
        th=threading.Thread(target=server.serve_forever,daemon=True);th.start()
        try:
            req=Request(f'http://127.0.0.1:{server.server_port}/video-replica/assets/reference.mp4',headers={'Range':'bytes=0-63'})
            with urlopen(req) as response:
                assert response.status==206
                assert response.headers['Content-Range']==f'bytes 0-63/{source.stat().st_size}'
                assert response.read()==expected
            req.add_header('Range',f'bytes={source.stat().st_size}-')
            try:urlopen(req)
            except HTTPError as error:assert error.code==416
            else:raise AssertionError('Invalid range accepted')
        finally:server.shutdown();th.join()
