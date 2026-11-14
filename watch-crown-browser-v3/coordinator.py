"""Bounded cleanup of both owned groups; exact tested finite parameters."""
from cleanup import cleanup,CleanupUnverified
def cleanup_both(driver,server):
 reports={};failed=[]
 for name,p in [('driver',driver),('server',server)]:
  try:reports[name]=cleanup(p,grace=.5,post_grace=1.0)
  except Exception as e:
   reports[name]=getattr(e,'report',{'status':'unverified','error':repr(e)})
   failed.append(name)
 if failed:raise CleanupUnverified({'status':'unverified','failed':failed,'processes':reports})
 return reports
