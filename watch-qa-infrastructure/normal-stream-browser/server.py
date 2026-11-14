from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from pathlib import Path
import os
Q=Path(__file__).resolve().parent;os.chdir(Q)
class Handler(SimpleHTTPRequestHandler):
 def do_GET(self):
  if self.path.startswith(('/range/','/fallback/')):
   route,_,name=self.path.strip('/').partition('/')
   p=Q/'fixtures'/name
   if name not in ['outer-normal-4k.ktx2.part0','outer-normal-4k.ktx2.part1']:self.send_error(404);return
   data=p.read_bytes();start=4389496 if route=='range' and name.endswith('part0') else 0
   if start and self.headers.get('Range')!='bytes=4389496-8388607':self.send_error(400);return
   self.send_response(206 if start else 200)
   if start:self.send_header('Content-Range','bytes 4389496-8388607/8388608')
   self.send_header('Content-Length',str(len(data)-start));self.end_headers();self.wfile.write(data[start:]);return
  return super().do_GET()
ThreadingHTTPServer(('127.0.0.1',8765),Handler).serve_forever()
