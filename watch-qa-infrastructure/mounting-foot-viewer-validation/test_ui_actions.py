import asyncio,unittest
from ui_actions import pause_visible_motion,set_visible_finish
class Locator:
 def __init__(self,page,selector):self.p=page;self.s=selector
 async def wait_for(self,**kw):self.p.events.append((self.s,'wait',kw))
 async def get_attribute(self,name):return self.p.pressed
 async def click(self,**kw):self.p.events.append((self.s,'click',kw))
 async def set_checked(self,value,**kw):self.p.events.append((self.s,'check',value,kw))
class Page:
 def __init__(self,pressed):self.pressed=pressed;self.events=[]
 def locator(self,s):return Locator(self,s)
 async def wait_for_function(self,*a,**kw):self.events.append(('state-read',a,kw))
async def op(name,value):return await value
class VisibleUI(unittest.TestCase):
 def test_running_pauses_via_visible_button(self):
  p=Page('true');asyncio.run(pause_visible_motion(p,op));self.assertEqual([x[0]for x in p.events if x[1]=='click'],['#motion'])
 def test_already_paused_never_toggles_on(self):
  p=Page('false');asyncio.run(pause_visible_motion(p,op));self.assertFalse(any(x[1]=='click'for x in p.events))
 def test_unknown_state_fails_closed(self):
  with self.assertRaises(AssertionError):asyncio.run(pause_visible_motion(Page(None),op))
 def test_finish_visible_route(self):
  p=Page('false');asyncio.run(set_visible_finish(p,op,False));self.assertEqual([x[0]for x in p.events if x[1]=='click'],['.atelier-more[data-mode="settings"]','#atelier-tools [data-mode="engineering"]','#close']);self.assertEqual([x[0]for x in p.events if x[1]=='check'],['#atelier-tools input[data-check="finish"]']);self.assertNotIn('force',repr(p.events));self.assertNotIn('dispatch',repr(p.events))
if __name__=='__main__':unittest.main()
