const percentile=(values,q)=>values.length?values[Math.min(values.length-1,Math.floor(values.length*q))]:null;
export function createPerformanceMonitor({capacity=3600,now=()=>performance.now()}={}) {
  const costs=[],cadence=[],loads=[];let lastFrame=null,totalFrames=0,firstInteractiveMs=null,measurementStart=now();
  return {
    load(metrics){loads.push({...metrics});},
    interactive(ms){if(firstInteractiveMs===null)firstInteractiveMs=ms;},
    frame({timestamp,cpuMs,drawCalls,triangles,geometries,textures}) {
      if(lastFrame!==null)cadence.push(timestamp-lastFrame);lastFrame=timestamp;costs.push(cpuMs);totalFrames++;
      if(costs.length>capacity)costs.shift();if(cadence.length>capacity)cadence.shift();
      this.renderer={drawCalls,triangles,geometries,textures};
    },
    breakCadence(){lastFrame=null;},
    reset(){costs.length=cadence.length=0;lastFrame=null;totalFrames=0;measurementStart=now();this.renderer=null;},
    snapshot(){const cpu=[...costs].sort((a,b)=>a-b),intervals=[...cadence].sort((a,b)=>a-b);
      return {loads:loads.map(value=>({...value})),firstInteractiveMs,totalFrames,sampledFrames:costs.length,measurementDurationMs:now()-measurementStart,
        cpuFrameMs:{median:percentile(cpu,.5),p95:percentile(cpu,.95),max:cpu.at(-1)??null},
        renderedIntervalMs:{median:percentile(intervals,.5),p95:percentile(intervals,.95)},renderer:this.renderer||null,
        measurementNotes:'CPU includes motion/camera preparation and render submission; GPU time unavailable. Body bytes measure decoded HTTP response bytes, not cold/warm network transfer. Render intervals include on-demand idle gaps unless reset. Physical phone measurements are not inferred.'};},
  };
}
