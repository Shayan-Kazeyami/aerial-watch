import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import vm from 'node:vm';

const source=await readFile(new URL('../assembly-review.js',import.meta.url),'utf8');
const stateSource=await readFile(new URL('../assembly-state.js',import.meta.url),'utf8');
const {createObjectTreeDisposer}=await import('data:text/javascript;base64,'+Buffer.from(stateSource).toString('base64'));

test('load rejection and registered ownership share one resource cleanup boundary',()=>{
 const calls=[],root={traverse:visit=>visit({isMesh:true,geometry:{dispose:()=>calls.push('geometry')},material:null}),removeFromParent:()=>calls.push('detach')};
 const helpers=source.slice(source.indexOf('const objectDisposers='),source.indexOf('scene.background ='));
 const context=vm.createContext({createObjectTreeDisposer,root});
 vm.runInContext(helpers+'\nconst registered=ownedObjectTreeDisposer(root);disposeObjectTree(root);registered();',context);
 assert.deepEqual(calls,['geometry','detach']);
});

test('a rejected proposal retry releases its loaded tree and remains retryable',async()=>{
 const retry={disabled:false},result={gltf:{scene:{}}};let disposals=0;
 const warning=source.slice(source.indexOf('function proposalWarning(error){'),source.indexOf('function installProposal(result){'));
 const context=vm.createContext({lifecycle:{disposed:false},loadWarnings:[],
  $:()=>retry,visibility(){},announce(){},loadGLTFAsset:async()=>result,assetOptions:()=>({}),
  installProposal(){throw new Error('Expected two distinct open-work plates.');},
  disposeObjectTree:root=>{assert.equal(root,result.gltf.scene);disposals++;},console});
 vm.runInContext(warning+'\nproposalWarning(new Error("first failure"));',context);
 await retry.onclick();
 assert.equal(disposals,1);assert.equal(retry.disabled,false);
});
