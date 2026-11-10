import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import vm from 'node:vm';
import {createAtelierNavigation} from '../atelier-navigation.js';
const source=readFileSync(new URL('../atelier-preview.js',import.meta.url),'utf8');
const block=source.split('// BEGIN restore-state synchronization')[1].split('\n').slice(1).join('\n').split('// END restore-state synchronization.')[0];
function harness({focus='importButton',selected=false}={}){
 const calls=[],outputs={},els={};
 for(const id of ['atelier-explosion','atelier-explosion-value','context','import-config','selection','assembly-canvas','close','part-name'])els[id]={id,focus(){calls.push(['focus',id]);}};
 els.selection.hidden=!selected;els['part-name'].textContent='Balance';
 const importButton={id:'importButton'},other={id:'other'},body={id:'body'};
 const active=focus==='importButton'?importButton:focus==='input'?els['import-config']:focus==='body'?body:other;
 els.context.contains=el=>el===importButton;
 const dock={id:'dock'},settings={id:'settings'};
 const context={navigation:createAtelierNavigation(),selectedIdentity:'',explodeAmount:0,selectedBefore:!selected,panelOpener:null,$:id=>els[id]||null,updateText:(id,value)=>outputs[id]=value,setMode:(mode,options)=>calls.push(['mode',mode,options.activate]),document:{body,activeElement:active,querySelector:selector=>selector.startsWith('.task-dock')?dock:settings,addEventListener:(name,handler)=>{context.listener=handler;}}};
 vm.createContext(context);vm.runInContext(block,context);
 return {context,calls,outputs,els,send:detail=>context.listener({detail})};
}
test('successful .55 restore opens Explode without activating model-changing actions',()=>{
 const h=harness();h.send({reason:'restore',amount:.55,view:'showcase'});
 assert.equal(h.context.explodeAmount,.55);assert.equal(h.els['atelier-explosion'].value,'55');assert.equal(h.outputs['atelier-explosion-value'],'55%');
 assert.deepEqual(h.calls,[['mode','explode',false],['focus','close']]);
});
test('restore mode precedence covers crown, selection, isolation, interior and complete watch',()=>{
 const cases=[ [{amount:.55,crownPulled:true,selected:true},'explode'],[{amount:0,crownPulled:true},'time'],[{view:'crown'},'time'],[{selected:true,interior:true},'selection'],[{isolated:true},'components'],[{interior:true},'inside'],[{},'explore'] ];
 for(const [detail,expected] of cases){const h=harness();h.send({reason:'restore',amount:0,...detail});assert.deepEqual(h.calls[0],['mode',expected,false]);}
});
test('adopts restored selection before opening tools, preventing sync selection takeover',()=>{
 const h=harness({selected:true});h.context.setMode=(mode,options)=>{assert.equal(h.context.selectedBefore,true);h.calls.push(['mode',mode,options.activate]);};
 h.send({reason:'restore',amount:.55,selected:true});assert.equal(h.calls[0][1],'explode');
});
test('ordinary zero events update slider but do not force Explore or move focus',()=>{
 const h=harness();h.send({amount:0});assert.equal(h.outputs['atelier-explosion-value'],'0%');assert.deepEqual(h.calls,[]);
 h.send({amount:.75});assert.equal(h.els['atelier-explosion'].value,'75');assert.deepEqual(h.calls,[]);
});
test('focus returns visibly after import but does not steal unrelated focused control',()=>{
 for(const focus of ['importButton','input','body']){const h=harness({focus});h.send({reason:'restore',amount:0});assert.deepEqual(h.calls.at(-1),['focus','assembly-canvas']);}
 const h=harness({focus:'other'});h.send({reason:'restore',amount:.55});assert.deepEqual(h.calls,[['mode','explode',false]]);
});
test('amount remains bounded; capabilities remain untouched',()=>{
 for(const [amount,expected] of [[-2,0],[2,1],[NaN,0]]){const h=harness();h.send({amount});assert.equal(h.context.explodeAmount,expected);assert.deepEqual(h.calls,[]);}
 assert.match(source,/atelier:capabilities/);
});
test('runtime tags only successful restore with complete presentation state',()=>{
 const runtime=readFileSync(new URL('../assembly-review.js',import.meta.url),'utf8');
 assert.equal((runtime.match(/reason:'restore'/g)||[]).length,1);
 assert.match(runtime,/explosion\?\.setAmount\(config\.explosion,\{instant:true\}\);document\.dispatchEvent/);
 for(const key of ['view:config.view','interior:interiorView','crownPulled:!!config.crown.pulled','selected:restoredInspection.selected.length>0','isolated:restoredInspection.isolated!==null'])assert.ok(runtime.includes(key));
 assert.match(runtime,/explosion and pose restored/);
 assert.match(runtime,/catch\(e\).*Could not restore view:/);
});
test('desktop removes duplicate panel status while retaining the sole global live region',()=>{
 const css=readFileSync(new URL('../atelier-preview.css',import.meta.url),'utf8');const html=readFileSync(new URL('../atelier-preview.html',import.meta.url),'utf8');
 assert.match(css,/@media\(min-width:1051px\)\{#atelier-panel-status\{display:none\}\}/);
 assert.match(html,/<p class="atelier-status" role="status" id="status">/);
 assert.match(html,/id="atelier-panel-status"/);
 assert.match(css,/\.atelier-status\{display:block!important;position:absolute!important;width:1px!important/);
});

