"""Read-only loopback playback of progressively rendered local review media."""
import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import re
from urllib.parse import urlsplit

from .paired_viewer import send_video


def server(root, port=8777, broadcast_video=None):
    root=Path(root).resolve()
    html=Path(__file__).resolve().parents[1]/'viewer/long-visual.html'
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.headers.get('Host') not in (f'127.0.0.1:{self.server.server_port}',f'localhost:{self.server.server_port}'):
                self.send_error(403);return
            path=urlsplit(self.path).path
            if path=='/':payload,kind=html.read_bytes(),'text/html; charset=utf-8'
            elif path=='/api/status':
                status=root/'status.json'
                value=json.loads(status.read_text(encoding='utf-8')) if status.exists() else {'complete':False,'processed_frames':0,'total_frames':7500,'ready_seconds':0,'chunks':[],'preparing':True}
                payload,kind=json.dumps(value,ensure_ascii=False).encode(),'application/json'
            elif path=='/api/mapping':
                mapping=root/'mapping.json'
                payload,kind=mapping.read_bytes() if mapping.exists() else b'{"segments":[]}','application/json'
            elif path=='/video/broadcast' and broadcast_video:
                send_video(self,Path(broadcast_video));return
            elif re.fullmatch(r'/media/(part-\d{3}\.mp4|first-five-minutes\.mp4)',path):
                target=root/path.rsplit('/',1)[-1]
                if not target.is_file():self.send_error(404);return
                send_video(self,target);return
            else:self.send_error(404);return
            self.send_response(200);self.send_header('Content-Type',kind)
            self.send_header('Content-Length',str(len(payload)));self.send_header('Cache-Control','no-store')
            self.end_headers();self.wfile.write(payload)
        def log_message(self,*args):pass
    return ThreadingHTTPServer(('127.0.0.1',port),Handler)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',required=True);parser.add_argument('--port',type=int,default=8777)
    parser.add_argument('--broadcast-video')
    args=parser.parse_args()
    server(args.root,args.port,args.broadcast_video).serve_forever()
