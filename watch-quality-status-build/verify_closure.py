from pathlib import Path
import json,hashlib
Q=Path('watch-quality-status-build');RID='ea85a4e6e44dbbfe4337f1dd8fa376793db7e9ce90628fe1d50b2edef9482de6';assert(Q/'release-id.txt').read_text().strip()==RID;S=Q/'staging/preview-b/releases'/RID;m=json.load(open(S/'deployment-manifest.json'));can={k:m[k]for k in ['schemaVersion','localFiles','references']};assert hashlib.sha256(json.dumps(can,separators=(',',':')).encode()).hexdigest()==RID
for f in m['localFiles']+m['references']:
 p=Q/'staging/preview-b/releases'/f['ownerReleaseId']/f['path']if'ownerReleaseId'in f else S/f['path'];b=p.read_bytes();assert len(b)==f['sizeBytes']and hashlib.sha256(b).hexdigest()==f['sha256']
old=Path('coordinated-release-successor/assembly-review-reset-candidate.js').read_bytes();new=(S/'assembly-review.js').read_bytes();assert hashlib.sha256(old).hexdigest()=='f890d65acb36f7bd3da53e3c5e5ed78b62a803bece14f196041696efec359a22';assert old.count('Â· measuring playbackâ€¦'.encode())==1;assert old.replace('Â· measuring playbackâ€¦'.encode(),'· measuring playback…'.encode())==new
r={'passed':True,'release':RID,'closureFiles':len(m['localFiles'])+len(m['references']),'literalOnlyVersusPinnedAuthoringSource':True,'browserVisualDeploymentApproval':False};(Q/'closure-verification.json').write_text(json.dumps(r,indent=2));print(r)
