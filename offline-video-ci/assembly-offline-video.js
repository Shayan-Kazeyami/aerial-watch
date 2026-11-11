import {createFrameVideoExporter} from './assembly-video-export.js';
import {createVideoExportDialog} from './assembly-video-dialog.js';

export function createOfflineVideoExport({canvas,begin,renderFrame,end,onProgress=()=>{},doc=globalThis.document,win=globalThis.window}={}){
 let disposed=false,progress=null,exporter;
 const dialog=createVideoExportDialog({doc,onCancel:()=>exporter.cancel()});
 exporter=createFrameVideoExporter({canvas,
  begin,
  renderFrame,
  end,
  onProgress:value=>{progress=value;dialog.update(value);onProgress(value);},
 });
 const cancel=()=>exporter.cancel(),hidden=()=>{if(doc.hidden)cancel();};
 win.addEventListener('pagehide',cancel);win.addEventListener('resize',cancel);doc.addEventListener('visibilitychange',hidden);
 return {
  get supported(){return typeof globalThis.VideoEncoder==='function'&&typeof globalThis.VideoFrame==='function';},
  get active(){return exporter.active;},
  get progress(){return progress;},
  async start(options){
   if(disposed)throw new Error('The video exporter has closed.');
   if(exporter.active)return exporter.start(options);
   dialog.open();
   try{return await exporter.start(options);}
   finally{progress=null;if(!disposed)dialog.close();}
  },
  cancel,
  dispose(){if(disposed)return;disposed=true;win.removeEventListener('pagehide',cancel);win.removeEventListener('resize',cancel);doc.removeEventListener('visibilitychange',hidden);exporter.dispose();dialog.dispose();},
 };
}
