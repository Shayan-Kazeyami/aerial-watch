"""Hash actual page execution responses against an external pre-run manifest."""
import asyncio,hashlib
from urllib.parse import urlsplit,urlunsplit
class ResponseIdentity:
 def __init__(self,page,expected):
  self.expected=expected;self.tasks=[];self.records=[];self.errors=[];self.verified=set();page.on('response',self.observe)
 @staticmethod
 def key(url):
  x=urlsplit(url);return urlunsplit((x.scheme,x.netloc,x.path,'',''))
 def observe(self,response):
  key=self.key(response.url)
  if key in self.expected:self.tasks.append(asyncio.create_task(self.check(response,key)))
 async def check(self,response,key):
  try:
   entry=self.expected[key];kind=response.request.resource_type;assert kind==entry['resourceType'],(key,kind)
   if response.status==304:
    assert key in self.verified,'304 without previously verified execution response'
    self.records.append({'url':response.url,'status':304,'resourceType':kind,'reuse':'Previously verified response; static immutable named source'});return
   assert response.status==200,(key,response.status)
   body=await asyncio.wait_for(response.body(),30);digest=hashlib.sha256(body).hexdigest();assert digest==entry['sha256'],(key,digest,entry['sha256']);self.verified.add(key);self.records.append({'url':response.url,'status':200,'resourceType':kind,'sha256':digest,'bytes':len(body)})
  except Exception as e:self.errors.append(repr(e))
 async def finish(self):
  # Browser functional flow must be settled before finish; no later execution expected.
  index=0
  while index<len(self.tasks):
   pending=self.tasks[index:];index=len(self.tasks);await asyncio.gather(*pending)
  missing=sorted(set(self.expected)-self.verified);assert not self.errors and not missing,{'responseIdentityErrors':self.errors,'missingActualExecutionResponses':missing}
  return {'actualExecutionResponseHashesVerified':True,'expectedUnique':len(self.expected),'records':self.records,'scope':'Actual page document/script/fetch response bytes, not APIRequestContext refetches or self-reported script hashes.'}
def expected_named(base,pins):
 return {ResponseIdentity.key(base+name):{'sha256':sha,'resourceType':'document'if name.endswith('.html')else'fetch'if name.endswith('.json')else'script'}for name,sha in pins.items()}
