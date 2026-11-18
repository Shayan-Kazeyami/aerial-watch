import asyncio,json,pathlib,subprocess,os
from playwright.async_api import async_playwright
P=pathlib.Path(__file__).parent
async def main():
 server=subprocess.Popen(['python','-m','http.server','8791','--bind','127.0.0.1'],cwd=P,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 try:
  async with async_playwright()as pw:
   browser=await pw.chromium.launch(**({'executable_path':os.environ['PROOF_CHROMIUM']}if os.environ.get('PROOF_CHROMIUM')else {}),args=['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader']);page=await browser.new_page();page.set_default_timeout(10000);await page.goto('http://127.0.0.1:8791/test.html');await page.wait_for_function('typeof runProof==="function"');r=await asyncio.wait_for(page.evaluate('runProof()'),20);(P/'RESULT.json').write_text(json.dumps(r,indent=2));print(json.dumps(r,indent=2));await browser.close()
 finally:server.terminate()
asyncio.run(main())
