from pathlib import Path
import shutil,hashlib,json
repo=Path(__file__).resolve().parent.parent
base=repo/'preview-b/releases/e79b22365b4874327d308eca789326fbea0da8d717ffca20da80b611e36b39c6'
candidate=Path(__file__).parent/'assembly-mechanism-batch.js'
stage=repo/'preview-b/releases/watch-batch-review-local'
if stage.exists(): raise SystemExit('Refusing to overwrite staging directory')
shutil.copytree(base,stage)
shutil.copy2(candidate,stage/'assembly-mechanism-batch.js')
differences=[]
for p in base.rglob('*'):
 if p.is_file() and p.read_bytes()!=(stage/p.relative_to(base)).read_bytes(): differences.append(str(p.relative_to(base)))
assert differences==['assembly-mechanism-batch.js'],differences
report={'base':str(base.relative_to(repo)),'stage':str(stage.relative_to(repo)),'changed_files':differences,'candidate_sha256':hashlib.sha256(candidate.read_bytes()).hexdigest(),'public_loader_changed':False,'sealed_release_changed':False,'browser_gpu_verified':False}
(Path(__file__).parent/'STAGING.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report))
