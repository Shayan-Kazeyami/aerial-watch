FULL='bb022255b999645d468cc2b62100cef7c4226c3df136ab1732b40c107655d585'
def assert_snapshot(s):
 d=s['detail'];i=s['inspect'];b=s['bindings']
 assert d['required'] and d['ready'] and d['phase']=='full' and d['installedDetail']=='full'
 n=d['activeNormalIdentity'];assert n=={'bytes':16562348,'sha256':FULL,'width':4096,'height':4096,'mipLevels':13,'verified':True}
 assert not i['failed'] and not i['loading'] and i['presentation']['interactive'] and i['finish'] and i['crystals']
 assert not i['animation'] and not i['interiorAnimation']
 assert b and any(x['effectiveVisible'] for x in b),'nonempty visible R14 bindings required'
 ids=[]
 for x in b:
  assert x['materials'],'nonempty actual material bindings required'
  for m in x['materials']:
   assert m['normalUUID'] and m['width']==4096 and m['height']==4096 and m['mipLevels']==13
   ids.append(m['normalUUID'])
 assert len(set(ids))==1,'all actual R14 normal maps must share installed full texture'
# Compare explicit stable render state only; raw full snapshot retained separately.
# Do not drop arbitrary config keys or pretend a full config equality assertion.
def stable(s):
 c=s['configuration'];i=s['inspect'];d=s['detail']
 return {'detail':d,'camera':c['camera'],'renderer':c['renderer'],'premiumFace':c['premiumFace'],'renderQuality':i['renderQuality'],'view':i['view'],'finish':i['finish'],'crystals':i['crystals'],'animation':i['animation'],'interiorAnimation':i['interiorAnimation'],'inspectionDisplay':i['inspectionDisplay'],'bindings':[{'name':x['name'],'visible':x['visible'],'effectiveVisible':x['effectiveVisible'],'materials':[{k:v for k,v in m.items() if k!='normalUUID'} for m in x['materials']]} for x in s['bindings']]}

def assert_same_texture_bindings(before,after):
 def identities(s):return [(x['name'],[m['normalUUID'] for m in x['materials']]) for x in s['bindings']]
 assert identities(before)==identities(after),'same-page normal texture binding changed during screenshot'
