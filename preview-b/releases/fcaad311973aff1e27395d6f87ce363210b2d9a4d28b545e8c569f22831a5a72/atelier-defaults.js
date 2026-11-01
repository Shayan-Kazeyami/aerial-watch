// Reviewed presentation defaults. Explicit comparison/compatibility choices win.
export const ATELIER_DEFAULTS=Object.freeze({
 face:'svg04',leather:'craft12',finish:'brushed',crystal:'clear',
 cap:'satin',assets:'meshopt',light:'softbox',antialias:'smaa',
});
export function withAtelierDefaults(href){
 const url=new URL(href);
 for(const [key,value] of Object.entries(ATELIER_DEFAULTS))if(!url.searchParams.has(key))url.searchParams.set(key,value);
 return url;
}
