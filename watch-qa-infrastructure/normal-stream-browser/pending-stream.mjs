// Observe native reader acquisition/read without changing loader source.
export function pendingStreamFixture(){
 let signalRead;const pendingRead=new Promise(r=>signalRead=r);
 const state={acquired:0,readCalls:0,pending:false,cancelled:false,released:0};
 const stream=new ReadableStream({pull(){},cancel(){state.cancelled=true}});
 const acquire=stream.getReader.bind(stream);
 stream.getReader=(...args)=>{const reader=acquire(...args);state.acquired++;return {
  read(){state.readCalls++;state.pending=true;const result=reader.read();signalRead();return result.finally(()=>{state.pending=false})},
  cancel(reason){return reader.cancel(reason)},
  releaseLock(){state.released++;return reader.releaseLock()}
 }};
 return {stream,state,pendingRead};
}
