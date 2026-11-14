"""Unexecuted POSIX external process-group watchdog. Explicit CLI only."""
import os,signal,subprocess,sys,time,json
from pathlib import Path
R=Path(__file__).resolve().parent
LIMIT=1350

def stop(p):
 if p is None:return
 try:os.killpg(p.pid,signal.SIGTERM)
 except ProcessLookupError:return
 # The leader may already be dead while browser descendants remain alive.
 deadline=time.monotonic()+5
 while time.monotonic()<deadline:
  try:os.killpg(p.pid,0)
  except ProcessLookupError:break
  time.sleep(.1)
 try:os.killpg(p.pid,signal.SIGKILL)
 except ProcessLookupError:pass
 try:p.wait(timeout=5)
 except subprocess.TimeoutExpired:raise RuntimeError('Process leader did not reap')
def main():
 if os.name!='posix':raise RuntimeError('POSIX process groups required')
 evidence=R/'watchdog-results';evidence.mkdir(exist_ok=False)
 server=worker=None;report={'status':'STARTING','limit_seconds':LIMIT,'scope':'BOOTSTRAP_ONLY_NOT_LIFECYCLE_OR_MEMORY','cleanup_errors':[]};start=time.monotonic()
 try:
  with (evidence/'server.log').open('wb')as sl,(evidence/'worker.log').open('wb')as wl:
   server=subprocess.Popen([sys.executable,str(R/'server.py')],cwd=R,stdout=sl,stderr=subprocess.STDOUT,start_new_session=True)
   # No probe requests/browser run during preparation. Actual run gets a bounded startup delay.
   time.sleep(1)
   if server.poll()is not None:raise RuntimeError('Fixture server failed startup')
   worker=subprocess.Popen([sys.executable,str(R/'browser_harness.py')],cwd=R,stdout=wl,stderr=subprocess.STDOUT,start_new_session=True)
   while worker.poll()is None:
    if server.poll()is not None:raise RuntimeError('Fixture server exited unexpectedly')
    if time.monotonic()-start>LIMIT:raise TimeoutError('External wall-clock watchdog expired')
    time.sleep(.25)
   report['worker_exit_code']=worker.returncode
   if worker.returncode:raise RuntimeError('Harness process failed')
   result=json.loads((R/'browser-results/REPORT.json').read_text())
   report['harness_status']=result['status']
   report['status']='BOOTSTRAP_ONLY_COMPLETED'if result['status']=='BOOTSTRAP_ONLY_COMPLETED_NOT_LIFECYCLE_PASS'else'HOLD_HARNESS_RESULT'
 except BaseException as e:report['status']='STOPPED';report['failure']=repr(e)
 finally:
  for p,n in ((worker,'worker'),(server,'server')):
   try:stop(p)
   except BaseException as e:report['cleanup_errors'].append({'owner':n,'error':repr(e)})
  if report['cleanup_errors']:report['status']='HOLD_PROCESS_CLEANUP'
  report['elapsed_seconds']=time.monotonic()-start
  (evidence/'REPORT.json').write_text(json.dumps(report,indent=2)+'\n')
 return 0 if report['status']=='BOOTSTRAP_ONLY_COMPLETED' and not report['cleanup_errors'] else 1
if __name__=='__main__':raise SystemExit(main())
