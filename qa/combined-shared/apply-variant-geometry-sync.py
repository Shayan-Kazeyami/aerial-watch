from pathlib import Path
import hashlib,json,os,sys
r=Path(sys.argv[1]).resolve()
assert Path(os.environ['RUNNER_TEMP']).resolve() in r.parents
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
a=r/'leather-assets/r14/leather.gltf';v=r/'leather-assets/r14/leather-qa-avif-gentle.gltf'
assert sha(a)=='864fb10cee26bdc3befde7c4a76c4368862ed6c97efb261c768668f493ca8b86'
old='190126a6ca428f726bc6eeb814f1c1990ca10396847fa25b5062b8f98bc4f46e'
assert sha(v)==old
canonical=json.loads(a.read_text());original=json.loads(v.read_text())
assert canonical['buffers']==[{'uri':'geometry.bin','byteLength':8814096}]
assert original['buffers']==[{'uri':'geometry.bin','byteLength':6184988}]
keys=['images','textures','extensionsUsed']
result={**canonical,**{k:original[k] for k in keys}}
assert all(result[k]==canonical[k] for k in canonical if k not in keys)
assert all(result[k]==original[k] for k in keys)
assert result['asset']['extras']['authoredGeometryId']=='strap-hinge-skin-sourcecharts-r16-candidate'
blob=json.dumps(result,separators=(',',':'),ensure_ascii=False).encode()
assert len(blob)==12934,('review unexpected variant bytes',len(blob))
before=sha(r/'quality-study/viewer-revision.json')
p=v.with_suffix('.sync-tmp');p.write_bytes(blob);p.replace(v)
p=r/'deployment-manifest.json';m=json.loads(p.read_text())
entries=[e for e in m['files'] if e['path']=='leather-assets/r14/leather-qa-avif-gentle.gltf']
assert len(entries)==1 and entries[0]['sha256']==old
entries[0].update(sizeBytes=len(blob),sha256=sha(v))
tmp=p.with_suffix('.sync-tmp');tmp.write_text(json.dumps(m,indent=2)+'\n');tmp.replace(p)
assert sha(r/'quality-study/viewer-revision.json')==before
receipt={'beforeVariantSha256':old,'afterVariantSha256':sha(v),'variantBytes':len(blob),'sourceManifestSha256':sha(p),'canonicalSha256':sha(a),'rootSourceDigest':json.loads((r/'quality-study/viewer-revision.json').read_text())['digest'],'scope':'Explicit source asset overlay; canonical geometry/node/identity metadata plus exact original AVIF image/texture/extension fields. Not byte-identical prior source tree.'}
print(json.dumps(receipt,indent=2))
Path(os.environ['RUNNER_TEMP'],'variant-sync-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
