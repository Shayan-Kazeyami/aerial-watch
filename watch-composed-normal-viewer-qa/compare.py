from pathlib import Path
import json,sys
from normal_gates import stable
root=Path(sys.argv[1]);reports={}
for arm in ['baseline','candidate']:
 for kind in ['desktop','portrait']:
  files=list(root.rglob('evidence-'+arm+'-'+kind+'/REPORT.json'));assert len(files)==1,(arm,kind,files)
  r=json.loads(files[0].read_text());assert r['passed'] and r['normalClose'] and not r['errors'] and not r.get('failure') and not r.get('cleanupFailure');reports[arm,kind]=r
for kind in ['desktop','portrait']:
 a=reports['baseline',kind];b=reports['candidate',kind];assert a['browser']==b['browser'];assert stable(a['initial']['runtime'])==stable(b['initial']['runtime'])
 for label in ['front-after','lugs-after','rear-after']:
  get=lambda r:next(x['snapshot']['runtime'] for x in r['steps'] if x['name']==label)
  assert stable(get(a))==stable(get(b)),(kind,label,'stable state differs')
print('4 scoped composed functional/state arms passed. Manual original-image review required; not 15-task or release completion.')
