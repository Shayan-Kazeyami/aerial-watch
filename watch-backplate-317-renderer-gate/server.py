from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlsplit,unquote
import os
Q=Path(__file__).resolve().parent;os.chdir(Q)
class Handler(SimpleHTTPRequestHandler):
 def do_GET(self):
  path=unquote(urlsplit(self.path).path)
  if path.endswith('/outer-normal-4k.ktx2.part0')and self.headers.get('Range'):
   if self.headers['Range']!='bytes=4389496-8388607':self.send_error(416);return
   data=Path(self.translate_path(path)).read_bytes();assert len(data)==8388608;self.send_response(206);self.send_header('Content-Range','bytes 4389496-8388607/8388608');self.send_header('Content-Length','3999112');self.end_headers();self.wfile.write(data[4389496:]);return
  super().do_GET()
ThreadingHTTPServer(('127.0.0.1',8873),Handler).serve_forever()
