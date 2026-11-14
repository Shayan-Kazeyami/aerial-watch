"""Use ONLY visible existing atelier controls. No force, eval mutation or bridge events."""
async def pause_visible_motion(page,op):
 button=page.locator('#motion')
 await op('motion-visible',button.wait_for(state='visible',timeout=30000))
 pressed=await button.get_attribute('aria-pressed')
 if pressed not in ['true','false']:raise AssertionError('unknown motion state')
 if pressed=='true':await op('pause-visible-motion',button.click(timeout=30000))
 await op('motion-state-confirmed',page.wait_for_function("()=>{const s=assemblyInspect();return !s.animation&&!s.interiorAnimation&&document.getElementById('motion').getAttribute('aria-pressed')==='false'}",timeout=30000))
async def set_visible_finish(page,op,finished):
 await op('open-studio-tools',page.locator('.atelier-more[data-mode="settings"]').click(timeout=30000))
 await op('open-engineering',page.locator('#atelier-tools [data-mode="engineering"]').click(timeout=30000))
 toggle=page.locator('#atelier-tools input[data-check="finish"]')
 await op('visible-finish-toggle',toggle.set_checked(finished,timeout=30000))
 await op('finish-state-confirmed',page.wait_for_function('(expected)=>assemblyInspect().finish===expected',arg=finished,timeout=30000))
 await op('close-context',page.locator('#close').click(timeout=30000))
 await op('context-closed',page.locator('#context').wait_for(state='hidden',timeout=30000))
