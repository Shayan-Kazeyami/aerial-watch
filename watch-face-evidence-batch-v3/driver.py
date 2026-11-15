"""Import run_face_evidence(page, base_url, output_dir); no launch/navigation/runner."""
import json,hashlib,base64,io,math
from pathlib import Path
from PIL import Image,ImageChops
SEED_SCRIPT="""(()=>{let s=0xface402;Math.random=()=>{s=(1664525*s+1013904223)>>>0;return s/4294967296};window.__faceEvidenceSeed='face402';})();"""
async def run_face_evidence(page,base_url,output_dir):
 out=Path(output_dir);out.mkdir(parents=True,exist_ok=True);pins=json.loads((Path(__file__).parent/'SERVED_SHA256.json').read_text());records=[]
 for name,sha in pins.items():
  response=await page.request.get(base_url+name);assert response.ok;assert hashlib.sha256(await response.body()).hexdigest()==sha,name
 await page.wait_for_function('window.initializeQ333QA && window.initializeQ402QA && window.initializeQ401QA && window.__faceEvidenceReady?.()')
 assert await page.evaluate("new URLSearchParams(location.search).get('ao')==='off'&&!new URLSearchParams(location.search).has('tickBatch')")
 assert await page.evaluate("window.__faceEvidenceSeed==='face402'"),'seed must be installed before navigation'
 assert (await page.evaluate('window.__faceEvidenceState()'))['ao'] is False
 initial_scene=await page.evaluate('window.__facePinScene()');assert initial_scene['environment']is not None and initial_scene['lightShot']=='face'
 async def capture(path,handle,name,calibration,wire):
  value=await page.evaluate("({h,n,w})=>window.__faceCapture(window[h],n,w)",{'h':handle,'n':name,'w':wire})
  raw=base64.b64decode(value.pop('png').split(',',1)[1],validate=True);path.write_bytes(raw);value['calibration']=calibration;value['wireDiagnostic']=wire;path.with_suffix('.roi.json').write_text(json.dumps(value,indent=2));image=Image.open(io.BytesIO(raw)).convert('RGBA');assert list(image.size)==value['ack']['dimensions'][2:];roi=value['roi'];assert roi['viewport']==list(image.size) and roi['visibleSamples']>=100 and roi['visibleFraction']>=.6
  points=roi['samples'];domain=calibration.get('repairDomain')
  if domain:
   tri=[v['pixel']for v in domain];assert all(0<=x<image.width and 0<=y<image.height for x,y in tri),'Repair domain clipped'
   a,b,c=tri;cross=lambda a,b,c:(b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0]);area=abs(cross(a,b,c))/2;assert area>=16,'Repair domain insufficient scale'
   def inside(p):
    q=[cross(a,b,p),cross(b,c,p),cross(c,a,p)];return min(q)>=-1e-8 or max(q)<=1e-8
   points=[v for v in points if inside(v)];assert len(points)>=30,'Insufficient visible repair-domain samples'
  rgba=[image.getpixel(tuple(p))for p in points];luma=sorted(.2126*r+.7152*g+.0722*b for r,g,b,a in rgba);count=len(luma);mean=sum(luma)/count;std=math.sqrt(sum((x-mean)**2 for x in luma)/count);p05=luma[int((count-1)*.05)];p95=luma[int((count-1)*.95)];stats={'samples':count,'p05':p05,'p95':p95,'std':std,'range90':p95-p05,'opaqueFraction':sum(v[3]>=250 for v in rgba)/count,'blackFraction':sum(all(x<=2 for x in v[:3])for v in rgba)/count,'whiteFraction':sum(any(x>=253 for x in v[:3])for v in rgba)/count}
  assert value['material']['wireframe']==wire and value['material']['opacity']==1 and not value['material']['transparent']
  if not wire:
   assert stats['opaqueFraction']>=.99 and stats['blackFraction']<.2 and stats['whiteFraction']<.2,'Clipped or absent target region'
   if name=='SVG_seconds-edge-41':assert p95-p05>=12 and std>=4,'q333 target lacks useful highlight variation'
   # q402 parent is planar: a uniform well-lit cap is legitimate, not a required false highlight.
  value['regionStatistics']=stats;value['regionScope']='CPU target and optional parent-domain rays paired with actual render; numerical witness only. Human paired PBR/wire review mandatory.'
  path.write_bytes(raw);path.with_suffix('.roi.json').write_text(json.dumps(value,indent=2));return image,value
 for obj in ['q333','q402','q401']:
  init='initialize'+obj.upper()+'QA';handle='__'+obj+'QA';await page.evaluate(f'window.{init}()')
  try:
   await page.evaluate(f'window.{handle}.setup()')
   shots=([('near',None),('grazing',None)] if obj=='q333' else [(mode,parent)for parent in [397,1158]for mode in ['near','grazing']] if obj=='q402' else [(mode,face)for face in [None,35,186,8]for mode in ['fit-front','fit-grazing']])
   for mode,parent in shots:
    calibration=await page.evaluate(f'window.{handle}.fittedView({str(mode=="fit-grazing").lower()},{json.dumps(parent)})') if obj=='q401' else await page.evaluate(f'window.{handle}.view({json.dumps(mode)},{json.dumps(parent)})');await page.evaluate(f'window.{handle}.frame()');point=await page.evaluate(f'window.{handle}.pointer()');await page.evaluate('p=>window.__faceArmPointer(p.object,p.x,p.y)',point);await page.mouse.click(point['x'],point['y']);pointer_witness=await page.evaluate('window.__facePointerPromise');assert pointer_witness['freshStatusMutation'] and pointer_witness['pointer']['trusted']
    for wire in ([False,True]if obj=='q402'else[False]):
     if obj=='q402':await page.evaluate(f'window.{handle}.wire({str(wire).lower()})')
     images={};states={}
     for arm,candidate in ([('A',False),('A2',False)]if obj=='q401'else[('A',False),('B',True),('A2',False)]):
      await page.evaluate(f'window.{handle}.swap({str(candidate).lower()})');await page.evaluate(f'window.{handle}.frame()');key=f'{obj}-{parent}-{mode}-'+('wire'if wire else'pbr')+'-'+arm;image,state=await capture(out/(key+'.png'),handle,point['object'],calibration,wire);images[arm]=image;states[arm]=state;records.append({'key':key,'calibration':calibration,'pointer':point,'freshPointerWitness':pointer_witness,**state});(out/'FACE_RESULT.json').write_text(json.dumps({'status':'INCOMPLETE_PENDING_ALL_ASSERTIONS_AND_HUMAN_REVIEW','records':records},indent=2))
     assert ImageChops.difference(images['A'].convert('RGB'),images['A2'].convert('RGB')).getbbox()is None,'source RGB repeat mismatch'
     assert ImageChops.difference(images['A'].getchannel('A'),images['A2'].getchannel('A')).getbbox()is None,'source alpha repeat mismatch'
     for arm in (['A2']if obj=='q401'else['B','A2']):
      for field in ['camera','projection','target','zoom','canvas','clock']:assert states['A']['state'][field]==states[arm]['state'][field],field
      assert states['A']['material']==states[arm]['material'],'A/B/A material tuple drift'
     if obj!='q401':ImageChops.difference(images['A'].convert('RGB'),images['B'].convert('RGB')).save(out/f'{obj}-{parent}-{mode}-{wire}-difference.png')
     if obj=='q402':await page.evaluate(f'window.{handle}.wire(false)')
  finally:
   await page.evaluate("h=>{window.__facePointerCancel?.();window[h]?.dispose();}",handle)
 (out/'FACE_RESULT.json').write_text(json.dumps({'status':'CAPTURED_PENDING_HUMAN_QUALITY','records':records,'no_assumed_AB_tolerance':True},indent=2));return records
