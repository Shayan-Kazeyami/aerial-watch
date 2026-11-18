import {createReadbackVideoFrame} from './assembly-video-frame.js';
import {createFrameVideoExporter,videoExportSizes} from './assembly-video-export.js';
import {createVideoExportDialog} from './assembly-video-dialog.js';

export function createOfflineVideoExport({canvas,gl,begin,renderFrame,end,onProgress=()=>{},doc=globalThis.document,win=globalThis.window}={}){
 let disposed=false,choosing=false,progress=null,exporter;
 const dialog=createVideoExportDialog({doc,onCancel:()=>exporter.cancel()});
 const snapshot=createReadbackVideoFrame({canvas,gl,doc});
 exporter=createFrameVideoExporter({canvas,createFrame:(_,metadata)=>snapshot(metadata),
  begin,
  renderFrame,
  end,
  onProgress:value=>{progress=value;dialog.update(value);onProgress(value);},
 });
 const cancel=()=>dialog.cancelChoice()||exporter.cancel(),hidden=()=>{if(doc.hidden)cancel();};
 win.addEventListener('pagehide',cancel);win.addEventListener('resize',cancel);doc.addEventListener('visibilitychange',hidden);
 return {
  get supported(){return typeof globalThis.VideoEncoder==='function'&&typeof globalThis.VideoFrame==='function';},
  get active(){return exporter.active;},
  get progress(){return progress;},
  async start(options){
   if(disposed)throw new Error('The video exporter has closed.');
   if(choosing||exporter.active)throw new Error('A video is already rendering or being prepared.');
   const width=canvas.width,height=canvas.height,sizes=videoExportSizes(width,height);
   choosing=true;
   try{
    const size=options?.size??(sizes.compact?await dialog.choose(sizes):'view');
    if(!size||disposed||canvas.width!==width||canvas.height!==height)throw Object.assign(new Error('Video render cancelled. No video was saved.'),{name:'AbortError'});
    dialog.open({size:sizes[size]});
    return await exporter.start({...options,size});
   }finally{choosing=false;progress=null;if(!disposed)dialog.close();}
  },
  cancel,
  dispose(){if(disposed)return;disposed=true;win.removeEventListener('pagehide',cancel);win.removeEventListener('resize',cancel);doc.removeEventListener('visibilitychange',hidden);exporter.dispose();dialog.dispose();},
 };
}

