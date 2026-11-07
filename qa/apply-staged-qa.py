import hashlib,json,pathlib,sys
root=pathlib.Path('candidate')
sha=lambda b:hashlib.sha256(b).hexdigest()
guards={'assembly-render-pipeline.js':'a1c48b096c3089471e9a448bad143253c7c67c9a386248c761c0456f0ff1d8b1','assembly-review.js':'52eb488530ef8edc3f3f1535d8240b13e1ab295881abbb26a69e623aa9dce0b8','vendor/three.module.js':'104f56145899722094556490d787aae0617cc2fc3382f31df02d724ea1aee341'}
guards.update({"vendor/postprocessing/RenderPass.js":"817f6c3cdcd0fd41515d112359ea0532568eefb5aabd3b33903957ebca1b8a6a","vendor/postprocessing/GTAOPass.js":"78f278563029f53a97c662bf9bcc5bf89b12b3e9ab2b80270dbb53c2d0a81162","vendor/postprocessing/UnrealBloomPass.js":"ba8f2fcadfa6588384c9473498f974d81d120f02f0e63a0e59c265202a006b5a","vendor/postprocessing/SMAAPass.js":"1a96804b8cb33ba76a67f9a8e77f2d5e2bf47b1a5c9a8476901aa75e24acb85c","vendor/postprocessing/OutputPass.js":"02e4a261af34de71338185e9e87f0cbe5cba9115608d984363e1269dec1d2272","vendor/postprocessing/EffectComposer.js":"4e079a5886152d7e529a59aef644e968ab4d32c6a33ce016b36bf29b2eac26f7"})
for p,h in guards.items():assert sha((root/p).read_bytes())==h,'baseline guard '+p
assert json.loads((root/'quality-study/viewer-revision.json').read_text())['digest']=='947d891f95f7be19219ca3c7f7f2ca78aeae52fef8d41d0a7d42e48421a48063'
payload=json.loads(pathlib.Path('qa/staged-source.json').read_text())
assert set(payload)=={'assembly-render-pipeline.js','assembly-review.js','qa-staged-capture.js','quality-study/viewer-revision.json','quality-study/viewer-revision.js'}
for p,s in payload.items():(root/p).write_text(s)
revision=json.loads((root/'quality-study/viewer-revision.json').read_text())
assert revision['digest']=='7056ba7ec7e6ea45ae4dcd4ef19e45e0f70744df762d45d2ddc7f3534d4d5ce4'
assert sha(json.dumps(revision['files'],separators=(',',':')).encode())==revision['digest']
for f in revision['files']:
 b=(root/f['path']).read_bytes();assert len(b)==f['bytes'] and sha(b)==f['sha256'],'QA source mismatch '+f['path']
manifest=json.loads((root/'deployment-manifest.json').read_text());rows={f['path']:f for f in manifest['files']}
for p in payload:
 b=(root/p).read_bytes();rows[p]={**rows.get(p,{}),'path':p,'sizeBytes':len(b),'sha256':sha(b)}
manifest['files']=sorted(rows.values(),key=lambda f:f['path']);(root/'deployment-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('QA-only staged hooks applied; original render algorithms, Studio and budget unchanged; distinct source digest '+revision['digest'])
