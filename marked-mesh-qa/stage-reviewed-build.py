import pathlib,json,subprocess
r=json.loads(pathlib.Path('marked-output/report.json').read_text());assert r['passed'] is True
b=json.loads(pathlib.Path('marked-mesh-qa/build.json').read_text());d=pathlib.Path('preview-b/releases')/b['releaseId'];m=json.loads((d/'deployment-manifest.json').read_text());paths=[str(d/f['path'])for f in m['localFiles']]+[str(d/'deployment-manifest.json'),str(d/'release-receipt.json')]
for i in range(0,len(paths),50):subprocess.run(['git','add','--',*paths[i:i+50]],check=True)
subprocess.run(['git','-c','user.name=Aerial Watch QA','-c','user.email=actions@users.noreply.github.com','commit','-m','Stage verified marked mesh candidate '+b['releaseId']],check=True)
# New branch only; production pointer is deliberately untouched for visual review.
branch='qa/marked-mesh-build-'+b['releaseId'][:12]
subprocess.run(['git','push','origin','HEAD:refs/heads/'+branch],check=True)
pathlib.Path('marked-output/staged.json').write_text(json.dumps({'branch':branch,'commit':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),'releaseId':b['releaseId']}))
