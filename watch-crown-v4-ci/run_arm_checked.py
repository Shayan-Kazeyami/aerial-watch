import subprocess,sys,os,urllib.request,time,json,hashlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent/'watch-crown-browser-v4'))
from coordinator import cleanup_both
Q=Path(__file__).resolve().parent.parent/'watch-crown-browser-v4';arm=sys.argv[1];assert arm in ['baseline','candidate'];server=driver=None
for name,h in json.loads((Q/'FREEZE.json').read_text()).items():assert hashlib.sha256((Q/name).read_bytes()).hexdigest()==h,name
with (Q/(arm+'-server.log')).open('w') as sl,(Q/(arm+'-driver.log')).open('w') as dl:
 try:
  server=subprocess.Popen([sys.executable,str(Q/'server.py')],env=dict(os.environ,QA_ARM=arm),start_new_session=True,stdout=sl,stderr=subprocess.STDOUT)
  for _ in range(40):
   assert server.poll() is None
   try:urllib.request.urlopen('http://127.0.0.1:8873/',timeout=1);break
   except OSError:time.sleep(.25)
  else:raise RuntimeError('server unavailable')
  driver=subprocess.Popen([sys.executable,str(Q/'driver.py'),arm],start_new_session=True,stdout=dl,stderr=subprocess.STDOUT);driver_exit=driver.wait(timeout=1170);(Q/(arm+'-driver-exit.json')).write_text(json.dumps({'returncode':driver_exit})+'\n');assert driver_exit==0
 finally:
  try:
   cleanup_report=cleanup_both(driver,server)
  except Exception as e:
   (Q/(arm+'-cleanup.json')).write_text(json.dumps(getattr(e,'report',{'status':'unverified','error':repr(e)}),indent=2)+'\n')
   raise
  else:
   (Q/(arm+'-cleanup.json')).write_text(json.dumps(cleanup_report,indent=2)+'\n')

# Reached only after driver exit0 AND both cleanup paths returned without exception.
result=json.loads((Q/('RESULT-'+arm+'.json')).read_text())
assert result['passed'] is True and result['arm']==arm and not result['errors']
for name in ('driver','server'):
 c=cleanup_report[name];assert c['status']=='verified' and c['leader_reaped'] is True and c['group_absent'] is True and c['errors']==[]
(Q/(arm+'-ACCEPTANCE.json')).write_text(json.dumps({'arm':arm,'driver_exit':driver_exit,'functional_assertions':True,'cleanup_verified':True,'scope':'crown keyboard QA only, not release approval'},indent=2)+'\n')
