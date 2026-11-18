"""Run previously reviewed browser/diagnostic gates against the actual new sealed path."""
import pathlib,tempfile,subprocess,shutil,json,hashlib
ROOT=pathlib.Path(__file__).resolve().parent.parent;OUT=pathlib.Path(__file__).resolve().parent
rid=(OUT/'release-id.txt').read_text().strip();review=ROOT/'watch-batch-integration-review-v1'
with tempfile.TemporaryDirectory(prefix='watch-sealed-ci-',dir=ROOT) as tmp:
 d=pathlib.Path(tmp);browser=review/'browser_review.py';text=browser.read_text();assert 'watch-batch-review-local' in text
 (d/'browser_review.py').write_text(text.replace('watch-batch-review-local',rid))
 diagnostic=d/'diagnostic';shutil.copytree(review/'live-webgl-diagnostic',diagnostic)
 html=diagnostic/'diagnostic.html';html.write_text(html.read_text().replace('watch-batch-review-local',rid))
 results=[]
 for cmd in [['python',str(d/'browser_review.py')],['python',str(diagnostic/'run.py'),str(ROOT),str(ROOT/'watch-batch-live-evidence')]]:
  results.append(subprocess.run(cmd,cwd=ROOT).returncode)
 (OUT/'CI_BINDING.json').write_text(json.dumps({'releaseId':rid,'original_harness_sha256':hashlib.sha256(browser.read_bytes()).hexdigest(),'replacement':'Only local candidate directory string replaced with sealed release ID','return_codes':results,'deployed':False},indent=2))
 assert results==[0,0],results
