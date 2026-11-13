import {createLugFinish,lugFinishBackendPolicy} from './assembly-case-lug-finish.js';
import {MeshPhysicalMaterial} from './vendor/three.module.js';
import {CASE_SOURCE_BUFFERS} from './assembly-parametric-case-source.js';
import {CASE_COMBINED_DATA} from './assembly-case-combined-data.js';
import {prepareCaseCombinedMaterials} from './assembly-case-combined-material.js';
export {loadCombinedCaseAsset} from './assembly-case-combined-loading.js';
import {createObjectTreeDisposer} from './assembly-state.js';

const sha=async bytes=>Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',bytes)),v=>v.toString(16).padStart(2,'0')).join('');
const bytes=attribute=>new Uint8Array(attribute.array.buffer,attribute.array.byteOffset,attribute.array.byteLength);
const checkAbort=signal=>signal?.throwIfAborted();
const identity=matrix=>matrix.elements.every((v,i)=>Math.abs(v-(i%5===0?1:0))<1e-7);
export const COMBINED_CASE_REVISION=CASE_COMBINED_DATA.revision;

/** Private opt-in replacement. Owns only its cloned combined geometry and newly created materials/textures.
 * Source mesh, metadata, parent, axes and transforms are retained; cap008 is NOT applied.
 * Candidate and baseline both export native positions as (x,z,-y), identity local matrices.
 */
