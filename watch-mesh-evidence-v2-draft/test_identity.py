import asyncio,hashlib
from identity import ResponseIdentity,expected_named
class Page:
 def on(self,n,f):self.callback=f
class Response:
 status=200
 def __init__(self,url,body,kind='script'):self.url=url;self.value=body;self.request=type('Request',(),{'resource_type':kind})()
 async def body(self):return self.value
async def run():
 url='http://127.0.0.1/module.js';expected=expected_named('http://127.0.0.1/',{'module.js':hashlib.sha256(b'actual').hexdigest()});p=Page();q=ResponseIdentity(p,expected);p.callback(Response(url+'?v=1',b'actual'));await q.finish();r=Response(url,b'');r.status=304;p.callback(r);assert(await q.finish())['actualExecutionResponseHashesVerified']
 for body,kind in [(b'wrong','script'),(b'actual','fetch')]:
  p=Page();q=ResponseIdentity(p,expected);p.callback(Response(url,body,kind))
  try:await q.finish()
  except AssertionError:pass
  else:raise AssertionError('invalid response accepted')
 p=Page();q=ResponseIdentity(p,expected)
 try:await q.finish()
 except AssertionError:pass
 else:raise AssertionError('missing response accepted')
 print('PASS actual-response collector arithmetic/missing/wrong-byte/wrong-role/cached-prior guards using fake response API. Not browser execution proof.')
asyncio.run(run())
