import {verifyThreadTopology} from './verify-thread-topology.mjs';
import {readFile,writeFile} from 'node:fs/promises';import {createHash} from 'node:crypto';import path from 'node:path';import {fileURLToPath} from 'node:url';
const sha=b=>createHash('sha256').update(b).digest('hex');
export async function generateLeatherIdentity(root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..')){
 const spec=JSON.parse(await readFile(path.join(root,'scripts/leather-authoring-spec.json'),'utf8'));
 const asset='leather-assets/r14/leather.gltf',gltf=JSON.parse(await readFile(path.join(root,asset),'utf8'));
 if(gltf.buffers.length!==1||gltf.buffers[0].uri!=='geometry.bin')throw Error('Expected one external authored geometry buffer');
 const bytes=await readFile(path.join(root,'leather-assets/r14/geometry.bin'));if(bytes.length!==gltf.buffers[0].byteLength)throw Error('Declared geometry length differs from actual');
 // Labels are authored identity, not the old import-lineage schema. Preserve
 // compatibility extras (R12) and all transforms/geometry/material factors.
 gltf.meshes[0].name='Upper strap / '+spec.id;
 gltf.meshes[2].name='Lower strap / '+spec.id;
 for(const i of [1,3])gltf.meshes[i].name=(i===1?'Upper':'Lower')+' sewing / round '+spec.thread.diameterMm+' mm / '+spec.id;
 gltf.materials[3].name='thread / constant round '+spec.thread.diameterMm+' mm / '+spec.id;
 for(const node of gltf.nodes){node.extras={...node.extras,authoredGeometryId:spec.id};if(node.mesh!==undefined)node.name=gltf.meshes[node.mesh].name;}
 gltf.asset.extras={...gltf.asset.extras,authoredGeometryId:spec.id};
 await writeFile(path.join(root,asset),JSON.stringify(gltf));
 // TERMINAL_AVIF_GEOMETRY_SYNC: only texture transport descriptors differ.
 const avifPath=path.join(root,'leather-assets/r14/leather-qa-avif-gentle.gltf'),oldAvif=JSON.parse(await readFile(avifPath,'utf8')),nextAvif=structuredClone(gltf);
 for(const key of ['images','textures','extensionsUsed'])nextAvif[key]=oldAvif[key];
 await writeFile(avifPath,JSON.stringify(nextAvif));
 const meshes=gltf.meshes.map((mesh,index)=>({index,name:mesh.name,primitives:mesh.primitives.map(p=>{
  const a=gltf.accessors[p.attributes.POSITION],view=gltf.bufferViews[a.bufferView];if(a.componentType!==5126||a.type!=='VEC3'||view.byteStride)throw Error('Unsupported position layout');
  const off=(view.byteOffset||0)+(a.byteOffset||0),min=[Infinity,Infinity,Infinity],max=[-Infinity,-Infinity,-Infinity];for(let i=0;i<a.count;i++)for(let k=0;k<3;k++){const x=bytes.readFloatLE(off+12*i+4*k);if(!Number.isFinite(x))throw Error('Nonfinite position');min[k]=Math.min(min[k],x);max[k]=Math.max(max[k],x);}
  return {material:p.material,positionCount:a.count,indexCount:gltf.accessors[p.indices].count,bounds:{min,max}};
 })}));
 const threadMeshes=[meshes[1],meshes[3]];const topology=spec.thread.topology==='adaptive-closed-components'?[[1,88],[3,44]].map(([i,count])=>verifyThreadTopology(gltf,bytes,i,count)):null;const stitches=topology?topology.reduce((n,m)=>n+m.components,0):threadMeshes.reduce((n,m)=>n+m.primitives[0].positionCount/(spec.thread.ringsPerStitch*spec.thread.radialSides),0);if(stitches!==132)throw Error('Thread topology/spec differs; update authoring spec before generating identity');
 const assembly=await readFile(path.join(root,'rebuild/assembly.glb'));
 const identity={schemaVersion:1,...spec,asset,expectedGeometry:{bytes:bytes.length,sha256:sha(bytes),bufferIndex:0},thread:{...spec.thread,count:stitches,triangleCount:threadMeshes.reduce((n,m)=>n+m.primitives[0].indexCount/3,0)},meshes,hardware:{asset:'rebuild/assembly.glb',expectedBytes:assembly.length,expectedSha256:sha(assembly),verificationScope:'expected source identity only; not verified by leather-buffer loader'},generator:'scripts/generate-leather-identity.mjs'};
 await writeFile(path.join(root,'assembly-leather-authoring-identity.js'),'// Generated from final geometry bytes + explicit authoring spec. Regenerate after EVERY asset edit.\nexport const AUTHORED_LEATHER_IDENTITY=Object.freeze('+JSON.stringify(identity,null,2)+');\n');return identity;
}
if(process.argv[1]&&path.resolve(process.argv[1])===fileURLToPath(import.meta.url))await generateLeatherIdentity(process.argv[2]?path.resolve(process.argv[2]):undefined);
