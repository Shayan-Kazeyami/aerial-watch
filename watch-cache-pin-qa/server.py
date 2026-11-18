from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
class Handler(SimpleHTTPRequestHandler):
 def end_headers(self):
  self.send_header('Cache-Control','public,max-age=600');super().end_headers()
ThreadingHTTPServer(('127.0.0.1',8765),Handler).serve_forever()
