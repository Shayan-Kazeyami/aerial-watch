import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';

const source=await readFile(new URL('../assembly-state.js',import.meta.url),'utf8');
const {createObjectTreeDisposer}=await import('data:text/javascript;base64,'+Buffer.from(source).toString('base64'));

function tree(objects,calls){return {traverse:visit=>objects.forEach(visit),removeFromParent:()=>calls.push('detach')};}
function resource(name,calls,extra={}){return {...extra,dispose:()=>calls.push(name)};}

test('tree cleanup disposes shared geometry, materials and textures once and detaches',()=>{
  const calls=[],geometry=resource('geometry',calls),texture=resource('texture',calls,{isTexture:true});
  const material=resource('material',calls,{map:texture});
  const dispose=createObjectTreeDisposer(tree([{isMesh:true,geometry,material},{isMesh:true,geometry,material:[material]}],calls));
  dispose();dispose();
  assert.deepEqual(calls,['geometry','material','texture','detach']);
});

test('tree cleanup continues and detaches if a resource disposer throws',()=>{
  const calls=[],broken={dispose(){calls.push('broken');throw new Error('failure');}};
  const geometry=resource('geometry',calls),texture=resource('texture',calls,{isTexture:true}),material=resource('material',calls,{map:texture});
  const dispose=createObjectTreeDisposer(tree([{isMesh:true,geometry:broken,material},{isMesh:true,geometry,material}],calls));
  assert.throws(dispose,AggregateError);
  assert.deepEqual(calls,['broken','geometry','material','texture','detach']);
  assert.doesNotThrow(dispose);
  assert.deepEqual(calls,['broken','geometry','material','texture','detach']);
});
