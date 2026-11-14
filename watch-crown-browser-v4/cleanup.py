"""Isolated proposal: reap owned leader before group probes. EPERM always fails closed."""
import os,signal,time
class CleanupUnverified(RuntimeError):
 def __init__(self,report):self.report=report;super().__init__(repr(report))
def cleanup(p,grace=1,post_grace=1):
 if p is None:return {'status':'not-started'}
 r={'pid':p.pid,'errors':[],'signals':[],'leader_reaped':False,'group_absent':False}
 def poll():
  try:
   rc=p.poll()
   if rc is not None:r.update(leader_reaped=True,returncode=rc)
  except Exception as e:r['errors'].append({'operation':'poll','error':repr(e)})
 def send(sig):
  try:os.killpg(p.pid,sig);r['signals'].append(int(sig));return True
  except ProcessLookupError:return False
  except OSError as e:r['errors'].append({'operation':'killpg','signal':int(sig),'errno':e.errno,'error':str(e)});return None
 poll();present=send(signal.SIGTERM);deadline=time.monotonic()+grace
 while present is True and time.monotonic()<deadline:
  poll();present=send(0)
  if present is True:time.sleep(.02)
 if present is not False:send(signal.SIGKILL)
 try:r['returncode']=p.wait(timeout=5);r['leader_reaped']=True
 except Exception as e:r['errors'].append({'operation':'wait','error':repr(e)})
 deadline=time.monotonic()+post_grace
 while True:
  poll();present=send(0)
  if present is False:r['group_absent']=True;break
  if present is None or time.monotonic()>=deadline:break
  time.sleep(.02)
 r['status']='verified' if r['leader_reaped'] and r['group_absent'] and not r['errors'] else 'unverified'
 if r['status']=='unverified':raise CleanupUnverified(r)
 return r
