/** Own browser download URLs long enough for slow download handlers to consume them. */
export function createDownloadManager({document:doc=globalThis.document,urlAPI=URL,setTimer=setTimeout,clearTimer=clearTimeout,lifetimeMs=60000}={}){
 const pending=new Map();let disposed=false;
 const release=url=>{const timer=pending.get(url);if(timer!==undefined)clearTimer(timer);pending.delete(url);urlAPI.revokeObjectURL(url);};
 return {
  get pendingCount(){return pending.size;},
  save(blob,name){
   if(disposed)throw new Error('Download manager is closed.');
   const link=doc.createElement('a'),url=urlAPI.createObjectURL(blob);
   link.href=url;link.download=name;link.hidden=true;
   try{
    doc.body.append(link);
    pending.set(url,setTimer(()=>release(url),lifetimeMs));
    link.click();
   }catch(error){if(pending.has(url))release(url);else urlAPI.revokeObjectURL(url);throw error;}finally{link.remove();}
   return {requested:true,name};
  },
  dispose(){if(disposed)return;disposed=true;for(const url of [...pending.keys()])release(url);},
 };
}
