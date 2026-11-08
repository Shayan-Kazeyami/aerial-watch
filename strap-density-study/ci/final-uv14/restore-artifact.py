"""Normalize packaging paths from successful immutable generation, not geometry."""
import pathlib,json,tarfile,shutil
D=pathlib.Path('reused');R=json.loads((D/'strap-output/sealed-release.json').read_text());rid=pathlib.Path(R['releasePath']).name;target=pathlib.Path('preview-b/releases')/rid
with tarfile.open(D/'strap-output/sealed-release.tar.gz')as tf:
 for m in tf.getmembers():
  if m.isdir():continue
  assert m.isfile(),m.name
  marker='preview-b/releases/'+rid+'/'
  assert marker in m.name,m.name
  rel=pathlib.PurePosixPath(m.name.split(marker,1)[1]);assert not rel.is_absolute()and '..'not in rel.parts
  p=target/str(rel);p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(tf.extractfile(m).read())
R['releasePath']=str(target);O=pathlib.Path('strap-output');O.mkdir(exist_ok=True);(O/'sealed-release.json').write_text(json.dumps(R,indent=2));shutil.copyfile(D/'strap-output/regeneration-steps.json',O/'regeneration-steps.json')
S=D/'strap-density-study/ci-final-candidate';T=pathlib.Path('strap-density-study/ci-final-candidate');shutil.copytree(S,T,dirs_exist_ok=True)
print('Reused unchanged generated release',target)
