"""Bounded cleanup: permission failures are evidence, never proof of exit.
Only call for owned Popen children started with start_new_session=True.
"""
import os, signal, time

class CleanupUnverified(RuntimeError):
 def __init__(self, report):
  self.report=report
  super().__init__('Process cleanup unverified: '+repr(report))

def cleanup(p, grace=5):
 if p is None:return {'status':'not-started'}
 report={'pid':p.pid,'errors':[],'signals':[],'leader_reaped':False}
 def signal_group(sig):
  try:
   os.killpg(p.pid,sig)
   report['signals'].append(int(sig))
   return True
  except ProcessLookupError:return False
  except OSError as e:
   report['errors'].append({'operation':'killpg','signal':int(sig),'errno':e.errno,'error':str(e)})
   return None
 present=signal_group(signal.SIGTERM)
 deadline=time.monotonic()+grace
 while present is True and time.monotonic()<deadline:
  present=signal_group(0)
  if present is True:time.sleep(min(.05,max(0,deadline-time.monotonic())))
 # A denied probe does not mean absent. Still attempt bounded escalation.
 if present is not False:signal_group(signal.SIGKILL)
 try:
  report['returncode']=p.wait(timeout=5)
  report['leader_reaped']=True
 except Exception as e:
  report['errors'].append({'operation':'wait','error':repr(e)})
 report['status']='unverified' if report['errors'] else 'signals-completed-leader-reaped'
 if report['errors']:raise CleanupUnverified(report)
 return report

def cleanup_both(driver, server, clean=cleanup):
 reports={};errors=[]
 for name,p in [('driver',driver),('server',server)]:
  try:reports[name]=clean(p)
  except Exception as e:
   reports[name]=getattr(e,'report',{'status':'unverified','error':repr(e)})
   errors.append(name)
 if errors:raise CleanupUnverified({'status':'unverified','failed':errors,'processes':reports})
 return reports
