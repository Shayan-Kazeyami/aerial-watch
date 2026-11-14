"""Unexecuted bounded native-keyboard alternative; no force or synthetic JS click."""
BUTTON_STATE="""()=>{const b=document.getElementById('play-motion');if(!b)return null;const r=b.getBoundingClientRect(),s=getComputedStyle(b),top=document.elementFromPoint(r.x+r.width/2,r.y+r.height/2);let inert=false;for(let n=b;n;n=n.parentElement)if(n.inert||n.hidden)inert=true;return{tag:b.tagName,disabled:b.disabled,pressed:b.getAttribute('aria-pressed'),inside:r.width>0&&r.height>0&&r.x>=0&&r.y>=0&&r.right<=innerWidth&&r.bottom<=innerHeight,hit:!!top&&b.contains(top),visible:s.visibility==='visible'&&s.display!=='none'&&!inert,focused:document.activeElement===b}}"""
def validate(state,focused=False):
 if not state or state['tag']!='BUTTON'or state['disabled']or not state['inside']or not state['hit']or not state['visible']:raise AssertionError('visible enabled unoccluded native button required')
 if focused and not state['focused']:raise AssertionError('same actual motion button must retain focus')
 if state['pressed']not in ['true','false']:raise AssertionError('unknown motion state')
async def pause_native_keyboard(page,op,maximum_tabs=32):
 if not 1<=maximum_tabs<=40:raise ValueError('bounded tab sweep required')
 state=await op('native-precondition',page.evaluate(BUTTON_STATE));validate(state);focus=[];before_space=None
 if state['pressed']=='true':
  for step in range(maximum_tabs+1):
   current=await op('keyboard-focus-read',page.evaluate("()=>({id:document.activeElement?.id,tag:document.activeElement?.tagName})"));focus.append(current)
   if current['id']=='play-motion':break
   if step==maximum_tabs:raise AssertionError('native motion button not reached within tab budget')
   await op('native-tab',page.keyboard.press('Tab'))
  before_space=await op('native-prespace',page.evaluate(BUTTON_STATE));validate(before_space,focused=True)
  if before_space['pressed']=='true':await op('native-pause-space',page.keyboard.press('Space'))
 await op('native-motion-confirmed',page.wait_for_function("()=>{const s=assemblyInspect();return !s.animation&&!s.interiorAnimation&&document.getElementById('play-motion').getAttribute('aria-pressed')==='false'}",timeout=25000))
 return{'route':'native Tab then Space','focusSequence':focus,'precondition':state,'beforeSpace':before_space}
