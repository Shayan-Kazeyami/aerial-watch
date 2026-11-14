"""Cleanup-only diagnostic for disposable runner. No browser/network/source mutation."""
import subprocess,sys,os,time,json,signal,platform,traceback
from pathlib import Path
from cleanup import cleanup,CleanupUnverified
Q=Path(__file__).resolve().parent
rows=[]
def probe(pid,operation):
 try:os.killpg(pid,0);return {'operation':operation,'state':'present'}
 except ProcessLookupError:return {'operation':operation,'state':'absent'}
 except OSError as e:return {'operation':operation,'state':'unverified','errno':e.errno,'error':str(e)}
# Children self-exit after20s even if cleanup signaling is denied.
marker=Q/'resistant-ready.json'
if marker.exists():raise RuntimeError('Fresh diagnostic workspace required')
child="import signal,time,os,pathlib; signal.signal(signal.SIGTERM,signal.SIG_IGN); pathlib.Path(%r).write_text(str(os.getpid())); time.sleep(20)"%str(marker)
cases={
 'ordinary_leader':'import time;time.sleep(20)',
 'exited_leader_resistant_descendant':"import subprocess,sys; subprocess.Popen([sys.executable,'-c',%r]);"%child
}
for name,code in cases.items():
 r={'case':name,'started':False};p=None;start=time.monotonic()
 try:
  p=subprocess.Popen([sys.executable,'-c',code],start_new_session=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);r.update(started=True,pid=p.pid)
  if name.startswith('exited'):
   p.wait(timeout=5)
   deadline=time.monotonic()+5
   while not marker.exists() and time.monotonic()<deadline:time.sleep(.02)
   if not marker.exists():raise RuntimeError('No resistant child readiness')
   r['resistant_child_pid']=int(marker.read_text())
  else:time.sleep(.15)
  r['before']=probe(p.pid,'before_cleanup')
  try:r['cleanup']=cleanup(p,grace=.5)
  except CleanupUnverified as e:r['cleanup']=e.report
  r['after']=probe(p.pid,'after_cleanup')
 except Exception as e:r['exception']=repr(e)
 finally:
  if p is not None:
   # Best effort final escalation is recorded, never suppress permission failures.
   try:os.killpg(p.pid,signal.SIGKILL);r['final_kill']='sent'
   except ProcessLookupError:r['final_kill']='absent'
   except OSError as e:r['final_kill']={'errno':e.errno,'error':str(e)}
   try:r['final_returncode']=p.wait(timeout=5)
   except Exception as e:r['final_wait_error']=repr(e)
  r['elapsed_seconds']=time.monotonic()-start;rows.append(r)
  (Q/'RESULT.json').write_text(json.dumps({'platform':platform.platform(),'python':sys.version,'pid':os.getpid(),'cases':rows,'scope':'diagnostic only; no viewer/native/production changes; any EPERM remains unverified'},indent=2)+'\n')
# Fail closed: exact complete case set, successful initial probe and cleanup evidence.
from gate import accepted
sys.exit(0 if accepted(rows) else 1)
