import {test} from 'node:test';
import assert from 'node:assert/strict';
import {componentLabel,componentSearchText} from '../assembly-component-labels.js';
test('English balance searches find French movement descriptions',()=>{
 const data={sourceIndex:112,description:'Serge de balancier',partNumber:'OM10-00103'};
 assert.equal(componentLabel(data),'Balance rim · OM10 #112');
 assert(componentSearchText(data).includes('balance wheel'));assert(componentSearchText(data).includes('om10-00103'));
});
test('component names remain human-readable while source identities remain searchable',()=>{
 assert.equal(componentLabel({assemblyId:'SECONDS'}),'Small-seconds hand');
 assert.equal(componentLabel({assemblyId:'BACK-SCREW-0'}),'Caseback screw');
 assert(componentSearchText({sourceIndex:11,description:'Pierre bombée'}).includes('jewel bearing'));
 assert.equal(componentLabel({sourceIndex:50,description:'Pignon de remontoir'}),'Pinion · OM10 #50');
});
