"""Use actual published legacy shell controls, never force or hidden bypass."""
async def pause_visible_motion(page,op):
 button=page.locator('#play-motion')
 await op('legacy-motion-visible',button.wait_for(state='visible',timeout=25000))
 await op('legacy-motion-enabled',page.wait_for_function("()=>!document.getElementById('play-motion').disabled",timeout=25000))
 pressed=await button.get_attribute('aria-pressed')
 if pressed not in ['true','false']:raise AssertionError('unknown motion state')
 if pressed=='true':await op('legacy-pause',button.click(timeout=25000))
 await op('legacy-motion-confirmed',page.wait_for_function("()=>{const s=assemblyInspect();return !s.animation&&!s.interiorAnimation&&document.getElementById('play-motion').getAttribute('aria-pressed')==='false'}",timeout=25000))
async def set_visible_finish(page,op,finished):
 toggle=page.locator('#finish')
 await op('legacy-finish-visible',toggle.wait_for(state='visible',timeout=25000))
 await op('legacy-finish',toggle.set_checked(finished,timeout=25000))
 await op('legacy-finish-confirmed',page.wait_for_function('(expected)=>assemblyInspect().finish===expected',arg=finished,timeout=25000))
