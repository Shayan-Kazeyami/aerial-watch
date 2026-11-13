import * as THREE from './vendor/three.module.js';

// Read-only accounting of declared live resources. This is not a GPU-memory
// query: drivers may pad/repack, retain retired allocations or defer disposal.
const enums=suffix=>new Map(Object.entries(THREE).filter(([name,value])=>name.endsWith(suffix)&&typeof value==='number').map(([name,value])=>[value,name]));
const formats=enums('Format'),types=enums('Type');
const positive=value=>Number.isFinite(value)&&value>0?Math.floor(value):null;
const sum=values=>values.reduce((total,value)=>total+(Number.isFinite(value)?value:0),0);
function depthTexelBytes(type,format=THREE.DepthFormat){
 if(!Number.isFinite(type))return null;
 if(format===THREE.DepthStencilFormat&&type===THREE.FloatType)return 8;
 if(type===THREE.UnsignedShortType)return 2;
 if(type===THREE.UnsignedIntType||type===THREE.FloatType||type===THREE.UnsignedInt248Type)return 4;
 if(Number.isFinite(THREE.Float32UnsignedInt248RevType)&&type===THREE.Float32UnsignedInt248RevType)return 8;
 return null;
}
function bytes(width,height,depth,format,type){
 if(!width||!height||!depth)return null;
 if(format===THREE.DepthFormat||format===THREE.DepthStencilFormat){const b=depthTexelBytes(type,format);return b===null?null:width*height*depth*b;}
 try{return THREE.TextureUtils.getByteLength(width,height,format,type)*depth;}catch{return null;}
}
function mipDimensions(width,height,depth,threeD){const result=[];do{result.push({width,height,depth});if(width===1&&height===1&&(!threeD||depth===1))break;width=Math.max(1,width>>1);height=Math.max(1,height>>1);if(threeD)depth=Math.max(1,depth>>1);}while(true);return result;}
function textureRecord(texture,overrides={}){
 const image=texture.image??texture.source?.data,faces=texture.isCubeTexture?6:1;
 const first=Array.isArray(image)?image[0]:image;
 const width=positive(overrides.width??first?.width??texture.mipmaps?.[0]?.width),height=positive(overrides.height??first?.height??texture.mipmaps?.[0]?.height),depth=positive(overrides.depth??first?.depth??1);
 let chains;
 if(texture.isCubeTexture&&Array.isArray(image))chains=image.map(face=>face?.mipmaps?.length?face.mipmaps:[face]);
 else if(texture.mipmaps?.length)chains=[texture.mipmaps];
 else chains=[[first]];
 const explicit=chains.some(chain=>chain.length>1)||!!texture.mipmaps?.length||!!first?.mipmaps?.length;
 const mipCount=explicit?Math.max(...chains.map(chain=>chain.length)):texture.generateMipmaps&&width&&height?mipDimensions(width,height,depth,!!texture.isData3DTexture).length:1;
 const sizes=width&&height?mipDimensions(width,height,depth,!!texture.isData3DTexture).slice(0,mipCount):[];
 const levelBytes=sizes.map(size=>bytes(size.width,size.height,size.depth,texture.format,texture.type));
 let logicalBytes=levelBytes.length===mipCount&&levelBytes.every(Number.isFinite)?sum(levelBytes)*faces:null;
 // Render-target cube mip arrays may have a shared level array rather than
 // six image chains. Logical storage still counts six faces above.
 const payloads=chains.flat().map(level=>level?.data?.byteLength).filter(Number.isFinite);
 const uploadPayloadBytes=payloads.length?sum(payloads):null;
 const compressed=!!(texture.isCompressedTexture||texture.isCompressedCubeTexture||texture.isCompressedArrayTexture);
 const assumptions=[];
 if(!width||!height)assumptions.push('Image dimensions not available yet.');
 if(logicalBytes===null)assumptions.push('Unsupported/unknown format dimensions; excluded from known subtotal.');
 if(compressed&&uploadPayloadBytes!==null&&logicalBytes!==null&&uploadPayloadBytes!==logicalBytes)assumptions.push('Provided compressed mip payload differs from format-defined logical size; both are reported.');
 if(texture.format===THREE.RGBFormat)assumptions.push('RGB logical payload may be repacked to RGBA by the backend.');
 if(texture.generateMipmaps&&!explicit)assumptions.push('Generated full mip chain inferred from current dimensions; residency not queried.');
 return {uuid:texture.uuid??null,name:texture.name||'',width,height,depth,faces,format:texture.format,formatName:formats.get(texture.format)||'unknown',type:texture.type,typeName:types.get(texture.type)||'unknown',compressed,mipCount,generateMipmaps:!!texture.generateMipmaps,explicitMipPayload:explicit,baseLevelLogicalBytes:levelBytes[0]===undefined?null:levelBytes[0]*faces,logicalBytes,uploadPayloadBytes,source:'Live texture after loader/transcode, not the encoded download size',assumptions};
}

