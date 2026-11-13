// Private CPU-side proof: no renderer upload, GPU accounting or app integration.
// The caller must track/dispose old and replacement textures and own the swap.
export function stageNormalSwap({materials,oldTexture,fullTexture}) {
 if(!oldTexture?.isCompressedTexture||!fullTexture?.isCompressedTexture)throw Error('Compressed textures required');
 if(oldTexture.format!==fullTexture.format||oldTexture.type!==fullTexture.type)throw Error('GPU format mismatch');
 if(!Array.isArray(materials)||!materials.length||new Set(materials).size!==materials.length||materials.some(m=>m.normalMap!==oldTexture))throw Error('Unexpected normal-map bindings');
 if(oldTexture.image?.width!==2048||oldTexture.image?.height!==2048||oldTexture.mipmaps?.length!==12)throw Error('Unexpected initial normal dimensions');
 if(fullTexture.image?.width!==4096||fullTexture.image?.height!==4096||fullTexture.mipmaps?.length!==13)throw Error('Unexpected full normal dimensions');
 const replacement=oldTexture.clone();replacement.source=fullTexture.source;replacement.mipmaps=fullTexture.mipmaps;replacement.needsUpdate=true;
 let state='staged';
 return {replacement,commit(){if(state!=='staged')throw Error('Swap already settled');let updated=0;try{for(const m of materials){if(m.normalMap!==oldTexture)throw Error('Normal binding changed');m.normalMap=replacement;updated++;}state='committed';}catch(error){for(let i=0;i<updated;i++)materials[i].normalMap=oldTexture;state='failed';replacement.dispose();throw error;}},cancel(){if(state==='staged'){state='cancelled';replacement.dispose();}},get state(){return state;}};
}