export async function createCombinedCaseReplacement({sourceMesh,loadCandidate,signal,plain=false,mapsEnabled=true,lugFinish=true,nativeRenderer=true,nodeLugFinishSupported=false},{prepareMaterials=prepareCaseCombinedMaterials}={}) {
  if(!sourceMesh?.isMesh||sourceMesh.userData?.assemblyId!=='CASE')throw new TypeError('Exactly one source CASE mesh is required.');
  const lugPolicy=lugFinishBackendPolicy({enabled:lugFinish,plain,nativeRenderer,nodeLugFinishSupported});
  if(!crypto?.subtle)throw new Error('CASE replacement requires SHA-256.');
  checkAbort(signal);sourceMesh.updateMatrix();
  if(!identity(sourceMesh.matrix))throw new Error('Unrecognized CASE local transform.');
  const original=sourceMesh.geometry,originalMaterial=sourceMesh.material;
  const fields=[['POSITION',original.attributes.position],['NORMAL',original.attributes.normal],['TEXCOORD_0',original.attributes.uv],['indices',original.index]];
  const snapshots=fields.map(([name,attribute])=>{
    const expected=CASE_SOURCE_BUFFERS[name];
    if(!attribute||attribute.isInterleavedBufferAttribute||attribute.normalized||attribute.count!==expected.count||attribute.itemSize!==expected.itemSize)throw new Error(`Unrecognized source CASE ${name}.`);
    return {name,attribute,data:bytes(attribute).slice()};
  });
  await Promise.all(snapshots.map(async s=>{if(await sha(s.data)!==CASE_SOURCE_BUFFERS[s.name].sha256)throw new Error(`Source CASE ${s.name} hash mismatch; cap008/other replacements cannot be stacked.`);}));
  checkAbort(signal);
  let loaded,disposeLoaded,derived,materials=[],plainMaterials=[],finishStudy,lugStudy;
  try {
    loaded=await loadCandidate();const root=(loaded.gltf||loaded).scene;
    if(!root?.traverse)throw new TypeError('Candidate GLTF scene is required.');
    disposeLoaded=createObjectTreeDisposer(root);checkAbort(signal);
    const meshes=[];root.traverse(o=>{if(o.isMesh)meshes.push(o);});
    if(meshes.length!==1||meshes[0].userData?.assemblyId!=='CASE')throw new Error('Candidate must contain only CASE.');
    const candidate=meshes[0];root.updateMatrixWorld(true);candidate.updateMatrix();
    if(!identity(candidate.matrix)||!identity(candidate.matrixWorld))throw new Error('Unrecognized candidate CASE local transform.');
    const geometry=candidate.geometry;
    for(const [name,itemSize,Type,count] of [['position',3,Float32Array,CASE_COMBINED_DATA.vertices],['normal',3,Float32Array,CASE_COMBINED_DATA.vertices],['uv',2,Float32Array,CASE_COMBINED_DATA.vertices],['tangent',4,Float32Array,CASE_COMBINED_DATA.vertices],['index',1,Uint32Array,CASE_COMBINED_DATA.triangles*3]]){
      const attribute=name==='index'?geometry.index:geometry.attributes[name];
      if(!attribute||attribute.isInterleavedBufferAttribute||attribute.normalized!==false||attribute.itemSize!==itemSize||attribute.count!==count||!(attribute.array instanceof Type)||attribute.array.length!==count*itemSize)throw new Error(`Candidate CASE ${name} attribute shape mismatch.`);
      if(await sha(bytes(attribute))!==CASE_COMBINED_DATA[name+'SHA256'])throw new Error('Candidate CASE buffer hash mismatch.');
    }
    checkAbort(signal);
    sourceMesh.updateMatrix();
    if(!identity(sourceMesh.matrix)||sourceMesh.geometry!==original||sourceMesh.material!==originalMaterial||snapshots.some(s=>{const current=s.name==='indices'?original.index:original.attributes[{POSITION:'position',NORMAL:'normal',TEXCOORD_0:'uv'}[s.name]];if(current!==s.attribute)return true;const live=bytes(s.attribute);return live.length!==s.data.length||live.some((v,i)=>v!==s.data[i]);}))throw new Error('Source CASE changed during replacement preparation.');
    derived=geometry.clone();
    const groups=CASE_COMBINED_DATA.groups;let cursor=0;
    if(!Array.isArray(groups)||geometry.index.count!==CASE_COMBINED_DATA.triangles*3)throw new Error('Combined CASE triangle/group mismatch.');
    derived.clearGroups();
    for(const g of groups){if(g.start!==cursor||!Number.isInteger(g.count)||g.count<=0||g.count%3||!Number.isInteger(g.materialIndex)||g.materialIndex<0||g.materialIndex>4)throw new Error('Combined CASE group coverage mismatch.');derived.addGroup(g.start,g.count,g.materialIndex);cursor+=g.count;}
    if(cursor!==geometry.index.count)throw new Error('Combined CASE incomplete group coverage.');
    derived.computeBoundingBox();derived.computeBoundingSphere();
    const specs=[['Smooth steel case surfaces',.29],['Polished steel',.13],['Satin terminal steel',.34]];
    materials=specs.map(([name,roughness])=>new MeshPhysicalMaterial({name:`${name}`,color:0xb9bec4,metalness:1,roughness,clearcoat:0}));
    plainMaterials=specs.map(([name])=>new MeshPhysicalMaterial({name:`plain silver · ${name}`,color:0xb9bec4,metalness:1,roughness:.29,clearcoat:0}));
    finishStudy=await prepareMaterials(derived,signal,{mapsEnabled});
    checkAbort(signal);
    sourceMesh.updateMatrix();
    if(!identity(sourceMesh.matrix)||sourceMesh.geometry!==original||sourceMesh.material!==originalMaterial||snapshots.some(s=>{const current=s.name==='indices'?original.index:original.attributes[{POSITION:'position',NORMAL:'normal',TEXCOORD_0:'uv'}[s.name]];if(current!==s.attribute)return true;const live=bytes(s.attribute);return live.length!==s.data.length||live.some((v,i)=>v!==s.data[i]);}))throw new Error('Source CASE changed during replacement preparation.');
    materials.push(...finishStudy.materials);plainMaterials.push(...finishStudy.materials.map(()=>plainMaterials[0].clone()));
    lugStudy=createLugFinish(derived,materials[0],{enabled:lugPolicy.enabled});materials.push(lugStudy.material);plainMaterials.push(plainMaterials[0].clone());
    const activeMaterials=plain?plainMaterials:materials;let enabled=false,disposed=false;
    const audit=Object.freeze({revision:CASE_COMBINED_DATA.revision,diagnosticOnly:true,representation:'FINE R5 COMBINED; fixed geometry across quality modes',numericalGateStatus:'R5 targeted front repair; combined-view acceptance pending; not manufacturing certified',loadMetrics:loaded.metrics?{...loaded.metrics}:null,asset:CASE_COMBINED_DATA.glbSHA256,triangles:CASE_COMBINED_DATA.triangles,groups:derived.groups.map(g=>({...g})),finishMode:plain?'plain':'machining-g32',nativeFrame:'source local (x,z,-y), unchanged source mesh/parent transform',cap008Applied:false,uvAuthored:true,materialStudy:finishStudy.proof});
    return {mesh:sourceMesh,materials:activeMaterials,plainMaterials,audit,
      get lugFinish(){return {...lugStudy.audit,requested:lugPolicy.requested,supported:lugPolicy.supported,reason:lugPolicy.reason,plainComparison:!!plain,implementation:lugPolicy.implementation,renderedParity:lugPolicy.renderedParity,backendSupport:'native GLSL or installed R5 TSL adapter; rendered node parity pending',nativeRenderer,policy:'active when R5 selected unless lugFinish=off or caseFinish=plain'};},
      setLugFinishEnabled(value){Object.assign(lugPolicy,lugFinishBackendPolicy({enabled:!!value,plain,nativeRenderer,nodeLugFinishSupported}));lugStudy.setEnabled(lugPolicy.enabled);materials[5]=lugStudy.material;},
      get finishNormalProof(){return finishStudy.normalProof;},
      get finishComparison(){return finishStudy.comparison;},
      get textureFiltering(){return finishStudy.textureFiltering;},
      setTextureQuality(quality,maxSupported){finishStudy.setTextureQuality(quality,maxSupported);},
      get enabled(){return enabled&&!disposed;},
      get ownsGeometry(){return enabled&&!disposed&&sourceMesh.geometry===derived;},
      setEnabled(value){
        if(disposed)return;const next=!!value;
        if(sourceMesh.geometry!==original&&sourceMesh.geometry!==derived){if(next)throw new Error('CASE geometry ownership conflict.');enabled=false;return;}
        sourceMesh.geometry=next?derived:original;sourceMesh.material=next?activeMaterials:originalMaterial;enabled=next;
      },
      dispose(){if(disposed)return;disposed=true;if(sourceMesh.geometry===derived){sourceMesh.geometry=original;sourceMesh.material=originalMaterial;}enabled=false;derived.dispose();for(const material of [...materials,...plainMaterials])if(!finishStudy?.materials.includes(material)&&material!==lugStudy?.baseline&&material!==lugStudy?.candidate)material.dispose();finishStudy?.dispose();lugStudy?.dispose();},
    };
  }catch(error){derived?.dispose();for(const material of [...materials,...plainMaterials])if(!finishStudy?.materials.includes(material)&&material!==lugStudy?.baseline&&material!==lugStudy?.candidate)material.dispose();finishStudy?.dispose();lugStudy?.dispose();throw error;}
  finally{disposeLoaded?.();}
}
