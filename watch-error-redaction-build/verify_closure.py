from pathlib import Path
import json,hashlib
Q=Path('watch-error-redaction-build');RID='3448182496cf6c2b906abe4b5a7128a9537ab745e8f992d4d55783fd389879e6';assert(Q/'release-id.txt').read_text().strip()==RID;S=Q/'staging/preview-b/releases'/RID;m=json.load(open(S/'deployment-manifest.json'));can={k:m[k]for k in ['schemaVersion','localFiles','references']};assert hashlib.sha256(json.dumps(can,separators=(',',':')).encode()).hexdigest()==RID
for f in m['localFiles']+m['references']:
 p=Q/'staging/preview-b/releases'/f['ownerReleaseId']/f['path']if'ownerReleaseId'in f else S/f['path'];b=p.read_bytes();assert len(b)==f['sizeBytes']and hashlib.sha256(b).hexdigest()==f['sha256']
old=Path('coordinated-release-successor/assembly-review-reset-candidate.js').read_bytes();new=(S/'assembly-review.js').read_bytes();assert hashlib.sha256(old).hexdigest()=='f890d65acb36f7bd3da53e3c5e5ed78b62a803bece14f196041696efec359a22';assert old.count('Â· measuring playbackâ€¦'.encode())==1;assert old.replace('Â· measuring playbackâ€¦'.encode(),'· measuring playback…'.encode())==new
assert hashlib.sha256((S/'atelier-error-details.js').read_bytes()).hexdigest()=='e28bdd29a032d5dad5d2a501b08c02536a386b22abb04fc7bc2796b9a843de58'
assert hashlib.sha256((Q/'source-fixture.mjs').read_bytes()).hexdigest()=='d3625d722ca27ff54d5b5254f8671342764aa26b50ecb57d2592c17ab6a675a7'
r={'passed':True,'release':RID,'closureFiles':len(m['localFiles'])+len(m['references']),'literalOnlyVersusPinnedAuthoringSource':True,'browserVisualDeploymentApproval':False};(Q/'closure-verification.json').write_text(json.dumps(r,indent=2));print(r)
