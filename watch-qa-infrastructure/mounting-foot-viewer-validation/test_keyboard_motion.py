import asyncio,unittest
from keyboard_motion import pause_native_keyboard
class Page:
 def __init__(self,pressed='true',reachable=True,initial=None,changed=None):self.events=[];self.pressed=pressed;self.reachable=reachable;self.focus='';self.keyboard=self;self.initial=initial or {};self.changed=changed or {};self.probes=0
 async def evaluate(self,s):
  if 'getComputedStyle' in s:
   self.probes+=1;r={'tag':'BUTTON','disabled':False,'pressed':self.pressed,'inside':True,'hit':True,'visible':True,'focused':self.focus=='play-motion'};r.update(self.initial if self.probes==1 else self.changed);return r
  return{'id':self.focus,'tag':'BUTTON'}
 async def press(self,key):
  self.events.append(key)
  if key=='Tab'and self.reachable:self.focus='play-motion'
 async def wait_for_function(self,*a,**k):self.events.append('assert-both-paused')
async def op(n,a):return await a
class Keyboard(unittest.TestCase):
 def test_real_focus_then_native_space(self):
  p=Page();r=asyncio.run(pause_native_keyboard(p,op));self.assertEqual(p.events,['Tab','Space','assert-both-paused']);self.assertTrue(r['beforeSpace']['focused'])
 def test_paused_does_not_toggle(self):
  p=Page('false');asyncio.run(pause_native_keyboard(p,op));self.assertEqual(p.events,['assert-both-paused'])
 def test_tab_budget_fails_without_space(self):
  p=Page(reachable=False)
  with self.assertRaises(AssertionError):asyncio.run(pause_native_keyboard(p,op,2))
  self.assertEqual(p.events,['Tab','Tab'])
 def test_bad_budget_rejected(self):
  with self.assertRaises(ValueError):asyncio.run(pause_native_keyboard(Page(),op,100))
 def test_initial_bad_states(self):
  for invalid in [{'disabled':True},{'pressed':'unknown'},{'tag':'DIV'},{'visible':False},{'hit':False}]:
   p=Page(initial=invalid)
   with self.assertRaises(AssertionError):asyncio.run(pause_native_keyboard(p,op))
   self.assertEqual(p.events,[])
 def test_changed_states_never_space(self):
  for invalid in [{'focused':False},{'disabled':True},{'tag':'DIV'},{'visible':False},{'hit':False},{'inside':False},{'pressed':'unknown'}]:
   p=Page(changed=invalid)
   with self.assertRaises(AssertionError):asyncio.run(pause_native_keyboard(p,op))
   self.assertNotIn('Space',p.events)
 def test_became_paused_does_not_restart(self):
  p=Page(changed={'pressed':'false'});asyncio.run(pause_native_keyboard(p,op));self.assertEqual(p.events,['Tab','assert-both-paused'])
 def test_both_state_probes_use_bounded_op(self):
  calls=[]
  async def bounded(n,a):calls.append(n);return await a
  asyncio.run(pause_native_keyboard(Page(),bounded));self.assertIn('native-precondition',calls);self.assertIn('native-prespace',calls)
if __name__=='__main__':unittest.main()
