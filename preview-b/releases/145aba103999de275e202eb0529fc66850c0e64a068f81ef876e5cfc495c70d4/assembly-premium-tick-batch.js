import * as THREE from './vendor/three.module.js';
function mergeTickGeometries(meshes){
 let vertices=0,indices=0;
 for(const m of meshes){const g=m.geometry,p=g.attributes.position,n=g.attributes.normal;if(!p||!n||p.isInterleavedBufferAttribute||n.isInterleavedBufferAttribute||p.itemSize!==3||n.itemSize!==3||p.normalized||n.normalized||!(p.array instanceof Float32Array)||!(n.array instanceof Float32Array)||p.count!==n.count||!p.array.every(Number.isFinite)||!n.array.every(Number.isFinite)||!g.index||g.index.count%3!==0||Object.keys(g.morphAttributes).length)return null;vertices+=p.count;indices+=g.index.count;}
 const pos=new Float32Array(vertices*3),normal=new Float32Array(vertices*3),index=vertices>65535?new Uint32Array(indices):new Uint16Array(indices);let vo=0,io=0;
 for(const m of meshes){const g=m.geometry,p=g.attributes.position,n=g.attributes.normal;pos.set(p.array,vo*3);normal.set(n.array,vo*3);for(let k=0;k<g.index.count;k++){const i=g.index.getX(k);if(!Number.isInteger(i)||i<0||i>=p.count)return null;index[io++]=i+vo;}vo+=p.count;}
 const geometry=new THREE.BufferGeometry();geometry.setAttribute('position',new THREE.BufferAttribute(pos,3));geometry.setAttribute('normal',new THREE.BufferAttribute(normal,3));geometry.setIndex(new THREE.BufferAttribute(index,1));return geometry;
}
// Private experiment only. Keep original meshes for exact inspection fallback.
export function createTickBatch(root){
 const ticks=[];root.traverse(o=>{if(o.isMesh&&/^SVG[ _]seconds-tick-\d{2}$/.test(o.name))ticks.push(o)});
 const ids=ticks.map(m=>Number(m.name.slice(-2))).sort((a,b)=>a-b);
 if(ids.length!==60||ids.some((n,i)=>n!==i))return {supported:false,reason:'Expected 60 distinct ticks.'};
 const parent=ticks[0].parent,ident=new THREE.Matrix4();
 if(!parent||ticks.some(m=>{m.updateMatrix();return m.parent!==parent||!m.matrix.equals(ident)||!m.visible||m.isSkinnedMesh||m.morphTargetInfluences||m.onBeforeRender!==THREE.Object3D.prototype.onBeforeRender||m.onAfterRender!==THREE.Object3D.prototype.onAfterRender||m.onBeforeShadow!==THREE.Object3D.prototype.onBeforeShadow||m.onAfterShadow!==THREE.Object3D.prototype.onAfterShadow||m.frustumCulled!==true||m.customDepthMaterial||m.customDistanceMaterial||Array.isArray(m.material)||!m.material?.isMaterial||m.material.transparent||!m.geometry?.index||Object.keys(m.geometry.attributes).sort().join(',')!=='normal,position'||m.geometry.groups.length||m.geometry.drawRange.start!==0||m.geometry.drawRange.count!==Infinity||!m.userData.premiumFacePart;}))return {supported:false,reason:'Unexpected tick topology, transforms or material.'};
 const groups=new Map();for(const m of ticks){const key=m.material;if(!groups.has(key))groups.set(key,[]);groups.get(key).push(m)}
 if(groups.size!==2||ticks.some(m=>m.castShadow!==ticks[0].castShadow||m.receiveShadow!==ticks[0].receiveShadow||m.layers.mask!==ticks[0].layers.mask||m.renderOrder!==ticks[0].renderOrder))return {supported:false,reason:'Unexpected material or render-state groups.'};
 const batches=[];
 try{for(const [material,items] of groups){const geometry=mergeTickGeometries(items);if(!geometry)throw new Error('Cannot merge tick geometry.');const mesh=new THREE.Mesh(geometry,material);mesh.name='Batched seconds ticks';mesh.userData={premiumFacePart:true,designRevision:items[0].userData.designRevision,batchedTickNames:items.map(m=>m.name)};mesh.castShadow=items[0].castShadow;mesh.receiveShadow=items[0].receiveShadow;mesh.layers.mask=items[0].layers.mask;mesh.renderOrder=items[0].renderOrder;mesh.visible=false;parent.add(mesh);batches.push(mesh)}}catch(e){for(const m of batches){m.removeFromParent();m.geometry.dispose()}return {supported:false,reason:e.message}}
 let enabled=false,disposed=false;const tickSet=new Set(ticks);
 function setEnabled(value){if(disposed)return;enabled=!!value;for(const m of ticks)m.visible=!enabled;for(const m of batches)m.visible=enabled;}
 return {supported:true,ticks,batches,get enabled(){return enabled},raycastVisible(mesh){return !disposed&&enabled&&tickSet.has(mesh)},setEnabled,dispose(){if(disposed)return;setEnabled(false);disposed=true;for(const m of batches){m.removeFromParent();m.geometry.dispose()}}};
}
