import subprocess,os,sys,time,signal,urllib.request,json,hashlib
from pathlib import Path
Q=Path(__file__).resolve().parent;V=Q.parent/'watch-lazy-viewer-v2';arm,mode=sys.argv[1:]
assert arm in ('baseline','candidate') and mode in ('normal','fault')
for p,h in json.loads((V/'FREEZE.json').read_text()).items(): assert hashlib.sha256((V/p).read_bytes()).hexdigest()==h
subprocess.run([sys.executable,str(V/'closure.py'),'--materialize'],check=True,timeout=180)
from cleanup import cleanup_both
server=driver=None
with (Q/'server.log').open('w') as log:
 try:
  server=subprocess.Popen([sys.executable,str(V/'server.py')],env=dict(os.environ,QA_ARM=arm),start_new_session=True,stdout=log,stderr=subprocess.STDOUT)
  for _ in range(40):
   assert server.poll() is None
   try:urllib.request.urlopen('http://127.0.0.1:8765/',timeout=1);break
   except OSError:time.sleep(.25)
  else:raise RuntimeError('server not ready')
  with (Q/'driver.log').open('w') as dl:
   driver=subprocess.Popen([sys.executable,str(V/'driver.py'),arm,mode],start_new_session=True,stdout=dl,stderr=subprocess.STDOUT)
   assert driver.wait(timeout=1080)==0
 finally:cleanup_both(driver,server)
