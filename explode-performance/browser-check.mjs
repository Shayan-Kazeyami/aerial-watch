import {chromium} from 'playwright';
import fs from 'node:fs';
const out='explode-performance/evidence';fs.mkdirSync(out,{recursive:true});
const release='1b013b90cdd2d448fbe5c88bc90e28786ba3424600fb43d35ddabed0707d9158';
const base=process.env.BASE_URL||`http://127.0.0.1:8765/preview-b/releases/${release}/atelier-preview.html`;
const candidate=fs.readFileSync('explode-performance/url.txt','utf8').trim();
const url=base+'?quality=efficient';
const b=await chromium.launch({headless:true,args:['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader','--disable-dev-shm-usage']});
const report={release,url,candidate,setup:'Chromium SwiftShader 430x932 DPR1 Smooth; separately sealed immutable baseline/candidate',modes:{}};
try{
 for(const mode of ['baseline','candidate']){
 const page=await b.newPage({viewport:{width:430,height:932},deviceScaleFactor:1,isMobile:true,hasTouch:true});page.setDefaultTimeout(180000);
 const errors=[];page.on('pageerror',e=>errors.push(String(e)));
 
 await page.route('**/assembly-review.js*',async route=>{const response=await route.fetch();await route.fulfill({response,body:await response.text()+`\nwindow.explodeQA={freeze(){for(const name of ['animate','animate-movement']){const e=$(name);e.checked=false;e.dispatchEvent(new Event('change',{bubbles:true}));}stopTour();clock.seek(0,{track:'mechanism'});clock.seek(0,{track:'hands'});applyClockPose(clock.snapshot());dirty=true;},state(){return {ready:!loading&&!failed&&!cameraTween&&!explosion?.animating,explosion:explosion.snapshot(),backend:backendIdentity,quality,calls:renderer.info.render.calls,triangles:renderer.info.render.triangles};}};`});});
 await page.goto((mode==='baseline'?base:candidate)+'?quality=efficient',{waitUntil:'domcontentloaded',timeout:180000});await page.locator('body[data-ready=true]').waitFor({timeout:300000});await page.evaluate(()=>explodeQA.freeze());await page.waitForFunction(()=>explodeQA.state().ready,{timeout:180000});
 const states={};
 for(const [name,amount] of [['assembled',0],['exploded',1],['partial',.37],['reassembled',0]]){
 await page.evaluate(amount=>document.dispatchEvent(new CustomEvent('atelier:explode',{detail:{amount,instant:true}})),amount);
 await page.waitForFunction(()=>explodeQA.state().ready,{timeout:180000});await page.evaluate(()=>explodeQA.freeze());await page.waitForTimeout(600);
 states[name]=await page.evaluate(()=>explodeQA.state());await page.locator('#assembly-canvas').screenshot({path:`${out}/${mode}-${name}.png`,timeout:120000});console.log(mode,name,states[name].explosion.amount);
 }
 if(errors.length)throw Error(JSON.stringify(errors));report.modes[mode]={states,errors};await page.close();
 }
}finally{fs.writeFileSync(`${out}/report.json`,JSON.stringify(report,null,2));await b.close();}
