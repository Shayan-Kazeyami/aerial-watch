import asyncio, pathlib, tempfile, json, unittest
from heartbeat import bounded, observe

class Session:
    async def send(self,method):
        return {'product':'mock-browser'}
class Frame:
    async def evaluate(self,code):
        return 123 if 'requestAnimationFrame' in code else {'ready':'true'}
class PartialFrame(Frame):
    async def evaluate(self,code):
        if 'requestAnimationFrame' not in code: raise RuntimeError('mock DOM failure')
        return await super().evaluate(code)
class Tests(unittest.IsolatedAsyncioTestCase):
    async def test_timeout_is_not_success(self):
        async def stall(): await asyncio.sleep(60)
        result=await bounded('stall',stall,.01)
        self.assertFalse(result['ok']);self.assertIn('TimeoutError',result['error'])
    async def test_probe_failure_does_not_hide_other_probes(self):
        stop=asyncio.Event()
        with tempfile.TemporaryDirectory() as directory:
            sink=pathlib.Path(directory)/'heartbeat.jsonl'
            task=asyncio.create_task(observe(stop,PartialFrame(),Session(),sink,.01))
            await asyncio.sleep(.04);stop.set();await task
            rows=[json.loads(line) for line in sink.read_text().splitlines()]
            self.assertTrue(rows)
            self.assertEqual([p['probe'] for p in rows[0]['probes']],['browser-process','frame-dom','frame-two-raf'])
            self.assertEqual([p['ok'] for p in rows[0]['probes']],[True,False,True])
    async def test_derived_harness_preserves_failed_visual_gate(self):
        source=(pathlib.Path(__file__).parent/'ui-check-diagnostic.py').read_text()
        self.assertNotIn("R['passed']=True",source)
        self.assertIn("'Page.captureScreenshot'",source)
        self.assertIn("}),180)",source)
        self.assertNotIn("await host.screenshot",source)
        self.assertIn("['efficient','balanced','detail','studio','efficient']",source)
if __name__=='__main__': unittest.main()
