import asyncio,json,pathlib,tempfile,unittest,subprocess
from instrumentation import action,bounded_run,sample_processes,sample_loop
class Tests(unittest.IsolatedAsyncioTestCase):
 async def test_nested_timeout_is_not_outer_deadline(self):
  with tempfile.TemporaryDirectory()as d:
   p=pathlib.Path(d)/'log'
   async def fail():raise TimeoutError('nested capture timeout')
   with self.assertRaises(TimeoutError):await bounded_run(p,fail,60)
   events=[json.loads(x)['event']for x in p.read_text().splitlines()]
   self.assertIn('nested-operation-timeout',events);self.assertNotIn('run-timeout',events)
 async def test_no_initial_process_is_recorded_and_sampling_continues(self):
  calls=[]
  def fake(*a,**kw):
   calls.append(1);return subprocess.CompletedProcess(a,1 if len(calls)==1 else 0,'PID PPID %CPU RSS COMMAND\n' if len(calls)==1 else '42 1 5.0 1000 chrome\n','')
  stop=asyncio.Event()
  with tempfile.TemporaryDirectory()as d:
   p=pathlib.Path(d)/'log';task=asyncio.create_task(sample_loop(stop,p,.005,lambda:sample_processes(fake)))
   await asyncio.sleep(.05);stop.set();await task
   rows=[json.loads(x)for x in p.read_text().splitlines()];self.assertGreater(len(rows),1);self.assertTrue(rows[0]['noMatchingProcesses']);self.assertEqual(rows[1]['psReturnCode'],0)
 async def test_timeout_action_cancellation_is_not_success(self):
  with tempfile.TemporaryDirectory()as d:
   p=pathlib.Path(d)/'log'
   async def stall():await asyncio.sleep(60)
   with self.assertRaises(TimeoutError):await bounded_run(p,lambda:action(p,'native-reset',stall),.01)
   events=[json.loads(x)['event']for x in p.read_text().splitlines()];self.assertEqual(events,['run-start','action-start','action-cancelled','run-timeout','run-exit']);self.assertNotIn('action-completed',events)
 async def test_external_cancel_attributed_separately(self):
  with tempfile.TemporaryDirectory()as d:
   p=pathlib.Path(d)/'log'
   async def stall():await asyncio.sleep(60)
   t=asyncio.create_task(bounded_run(p,lambda:action(p,'capture-dispatch',stall),60));await asyncio.sleep(.005);t.cancel()
   with self.assertRaises(asyncio.CancelledError):await t
   events=[json.loads(x)['event']for x in p.read_text().splitlines()];self.assertIn('run-external-cancellation',events);self.assertNotIn('run-timeout',events)
 async def test_action_failure_propagates(self):
  with tempfile.TemporaryDirectory()as d:
   p=pathlib.Path(d)/'log'
   async def fail():raise ValueError('fake screenshot failure')
   with self.assertRaises(ValueError):await action(p,'screenshot',fail)
   self.assertEqual(json.loads(p.read_text().splitlines()[-1])['event'],'action-failed')
if __name__=='__main__':unittest.main()
