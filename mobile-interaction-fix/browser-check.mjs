// Run with Playwright installed. BASE_URL serves candidate module directory.
import {chromium} from 'playwright';import assert from 'node:assert/strict';
const base=process.env.BASE_URL||'http://127.0.0.1:8000/';
const browser=await chromium.launch({headless:true,...(process.env.CHROMIUM_PATH?{executablePath:process.env.CHROMIUM_PATH}:{}),args:['--no-sandbox']});
for(const touch of [false,true]){
const context=await browser.newContext({viewport:{width:430,height:700},hasTouch:touch,isMobile:touch});const page=await context.newPage();await page.goto(base);await page.evaluate(async()=>{document.body.innerHTML='<canvas tabindex="0" style="width:400px;height:600px"></canvas>';const {createCrownHotspot}=await import('./assembly-crown-hotspot.js');window.turns=[];window.toggles=0;window.p={x:200,y:250};window.h=createCrownHotspot({canvas:document.querySelector('canvas'),available:()=>true,getAnchor:()=>p,getOutline:()=>`${p.x-10},${p.y-10} ${p.x+10},${p.y-10} ${p.x},${p.y+10}`,getPulled:()=>false,onTurn:d=>turns.push(d),onToggle:()=>toggles++});function update(){h.update();requestAnimationFrame(update)}update()});
// Projection is recomputed on the next paint, with the same SVG nodes retained.
const polygon=await page.locator('.crown-halo polygon').first().elementHandle();
await page.evaluate(()=>p={x:210,y:255});await page.waitForTimeout(40);
assert.equal(await polygon.getAttribute('points'),'200,245 220,245 210,265');
assert.ok(await polygon.evaluate(e=>e.isConnected));
await page.evaluate(()=>p={x:200,y:250});await page.waitForTimeout(40);
if(touch){
const c=await context.newCDPSession(page);await c.send('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:[{x:200,y:250}]});await c.send('Input.dispatchTouchEvent',{type:'touchMove',touchPoints:[{x:200,y:228}]});await page.waitForTimeout(300);const a=await page.evaluate(()=>turns.reduce((a,b)=>a+b,0));await page.waitForTimeout(300);const b=await page.evaluate(()=>turns.reduce((a,b)=>a+b,0));assert.ok(b>a+10);await c.send('Input.dispatchTouchEvent',{type:'touchMove',touchPoints:[{x:200,y:250}]});await page.waitForTimeout(100);const stopped=await page.evaluate(()=>turns.length);await page.waitForTimeout(250);assert.equal(await page.evaluate(()=>turns.length),stopped);await c.send('Input.dispatchTouchEvent',{type:'touchEnd',touchPoints:[]});
}else{await page.mouse.move(200,250);await page.mouse.down();await page.mouse.move(200,228);await page.waitForTimeout(300);const a=await page.evaluate(()=>turns.length);await page.waitForTimeout(300);assert.ok(await page.evaluate(()=>turns.length)>a);await page.mouse.move(200,250);await page.waitForTimeout(100);const n=await page.evaluate(()=>turns.length);await page.waitForTimeout(250);assert.equal(await page.evaluate(()=>turns.length),n);await page.mouse.up();await page.evaluate(()=>p={x:230,y:260});await page.waitForTimeout(50);assert.equal(await page.locator('.crown-hotspot').evaluate(e=>e.style.left),'230px');}
assert.equal(await page.evaluate(()=>toggles),0);await context.close();console.log(touch?'touch hold PASS':'desktop hold PASS');}
await browser.close();
