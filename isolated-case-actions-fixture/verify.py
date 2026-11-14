"""Pure read-only pin verification, no browser/server."""
from pathlib import Path
import json,hashlib,os
R=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def verify_package():
 f=json.loads((R/'FREEZE.json').read_text())
 for n,h in f['files'].items():assert sha(R/n)==h,n
 return True
if __name__=='__main__':
 verify_package()
 from server import inventory
 files=inventory()
 print(json.dumps({'package_verified':True,'closure_entries':len(files),'browser_runs':0}))
