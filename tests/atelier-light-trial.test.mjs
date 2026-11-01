import {test} from 'node:test';
import assert from 'node:assert/strict';
import {atelierReflectionCards,createAssemblyMaterials} from '../assembly-materials.js';

test('default and unknown light choices retain the original seven-card atelier rig',()=>{
  const expected=[
    [[0,48,38],[30,15],0xfff9f2,.8],
    [[-32,28,48],[20,45],0xfff7ed,4.5],
    [[32,2,25],[3.5,48],0xf1f5ff,6],
    [[-24,10,-35],[5,30],0xe5edff,2.5],
    [[5,45,10],[35,22],0xffffff,1.6],
    [[12,0,40],[10,48],0x080909,.03],
    [[-3,0,-45],[35,40],0xe5e9ed,.35],
  ];
  assert.deepEqual(atelierReflectionCards(),expected);
  assert.deepEqual(atelierReflectionCards('unknown'),expected);
});

test('atelier2 changes only the broad left card and adds a restrained neutral reflector',()=>{
  const base=atelierReflectionCards(),trial=atelierReflectionCards('atelier2');
  assert.equal(trial.length,base.length+1);
  for(let i=0;i<base.length;i++)if(i!==1)assert.deepEqual(trial[i],base[i]);
  assert.deepEqual(trial[1],[[-38,24,45],[10,45],0xfff7ed,4.5]);
  assert.deepEqual(trial[7],[[-6,6,58],[12,20],0xf4f5f6,.65]);
  trial[0][0][0]=99;
  assert.equal(atelierReflectionCards()[0][0][0],0);
});

test('optional light selector changes neither legacy nor atelier material parameters',()=>{
  for(const atelier of [false,true]){
    const base=createAssemblyMaterials(null,{atelier});
    const trial=createAssemblyMaterials(null,{atelier,light:'atelier2'});
    for(const kind of ['blued','crystal','polished','satin']){
      const data={userData:{finishKind:kind,assemblyId:kind==='crystal'?'FRONT-CRYSTAL':'TEST'}};
      const a=base.apply(data),b=trial.apply(data);
      for(const field of ['roughness','metalness','transmission','thickness','specularIntensity','attenuationDistance'])assert.equal(a[field],b[field]);
      assert(a.color.equals(b.color));
    }
    base.dispose();trial.dispose();
  }
});
