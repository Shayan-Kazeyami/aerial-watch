// Reviewed presentation defaults. Explicit comparison/compatibility choices win.
export const ATELIER_DEFAULTS=Object.freeze({
 face:'svg04',leather:'craft14',finish:'brushed',crystal:'clear',
 cap:'satin',assets:'meshopt',light:'softbox',antialias:'smaa',quality:'studio',tickBatch:'1',
});
// Touch phones start with the motion-first budget; explicit quality choices win.
export function defaultRenderQuality(environment=globalThis){
 const coarse=environment.matchMedia?.('(pointer: coarse)')?.matches;
 const narrow=environment.matchMedia?.('(max-width: 900px)')?.matches;
 return coarse&&narrow?'efficient':ATELIER_DEFAULTS.quality;
}
export function withAtelierDefaults(href,environment=globalThis){
 const url=new URL(href);
 for(const [key,value] of Object.entries(ATELIER_DEFAULTS))if(!url.searchParams.has(key))url.searchParams.set(key,key==='quality'?defaultRenderQuality(environment):value);
 // Only the motion-first R14 path opts into progressive delivery by default.
 // Explicit study/compatibility choices, including normalStream=0, always win.
 if(!url.searchParams.has('normalStream')&&url.searchParams.get('leather')==='craft14'&&url.searchParams.get('quality')==='efficient')url.searchParams.set('normalStream','1');
 return url;
}
