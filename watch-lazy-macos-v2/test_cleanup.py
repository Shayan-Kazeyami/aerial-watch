import unittest,subprocess,tempfile,time,os,signal,sys
from pathlib import Path
from cleanup import cleanup,cleanup_both
class CleanupTests(unittest.TestCase):
 def test_server_cleanup_even_if_driver_raises(self):
  called=[]
  def fail(p):
   called.append(p)
   if p=='driver':raise RuntimeError('injected')
  with self.assertRaises(RuntimeError):cleanup_both('driver','server',fail)
  self.assertEqual(called,['driver','server'])
 def test_exited_leader_term_resistant_child(self):
  with tempfile.TemporaryDirectory() as d:
   marker=Path(d)/'pid'
   child="import signal,time,os,pathlib;signal.signal(signal.SIGTERM,signal.SIG_IGN);pathlib.Path(%r).write_text(str(os.getpid()));time.sleep(60)"%str(marker)
   leader="import subprocess,sys;subprocess.Popen([sys.executable,'-c',%r])"%child
   p=subprocess.Popen([sys.executable,'-c',leader],start_new_session=True)
   try:
    p.wait(timeout=5)
    for _ in range(100):
     if marker.exists():break
     time.sleep(.01)
    self.assertTrue(marker.exists());pid=int(marker.read_text());start=time.monotonic();cleanup(p,grace=.1);self.assertLess(time.monotonic()-start,2)
    # Linux /proc may retain a killed orphan as zombie until reaped.
    for _ in range(100):
     stat=Path('/proc')/str(pid)/'stat'
     if not stat.exists() or stat.read_text().split()[2]=='Z':break
     time.sleep(.01)
    else:self.fail('descendant still live')
   finally:
    try:os.killpg(p.pid,signal.SIGKILL)
    except ProcessLookupError:pass
 def test_live_leader_terminated(self):
  p=subprocess.Popen([sys.executable,'-c','import time;time.sleep(60)'],start_new_session=True)
  cleanup(p,grace=.1);self.assertIsNotNone(p.returncode)
 def test_none(self):cleanup(None)
if __name__=='__main__':unittest.main()
