"""Reviewed-fixture candidate. Import is inert; CLI starts loopback only."""
from pathlib import Path
import hashlib,json,mimetypes
from http.server import BaseHTTPRequestHandler,HTTPServer
from urllib.parse import urlsplit,unquote
R=Path(__file__).resolve().parent
sha=lambda b:hashlib.sha256(b).hexdigest()
def inventory():
 d=json.loads((R/'CLOSURE_RESOLUTION.json').read_text()); assert d['all_manifest_files_verified']
 import os
 staging=Path(os.environ['CASE_FIXTURE_STAGING']).resolve(strict=True)
 files={x['url_path']:(staging/x['url_path'].lstrip('/'),x['expected_sha256'])for x in d['rows']}
 for name,h in d['root_entry_pins_separate_from_release_manifest'].items():files['/'+name]=(staging/name,h)
 files['/']=files['/index.html']
 for p,h in files.values():
  assert p.resolve(strict=True).is_relative_to(staging), 'Escaping fixture root'
  assert p.is_file() and sha(p.read_bytes())==h, str(p)
 return files
class Handler(BaseHTTPRequestHandler):
 def do_GET(self):
  raw=urlsplit(self.path).path
  decoded=unquote(raw)
  if decoded!=raw or '\\'in raw or any(x in ('.','..')for x in raw.split('/')):self.send_error(400);return
  parts=raw.split('/',2)
  if len(parts)!=3 or parts[1]not in ('baseline','candidate'):self.send_error(404);return
  variant=parts[1];key='/'+parts[2]
  item=self.server.files.get(key)
  if not item:self.send_error(404);return
  p,h=item
  if key.endswith('/assembly-hybrid-case.js'):
   p=R/(variant+'-assembly-hybrid-case.js');h=self.server.overrides[p.name]
  data=p.read_bytes()
  if sha(data)!=h:self.send_error(409,'Pinned bytes changed');return
  self.send_response(200);self.send_header('Content-Type',mimetypes.guess_type(str(p))[0]or'application/octet-stream');self.send_header('Content-Length',str(len(data)));self.send_header('Cache-Control','no-store');self.send_header('X-Fixture-SHA256',h);self.end_headers();self.wfile.write(data)
 def log_message(self,fmt,*args):pass
 def do_POST(self):self.send_error(405)
def make_server(port=8768):
 files=inventory(); prep=json.loads((R/'PREPARATION.json').read_text());
 for n,h in prep['overrides'].items():assert sha((R/n).read_bytes())==h
 s=HTTPServer(('127.0.0.1',port),Handler);s.files=files;s.overrides=prep['overrides'];return s
if __name__=='__main__':make_server().serve_forever()
