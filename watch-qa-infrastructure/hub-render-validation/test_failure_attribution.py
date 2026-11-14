import asyncio,importlib.util,sys,types,tempfile,json,unittest
from pathlib import Path
Q=Path(__file__).resolve().parent
class FakePage:
 def set_default_timeout(self,x):pass
 def on(self,*x):pass
 async def goto(self,*a,**k):raise ValueError('FAKE_PRIMARY_CAPTURE')
class FakeBrowser:
 version='fake'
 async def new_page(self,**k):return FakePage()
 async def close(self):raise RuntimeError('FAKE_CLEANUP')
class Manager:
 async def __aenter__(self):return types.SimpleNamespace(chromium=self)
 async def __aexit__(self,*a):pass
 async def launch(self,**k):return FakeBrowser()
class Attribution(unittest.TestCase):
 def test_both_failures_preserved(self):
  fake=types.ModuleType('playwright.async_api');fake.async_playwright=lambda:Manager();old=sys.modules.get('playwright.async_api');sys.modules['playwright.async_api']=fake
  try:
   spec=importlib.util.spec_from_file_location('fixture_run',Q/'run.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
   with tempfile.TemporaryDirectory()as d:
    m.Q=Path(d)
    with self.assertRaisesRegex(ValueError,'FAKE_PRIMARY_CAPTURE'):asyncio.run(m.main())
    r=json.loads((Path(d)/'evidence/REPORT.json').read_text());self.assertIn('FAKE_PRIMARY_CAPTURE',r['primaryFailure']);self.assertIn('FAKE_CLEANUP',r['cleanupFailure']);self.assertIn('FAKE_PRIMARY_CAPTURE',r['failure']);self.assertFalse(r['acceptance'])
  finally:
   if old is None:sys.modules.pop('playwright.async_api',None)
   else:sys.modules['playwright.async_api']=old
if __name__=='__main__':unittest.main()
