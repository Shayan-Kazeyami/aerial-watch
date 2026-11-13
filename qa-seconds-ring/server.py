from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from pathlib import Path
class H(SimpleHTTPRequestHandler):
 def do_GET(self):
  path=self.path.split('?')[0]
  if path.endswith('/assembly-review.js'):
   f=Path('.'+path)
   if not f.exists(): return super().do_GET()
   a=f.read_bytes()+b'\n'+Path('qa-seconds-ring/inject.js').read_bytes();self.send_response(200);self.send_header('Content-Type','text/javascript');self.send_header('Content-Length',str(len(a)));self.end_headers();self.wfile.write(a)
  elif path=='/__candidate':
   a=Path('qa-seconds-ring/candidate.json').read_bytes();self.send_response(200);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(a)));self.end_headers();self.wfile.write(a)
  else:super().do_GET()
ThreadingHTTPServer(('127.0.0.1',8768),H).serve_forever()
