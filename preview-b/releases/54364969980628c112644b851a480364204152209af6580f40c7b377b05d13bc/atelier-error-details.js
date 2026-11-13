// Local, bounded diagnostics only: no telemetry, arbitrary options or URL export.
function moduleResource(resource,source){
 try{
  const url=new URL(resource),base=new URL(source);
  if(!['http:','https:'].includes(url.protocol)||url.origin!==base.origin||url.username||url.password)return '[resource]';
  const sealed=base.pathname.match(/^(.*\/releases\/)[a-f0-9]{64}\//);
  const prefix=sealed?sealed[1]:new URL('.',base).pathname;
  if(!url.pathname.startsWith(prefix))return '[resource]';
  const module=url.pathname.slice(prefix.length);
  if(!/^[A-Za-z0-9_-][A-Za-z0-9_.-]*(?:\/[A-Za-z0-9_-][A-Za-z0-9_.-]*)*\.m?js$/.test(module))return '[resource]';
  if(sealed&&!/^[a-f0-9]{64}\//.test(module))return '[resource]';
  return `[module ${module}]`;
 }catch{return '[resource]';}
}
export function sanitizeError(value,{source}={}){return String(value?.message||value||'Unknown error')
 .replace(/(?:https?:\/\/|blob:|data:)[^\s)<>"']+/gi,resource=>moduleResource(resource,source))
 .replace(/[^\s]*\?[^\s)]+/g,'[resource query]')
 .replace(/\b(?:token|secret|password|authorization|cookie|api[_-]?key)\s*[:=]\s*[^\s,;]+/gi,'[redacted]')
 .replace(/[\x00-\x1f\x7f<>]/g,' ').replace(/\s+/g,' ').trim().slice(0,220);}
const names={baseline:'Watch assembly',proposal:'Open-work plates',premiumFace:'Selected dial',leather:'Selected leather',antialias:'Antialiasing',runtime:'3D runtime'};
const allowed={face:['svg04','svg03','svg'],leather:['compat12','craft14','craft12','craft11','craft10','craft9'],finish:['brushed','studio4','atelier2','atelier3'],crystal:['clear'],cap:['satin'],assets:['meshopt','raw'],light:['softbox','studio4','atelier2','atelier3'],antialias:['smaa'],quality:['studio','detail','balanced','efficient']};
export function errorDetails({state={},error,search='',source='',capabilities={}}={}){
 const active=!!error||['asset-error','error','degraded'].includes(state.phase);
 if(!active)return null;
 const failures=(Array.isArray(state.warnings)?state.warnings:[]).slice(0,8).map(w=>({asset:names[w.asset]||'Watch asset',reason:sanitizeError(w.message,{source})}));
 if(error||!failures.length)failures.push({asset:'3D runtime',reason:sanitizeError(error||state.message,{source})});
 const options={},params=new URLSearchParams(search);for(const [key,values]of Object.entries(allowed)){const value=params.get(key);if(values.includes(value))options[key]=value;}
 const release=String(source).match(/\/releases\/([a-f0-9]{64})\//)?.[1]||'root development';
 const caps={};for(const key of ['webglApiPresent','webgl2ApiPresent','secureContext'])if(typeof capabilities[key]==='boolean')caps[key]=capabilities[key];
 const report={format:'aerial-error-v1',source:release,phase:['asset-error','error','degraded'].includes(state.phase)?state.phase:'error',failures,options,capabilities:caps};
 return {summary:failures.map(f=>`${f.asset}: ${f.reason}`).join('\n'),text:JSON.stringify(report,null,2)};
}
export async function copyErrorDetails(text,{clipboard,showFallback=()=>{}}={}){
 try{if(typeof clipboard?.writeText!=='function')throw new Error('Clipboard unavailable');await clipboard.writeText(text);return true;}
 catch{showFallback(text);return false;}
}
