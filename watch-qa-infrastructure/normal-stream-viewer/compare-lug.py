from pathlib import Path
import json,sys
from gates import stable,assert_snapshot
root=Path(sys.argv[1]);rs={}
for arm in ['baseline','candidate']:
 files=list(root.rglob('evidence-lug-'+arm+'/REPORT.json'));assert len(files)==1,(arm,files)
 r=json.loads(files[0].read_text());assert r['passed'] and r['normalClose'] and not r.get('failure') and not r.get('cleanupFailure');assert_snapshot(r['after']);rs[arm]=r
assert rs['baseline']['browser']==rs['candidate']['browser']
assert stable(rs['baseline']['after'])==stable(rs['candidate']['after']),'stable rendering state differs: retain raw results; visual comparison HOLD'
print('Both actual viewer arms passed functional/state gates. MANUAL LEATHER VISUAL REVIEW STILL REQUIRED; not release acceptance.')
