import asyncio,json,traceback
from pathlib import Path
from playwright.async_api import async_playwright
P=Path('qa-component-search');O=P/'evidence';O.mkdir(exist_ok=True);R={'complete':False,'errors':[]}
async def main():
 async with async_playwright() as pw:
  b=await pw.chromium.launch(headless=True,args=['--no-sandbox','--disable-dev-shm-usage','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
  page=await b.new_page(viewport={'width':1000,'height':800});page.on('pageerror',lambda e:R['errors'].append(str(e)))
  try:
   await page.goto('http://127.0.0.1:8875/qa-component-search/runtime/atelier-preview.html?quality=efficient&assets=meshopt&face=svg04&leather=craft14&paused=1',wait_until='domcontentloaded')
   await page.wait_for_function('window.assemblyInspect&&!assemblyInspect().loading&&!assemblyInspect().failed',timeout=300000)
   await page.locator('.atelier-more').click();await page.locator('#context [data-mode="components"]').click();await page.locator('#atelier-search').fill('zzzz-no-such-part-74219')
   await page.wait_for_function('document.getElementById("atelier-count").textContent.startsWith("0 of ")')
   R['zeroMatches']=await page.evaluate("""()=>{const a=document.getElementById('atelier-count'),s=document.getElementById('search-count');const ancestors=[];for(let p=a;p;p=p.parentElement)ancestors.push({tag:p.tagName,id:p.id,role:p.getAttribute('role'),live:p.getAttribute('aria-live'),hidden:p.hidden,inert:p.inert});return {visibleText:a.textContent,visibleRole:a.getAttribute('role'),visibleLive:a.getAttribute('aria-live'),visible:a.checkVisibility(),originalText:s.textContent,originalRole:s.getAttribute('role'),originalVisible:s.checkVisibility(),originalHiddenAncestor:s.closest('[hidden]')?.id,originalInertAncestor:s.closest('[inert]')?.id,activeElement:document.activeElement?.id,ancestors,mainStatus:document.getElementById('status').textContent};}""")
   cdp=await page.context.new_cdp_session(page);ax=await cdp.send('Accessibility.getFullAXTree');R['matchingAXNodes']=[n for n in ax['nodes'] if '0 of ' in n.get('name',{}).get('value','')]
   assert R['zeroMatches']['visible'];assert R['zeroMatches']['originalRole']=='status';assert not R['zeroMatches']['originalVisible'];assert R['zeroMatches']['originalInertAncestor']=='runtime-bridge'
   R['resultLiveSemanticsMissing']=not any(x['live'] in ['polite','assertive'] or x['role'] in ['status','alert'] for x in R['zeroMatches']['ancestors'])
   assert R['resultLiveSemanticsMissing'],'Candidate issue not reproduced'
   assert R['zeroMatches']['activeElement']=='atelier-search'
   await page.screenshot(path=str(O/'zero-matches-visible.png'))
   await page.locator('#atelier-search').fill('');await page.wait_for_function('!document.getElementById("atelier-count").textContent.startsWith("0 of ")')
   R['restored']=await page.evaluate("({text:document.getElementById('atelier-count').textContent,activeElement:document.activeElement.id})");assert R['restored']['activeElement']=='atelier-search'
   await page.screenshot(path=str(O/'restored-results.png'));assert not R['errors'];R['complete']=True
  except Exception as e:R['failure']=repr(e);R['traceback']=traceback.format_exc();raise
  finally:
   R['scope']='Production runtime unchanged. Actual DOM and Chromium AX semantics verified;not a screen-reader audio/announcement test andnofixapplied.'
   (O/'report.json').write_text(json.dumps(R,indent=2));await b.close()
asyncio.run(main())
