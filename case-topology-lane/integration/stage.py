import pathlib,json,shutil
R=pathlib.Path('case-topology-lane/integration');rid=(R/'release-id.txt').read_text();out=R/'release';dest=pathlib.Path('preview-b/releases')/rid;base=pathlib.Path('preview-b/releases/f0148dab28e427621143d47b157bc7802ebab4f661d2d530e2162c4508b4b485');m=json.loads((out/'deployment-manifest.json').read_text())
for n in [f['path']for f in m['localFiles']]+['deployment-manifest.json','release-receipt.json']:
 s=out/n if(out/n).exists()else base/n;d=dest/n;d.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(s,d)
for folder in ['crown-unified-qa','layer-focus-qa']:pathlib.Path(folder,'release-id.txt').write_text(rid)
for n in ['assembly-crown-hotspot.js','assembly-review.js']:shutil.copyfile(dest/n,pathlib.Path('crown-unified-qa')/n)
pathlib.Path('case-integrated-release.json').write_text(json.dumps({'releaseId':rid,'baseRelease':base.name,'mainNotPromoted':True},indent=2))
