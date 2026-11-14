from pathlib import Path
import hashlib,json,shutil,sys
Q=Path(__file__).resolve().parent; B=Q.parent/'watch-normal-stream-build/staging';RID='c9d2d1a59b4efacb6d4b44824baefd047dab96351b0086fa8bfe1032168c31bc';S=B/'preview-b/releases'/RID
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def validate():
 m=json.loads((S/'deployment-manifest.json').read_text());assert hashlib.sha256(json.dumps({k:m[k] for k in ['schemaVersion','localFiles','references']},separators=(',',':')).encode()).hexdigest()==RID
 rows=m['localFiles']+m['references'];assert len(rows)==298
 for f in rows:
  p=B/'preview-b/releases'/f.get('ownerReleaseId',RID)/f['path'];assert p.stat().st_size==f['sizeBytes'] and sha(p)==f['sha256']
 for p,h in json.loads((Q/'SOURCE_PINS.json').read_text()).items():assert sha(Q.parent/p)==h
 return rows
rows=validate();report={'originalClosure':len(rows),'originalRID':RID,'sourceUntouched':True,'overlay':{}}
for arm in ['baseline','candidate']:
 changes={'assembly-review.js':Q/'assembly-review.qa.js'}
 if arm=='candidate':changes['assembly-lazy-detail.js']=Q.parent/'watch-lazy-reentry/candidate.mjs'
 report['overlay'][arm]={n:{'sha256':sha(p),'sizeBytes':p.stat().st_size} for n,p in changes.items()}
 if '--materialize' in sys.argv:
  out=Q/('prepared-'+arm);assert not out.exists();shutil.copytree(B,out)
  for n,p in changes.items():shutil.copyfile(p,out/'preview-b/releases'/RID/n)
  for f in rows:
   p=out/'preview-b/releases'/f.get('ownerReleaseId',RID)/f['path'];override=report['overlay'][arm].get(f['path']) if f.get('ownerReleaseId',RID)==RID else None
   expected=override or f;assert sha(p)==expected['sha256'] and p.stat().st_size==expected['sizeBytes']
(Q/'QA_CLOSURE.json').write_text(json.dumps(report,indent=2)+'\n');print('Verified original 298-file closure and declared QA overlays; materialized:', '--materialize' in sys.argv)