export function resourceSnapshot({renderer,scene,targets=[]}={}){
 const textures=new Map(),targetRecords=[],targetSeen=new Set(),targetTextureSet=new Set(),implicitDepth=[],msaaColor=[],msaaDepth=[];
 const addTexture=(texture,usage,overrides)=>{if(!texture?.isTexture)return null;let record=textures.get(texture);if(!record){record={...textureRecord(texture,overrides),uses:[]};textures.set(texture,record);}record.uses.push(usage);return record;};
 const visitValue=(value,usage,seen=new Set(),depth=0)=>{if(!value||depth>4)return;if(value.isTexture){addTexture(value,usage);return;}if(typeof value!=='object'||seen.has(value))return;seen.add(value);if(Array.isArray(value)){value.forEach((v,i)=>visitValue(v,`${usage}[${i}]`,seen,depth+1));return;}if(depth<2&&('value'in value))visitValue(value.value,usage+'.value',seen,depth+1);};
 const visitMaterial=(material,usage)=>{if(!material)return;for(const [key,value]of Object.entries(material)){if(key==='uniforms'&&value)for(const [name,u]of Object.entries(value))visitValue(u,`${usage}.uniforms.${name}`);else visitValue(value,`${usage}.${key}`);}};
 // Targets first ensure exact target dimensions take precedence over a material
 // alias of the same render-target texture.
 const allTargets=[...targets];scene?.traverse?.(object=>{if(object.shadow)for(const key of ['map','mapPass'])if(object.shadow[key]?.isRenderTarget)allTargets.push({label:`shadow:${object.name||object.type}:${key}`,target:object.shadow[key]});});
 for(const input of allTargets){const target=input?.target??input;if(!target?.isRenderTarget||targetSeen.has(target))continue;targetSeen.add(target);
  const name=input?.target?input.label||input.name||`target-${targetRecords.length+1}`:target.texture?.name||`target-${targetRecords.length+1}`;
  const width=positive(target.width),height=positive(target.height),depth=positive(target.depth??1),faces=target.isWebGLCubeRenderTarget||target.isCubeRenderTarget?6:1,samples=Math.max(0,Math.floor(target.samples||0));
  const attachments=(target.textures?.length?target.textures:[target.texture]).filter(Boolean),colors=attachments.map((texture,index)=>{targetTextureSet.add(texture);const r=addTexture(texture,`${name}.color[${index}]`,{width,height,depth});return {uuid:r.uuid,format:r.format,formatName:r.formatName,type:r.type,typeName:r.typeName,logicalBytes:r.logicalBytes,baseLevelLogicalBytes:r.baseLevelLogicalBytes};});
  const resolvedColorLogicalBytes=colors.every(c=>Number.isFinite(c.logicalBytes))?sum(colors.map(c=>c.logicalBytes)):null;
  const multisampleColorLogicalBytes=samples>1&&colors.every(c=>Number.isFinite(c.baseLevelLogicalBytes))?sum(colors.map(c=>c.baseLevelLogicalBytes))*samples:0;msaaColor.push(multisampleColorLogicalBytes);
  let depthAttachment=null,resolvedDepthLogicalBytes=0,implicitDepthUpperBytes=0,multisampleDepthUpperBytes=0;
  if(target.depthBuffer){
   const depthTexture=target.depthTexture;
   if(depthTexture){targetTextureSet.add(depthTexture);const r=addTexture(depthTexture,`${name}.depth`,{width,height,depth});depthAttachment={uuid:r.uuid,format:r.format,formatName:r.formatName,type:r.type,typeName:r.typeName};resolvedDepthLogicalBytes=r.logicalBytes;}
   else{implicitDepthUpperBytes=width&&height&&depth?width*height*depth*faces*(target.stencilBuffer?8:4):null;implicitDepth.push(implicitDepthUpperBytes);}
   if(samples>1){const perPixel=depthTexture?depthTexelBytes(depthTexture.type,depthTexture.format):(target.stencilBuffer?8:4);multisampleDepthUpperBytes=width&&height&&depth&&perPixel?width*height*depth*faces*perPixel*samples:null;msaaDepth.push(multisampleDepthUpperBytes);}
  }
  targetRecords.push({name,width,height,depth,faces,samples,depthBuffer:!!target.depthBuffer,stencilBuffer:!!target.stencilBuffer,colorAttachments:colors,depthAttachment,resolvedColorLogicalBytes,resolvedDepthLogicalBytes,implicitDepthUpperBytes,multisampleColorLogicalBytes,multisampleDepthUpperBytes,conservativeKnownBytes:sum([resolvedColorLogicalBytes,resolvedDepthLogicalBytes,implicitDepthUpperBytes,multisampleColorLogicalBytes,multisampleDepthUpperBytes]),assumptions:['Declared samples, not measured driver allocation.','MSAA counts separate sample storage plus resolved textures; backend may not retain a separate resolved implicit depth buffer.',...(!target.depthTexture&&target.depthBuffer?['Implicit depth uses 4 bytes/texel, or conservative 8 with stencil; backend-specific format not queried.']:[])]});
 }
 if(scene){addTexture(scene.background,'scene.background');addTexture(scene.environment,'scene.environment');scene.traverse?.(object=>{const materials=Array.isArray(object.material)?object.material:[object.material];materials.forEach((material,index)=>visitMaterial(material,`${object.name||object.type||'object'}.material[${index}]`))});}
 const records=[...textures.values()],assetRecords=[...textures].filter(([texture])=>!targetTextureSet.has(texture)).map(([,record])=>record),targetTextureRecords=[...textures].filter(([texture])=>targetTextureSet.has(texture)).map(([,record])=>record);
 const canvas=renderer?.domElement,width=positive(canvas?.width),height=positive(canvas?.height),rawRGBABytes=width&&height?width*height*4:null;
 const numericMemory=Object.fromEntries(Object.entries(renderer?.info?.memory||{}).filter(([,value])=>Number.isFinite(value)));
 return {schemaVersion:1,scope:'Read-only declared live texture/target logical storage; not physical VRAM or a measured process peak',textures:records,renderTargets:targetRecords,totals:{uniqueTextures:records.length,uniqueRenderTargets:targetSeen.size,assetTextureKnownLogicalBytes:sum(assetRecords.map(r=>r.logicalBytes)),renderTargetTextureKnownLogicalBytes:sum(targetTextureRecords.map(r=>r.logicalBytes)),multisampleColorKnownLogicalBytes:sum(msaaColor),multisampleDepthKnownUpperBytes:sum(msaaDepth),implicitDepthKnownUpperBytes:sum(implicitDepth),conservativeKnownLogicalBytes:sum(records.map(r=>r.logicalBytes))+sum(msaaColor)+sum(msaaDepth)+sum(implicitDepth),unknownTextureCount:records.filter(r=>r.logicalBytes===null).length},rendererReportedMemory:{values:numericMemory,scope:'Three renderer counters as reported; not physical GPU/driver memory'},pngCapture:{width,height,oneRawRGBA8CopyBytes:rawRGBABytes,illustrativeThreeCopyWorkingSetBytes:rawRGBABytes===null?null:rawRGBABytes*3,copyScenario:['canvas/readback RGBA8 staging','encoder or CPU pixel working copy','another browser/compositor copy may coexist'],limitation:'Three-copy scenario is an illustrative budget, not measured peak or guaranteed upper bound; encoded PNG, Blob copies, metadata, driver readback/alignment and outstanding retired resources are additional.'},limitations:['Texture dimensions/formats reflect current loaded/transcoded objects, including compressed-vs-RGBA differences; encoded KTX download bytes are not GPU payload.','Retired/disposed objects retained by drivers, default framebuffer, shader/program storage, geometry/buffers and unlisted internal targets are not included.','Generated mip levels and MSAA/depth storage are logical estimates; padding, allocation granularity, backend repacking and deferred destruction are unknown.','No attribution of a browser crash to a renderer is made.']};
}

