import hashlib,json,pathlib,os,subprocess
root=pathlib.Path('candidate');variant=os.environ['TIMING_VARIANT'];sha=lambda b:hashlib.sha256(b).hexdigest()
assert variant in ['baseline','candidate']
if variant=='candidate': subprocess.run(['python3','qa/apply-validity.py'],check=True)
r=json.loads((root/'quality-study/viewer-revision.json').read_text())
assert r['digest']==({'baseline':'947d891f95f7be19219ca3c7f7f2ca78aeae52fef8d41d0a7d42e48421a48063','candidate':'761258214fcbe5fe1597db826d381c3099c1586b2946884e2159b8d3b42a06cb'}[variant])
assert sha((root/'assembly-render-pipeline.js').read_bytes())=='a1c48b096c3089471e9a448bad143253c7c67c9a386248c761c0456f0ff1d8b1'
data=pathlib.Path('qa/timing-pipeline.js').read_bytes();(root/'assembly-render-pipeline.js').write_bytes(data)
for f in r['files']:
 if f['path']=='assembly-render-pipeline.js': f.update(bytes=len(data),sha256=sha(data))
r['baselineDigest']=r['digest'];r['scope']='QA render timing only over '+variant+' source; unchanged runtime deadlines and selected quality';r['digest']=sha(json.dumps(r['files'],separators=(',',':')).encode())
(root/'quality-study/viewer-revision.json').write_text(json.dumps(r,indent=2)+'\n');(root/'quality-study/viewer-revision.js').write_text('export default '+json.dumps(r,separators=(',',':'))+';\n')
for f in r['files']:
 b=(root/f['path']).read_bytes();assert len(b)==f['bytes'] and sha(b)==f['sha256']
m=json.loads((root/'deployment-manifest.json').read_text())
for f in m['files']:
 if f['path'] in ['assembly-render-pipeline.js','quality-study/viewer-revision.json','quality-study/viewer-revision.js']:
  b=(root/f['path']).read_bytes();f.update(sizeBytes=len(b),sha256=sha(b))
(root/'deployment-manifest.json').write_text(json.dumps(m,indent=2)+'\n')
with open(os.environ['GITHUB_ENV'],'a') as f:f.write('WATCH_EXPECTED_DIGEST='+r['digest']+'\n')
print('EXACT_TIMING_IDENTITY',variant,r['baselineDigest'],r['digest'])
