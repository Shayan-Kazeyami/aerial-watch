import os,signal,time

def cleanup(p,grace=5):
 if p is None:return
 try:
  os.killpg(p.pid,signal.SIGTERM)
 except ProcessLookupError:
  p.wait(timeout=5)
  return
 deadline=time.monotonic()+grace
 while time.monotonic()<deadline:
  try:os.killpg(p.pid,0)
  except ProcessLookupError:break
  time.sleep(min(.05,max(0,deadline-time.monotonic())))
 try:os.killpg(p.pid,signal.SIGKILL)
 except ProcessLookupError:pass
 p.wait(timeout=5)

def cleanup_both(driver,server,clean=cleanup):
 try:clean(driver)
 finally:clean(server)
