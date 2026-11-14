import subprocess,sys,os,urllib.request,time,json,hashlib
from pathlib import Path
from coordinator import cleanup_both
Q=Path(__file__).resolve().parent;arm=sys.argv[1];assert arm in ['baseline','candidate'];server=driver=None
for name,h in json.loads((Q/'FREEZE.json').read_text()).items():assert hashlib.sha256((Q/name).read_bytes()).hexdigest()==h,name
with (Q/(arm+'-server.log')).open('w') as sl,(Q/(arm+'-driver.log')).open('w') as dl:
 try:
  server=subprocess.Popen([sys.executable,str(Q/'server.py')],env=dict(os.environ,QA_ARM=arm),start_new_session=True,stdout=sl,stderr=subprocess.STDOUT)
  for _ in range(40):
   assert server.poll() is None
   try:urllib.request.urlopen('http://127.0.0.1:8873/',timeout=1);break
   except OSError:time.sleep(.25)
  else:raise RuntimeError('server unavailable')
  driver=subprocess.Popen([sys.executable,str(Q/'driver.py'),arm],start_new_session=True,stdout=dl,stderr=subprocess.STDOUT);assert driver.wait(timeout=1170)==0
 finally:
  try:
   cleanup_report=cleanup_both(driver,server)
  except Exception as e:
   (Q/(arm+'-cleanup.json')).write_text(json.dumps(getattr(e,'report',{'status':'unverified','error':repr(e)}),indent=2)+'\n')
   raise
  else:
   (Q/(arm+'-cleanup.json')).write_text(json.dumps(cleanup_report,indent=2)+'\n')