// Pure descriptor estimate for targets deliberately not reachable through a
// public renderer API (e.g. WebGLRenderer's internal transmission framebuffer).
// Keep this result separate from resourceSnapshot().renderTargets/totals.
export function estimateRenderTarget({label='unobserved target',width,height,depth=1,faces=1,format=THREE.RGBAFormat,type=THREE.HalfFloatType,samples=0,generateMipmaps=false,depthBuffer=true,stencilBuffer=false,depthType=THREE.UnsignedIntType,hasDepthTexture=false,resolveDepthBuffer=true,storeMultisampledDepthBuffer=true}={}){
 width=positive(width);height=positive(height);depth=positive(depth);faces=positive(faces);samples=Math.max(0,Math.floor(samples||0));
 const sizes=width&&height&&depth?mipDimensions(width,height,depth,false):[];
 const base=bytes(width,height,depth,format,type);const mipBytes=generateMipmaps?sizes.map(s=>bytes(s.width,s.height,s.depth,format,type)):[base];
 const resolvedColorLogicalBytes=faces&&mipBytes.length&&mipBytes.every(Number.isFinite)?sum(mipBytes)*faces:null;
 const multisampleColorLogicalBytes=samples>1&&base!==null?base*faces*samples:0;
 const dp=depthTexelBytes(depthType,stencilBuffer?THREE.DepthStencilFormat:THREE.DepthFormat)??(stencilBuffer?8:4),oneDepth=depthBuffer&&width&&height&&depth&&faces?width*height*depth*faces*dp:0;
 const depthLogicalLowerBytes=depthBuffer?oneDepth*Math.max(1,samples):0;
 const depthLogicalUpperBytes=depthLogicalLowerBytes+(depthBuffer&&samples>1?oneDepth:0);
 return {label,source:'Descriptor estimate only; renderer-private target not observed',width,height,depth,faces,format,formatName:formats.get(format)||'unknown',type,typeName:types.get(type)||'unknown',samples,generateMipmaps,depthBuffer,stencilBuffer,depthType,depthTypeName:types.get(depthType)||'unknown',hasDepthTexture,resolveDepthBuffer,storeMultisampledDepthBuffer,resolvedColorLogicalBytes,multisampleColorLogicalBytes,depthLogicalLowerBytes,depthLogicalUpperBytes,knownLogicalLowerBytes:sum([resolvedColorLogicalBytes,multisampleColorLogicalBytes,depthLogicalLowerBytes]),knownLogicalUpperBytes:sum([resolvedColorLogicalBytes,multisampleColorLogicalBytes,depthLogicalUpperBytes]),complete:resolvedColorLogicalBytes!==null,assumptions:['Caller supplies observed/configured dimensions, format and sample contract; this helper does not inspect or query private renderer state.','Depth range allows sample storage alone through sample storage plus a separate resolved depth allocation.','resolveDepthBuffer/storeMultisampledDepthBuffer describe use/store behavior, not proof that transient storage consumes no allocation.','No driver padding, allocator pooling, retired resize allocations or resident/deferred destruction is measured.']};
}
