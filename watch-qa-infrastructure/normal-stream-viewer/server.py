from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlsplit,unquote
import os
Q=Path(__file__).resolve().parent;arm=os.environ['QA_ARM'];assert arm in ['baseline','candidate'];root=Q/('prepared-v2-'+arm);os.chdir(root)
class Handler(SimpleHTTPRequestHandler):
 def do_GET(self):
  path=unquote(urlsplit(self.path).path)
  if path.endswith('/outer-normal-4k.ktx2.part0') and self.headers.get('Range'):
   if self.headers['Range']!='bytes=4389496-8388607':self.send_error(416);return
   p=Path(self.translate_path(path));data=p.read_bytes();assert len(data)==8388608
   self.send_response(206);self.send_header('Content-Range','bytes 4389496-8388607/8388608');self.send_header('Content-Length','3999112');self.end_headers();self.wfile.write(data[4389496:]);return
  return super().do_GET()
ThreadingHTTPServer(('127.0.0.1',8765),Handler).serve_forever()
