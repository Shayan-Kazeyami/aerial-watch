import subprocess,os,sys,time,signal
from pathlib import Path
Q=Path(__file__).resolve().parent
subprocess.run([sys.executable,str(Q/'closure.py'),'--materialize'],check=True,timeout=180)
for arm in ['baseline','candidate']:
 env=dict(os.environ,QA_ARM=arm);server=subprocess.Popen([sys.executable,str(Q/'server.py')],env=env,start_new_session=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 try:
  time.sleep(1);assert server.poll() is None
  for mode in ['normal','fault']:
   p=subprocess.Popen([sys.executable,str(Q/'driver.py'),arm,mode],start_new_session=True)
   try:rc=p.wait(timeout=1080);assert rc==0
   finally:
    try:os.killpg(p.pid,signal.SIGKILL)
    except ProcessLookupError:pass
 finally:
  os.killpg(server.pid,signal.SIGTERM)
  try:server.wait(timeout=5)
  except subprocess.TimeoutExpired:os.killpg(server.pid,signal.SIGKILL);server.wait()
