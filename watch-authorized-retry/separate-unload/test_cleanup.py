import asyncio, unittest
from cleanup import normal_unload_then_close
class Page:
 def __init__(self,fail=False):self.fail=fail;self.calls=[]
 async def goto(self,*a,**kw):
  self.calls.append((a,kw))
  if self.fail:raise TimeoutError('unload timeout')
class Browser:
 def __init__(self,fail=False):self.fail=fail;self.calls=0
 async def close(self):
  self.calls+=1
  if self.fail:raise TimeoutError('close timeout')
async def traced(label,op,seconds):return await asyncio.wait_for(op(),seconds)
class Tests(unittest.IsolatedAsyncioTestCase):
 async def test_normal_unload_and_close_once(self):
  p=Page();b=Browser();r=await normal_unload_then_close(p,b,traced)
  self.assertTrue(r['normalUnloadCompleted']);self.assertEqual(b.calls,1);self.assertEqual(p.calls[0][0],('about:blank',))
 async def test_unload_failure_is_not_hidden_by_successful_close(self):
  p=Page(True);b=Browser();r=await normal_unload_then_close(p,b,traced)
  self.assertFalse(r['normalUnloadCompleted']);self.assertIn('unload timeout',r['unloadFailure']);self.assertIsNone(r['cleanupFailure']);self.assertEqual(b.calls,1)
 async def test_close_failure_is_separate(self):
  p=Page();b=Browser(True);r=await normal_unload_then_close(p,b,traced)
  self.assertTrue(r['normalUnloadCompleted']);self.assertIsNone(r['unloadFailure']);self.assertIn('close timeout',r['cleanupFailure'])
if __name__=='__main__':unittest.main()
