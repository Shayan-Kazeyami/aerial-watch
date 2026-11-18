// Validate decoded lining maps: GLTFLoader may resolve a failed image as null.
export function hasCompleteLining(gltf){
 let found=false,complete=true;
 gltf?.scene?.traverse(mesh=>{if(!mesh?.isMesh)return;for(const m of(Array.isArray(mesh.material)?mesh.material:[mesh.material])){if(m?.name?.startsWith('lining /')){found=true;if(!m.map||!m.normalMap||!m.roughnessMap)complete=false;}}});
 return found&&complete;
}
export async function loadWithLiningFallback({loadVariant,loadBaseline,validate=hasCompleteLining,dispose,signal,skipVariant=false}){
 signal?.throwIfAborted();let valid;
 if(!skipVariant){const candidate=await loadVariant();if(signal?.aborted){dispose(candidate);signal.throwIfAborted();}try{valid=validate(candidate.gltf)}catch(error){dispose(candidate);throw error;}if(valid)return {result:candidate,used:'variant'};dispose(candidate);signal?.throwIfAborted();}
 const baseline=await loadBaseline();if(signal?.aborted){dispose(baseline);signal.throwIfAborted();}try{valid=validate(baseline.gltf)}catch(error){dispose(baseline);throw error;}if(!valid){dispose(baseline);throw new Error('Lining textures unavailable in both optimized and original assets.');}
 return {result:baseline,used:'baseline',fallbackReason:skipVariant?'AVIF decoder unavailable or probe timed out.':'Optimized lining textures did not decode completely.'};
}
