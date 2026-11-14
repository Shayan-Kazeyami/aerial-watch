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
const credentialKey=/(?:token|secret|password|passwd|pwd|authorization|cookie|api[_-]?key|private[_-]?key|secret[_-]?(?:access[_-]?)?key)$/i;
function redactStructuredDiagnostic(text){
 if(text.length>16000)return '[diagnostic omitted: oversized]';
 const visit=(value,depth)=>{
  if(depth>8)return '[redacted nested diagnostic]';
  if(Array.isArray(value))return value.map(item=>visit(item,depth+1));
  if(value&&typeof value==='object')return Object.fromEntries(Object.entries(value).map(([key,item])=>[key,credentialKey.test(key)?'[redacted]':visit(item,depth+1)]));
  if(typeof value==='string'){
   if(value.length>16000)return '[diagnostic omitted: oversized]';
   try{const nested=JSON.parse(value);if(nested&&typeof nested==='object')return JSON.stringify(visit(nested,depth+1));}catch{}
   const nestedStart=value.indexOf('{');
   if(nestedStart>=0)return value.slice(0,nestedStart)+'[structured diagnostic omitted]';
  }
  return value;
 };
 try{const value=JSON.parse(text);if(value&&typeof value==='object')return JSON.stringify(visit(value,0));}catch{}
 // Prefixed/malformed response bodies may contain nested serialized credentials.
 // Do not guess where that structured body ends: retain only its plain prefix.
 const objectStart=text.indexOf('{');
 if(objectStart>=0)return text.slice(0,objectStart)+'[structured diagnostic omitted]';
 return text;
}
export function sanitizeError(value,{source}={}){return redactStructuredDiagnostic(String(value?.message||value||'Unknown error'))
 // Decode only valid JSON-quoted KEY tokens, never value escapes.
 .replace(/("(?:\\.|[^"\\])*")\s*[:=]/g,(match,key)=>{try{return credentialKey.test(JSON.parse(key))?'"secret":':match;}catch{return match;}})
 .replace(/(?:https?:\/\/|blob:|data:)[^\s)<>"']+/gi,resource=>moduleResource(resource,source))
 .replace(/[^\s]*\?[^\s)]+/g,'[resource query]')
 // Quoted values preserve escaped-string boundaries; unquoted credentials
 // redact the remaining diagnostic conservatively (spaces, cookies and folds).
 .replace(/["']?\b(?:[A-Za-z0-9]+[_-])*(?:token|secret|password|passwd|pwd|authorization|proxy[_-]?authorization|cookie|set[_-]?cookie|api[_-]?key|private[_-]?key|secret[_-]?(?:access[_-]?)?key|(?:access|refresh|session|client|id|auth)[_-]?(?:token|secret|key))["']?\s*[:=]\s*(?:"(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*'|[\s\S]*)/gi,'[redacted]')
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
