// A bounded known-size stream sink. Content-Length is a hint, not trusted truth.
export function createByteCollector(expectedBytes,{maxPreallocateBytes=64*1024*1024}={}) {
 let bytes=Number.isSafeInteger(expectedBytes)&&expectedBytes>0&&expectedBytes<=maxPreallocateBytes?new Uint8Array(expectedBytes):null;
 let chunks=bytes?null:[],length=0,peakOwnedBytes=bytes?.byteLength||0,largestChunkBytes=0;
 const initialCapacity=bytes?.byteLength||0;let retainedBytes=initialCapacity;
 return {
  append(value){
   largestChunkBytes=Math.max(largestChunkBytes,value.byteLength);
   if(bytes&&length+value.byteLength<=bytes.byteLength){peakOwnedBytes=Math.max(peakOwnedBytes,bytes.byteLength+value.byteLength);bytes.set(value,length);}
   else {
    if(bytes){chunks=[bytes.subarray(0,length)];bytes=null;}
    chunks.push(value);retainedBytes+=value.byteLength;peakOwnedBytes=Math.max(peakOwnedBytes,retainedBytes);
   }
   length+=value.byteLength;
  },
  finish(){
   let result;
   if(bytes&&length===bytes.byteLength)result=bytes;
   else if(bytes){result=bytes.slice(0,length);peakOwnedBytes=Math.max(peakOwnedBytes,bytes.byteLength+result.byteLength);}
   else {result=new Uint8Array(length);peakOwnedBytes=Math.max(peakOwnedBytes,retainedBytes+length);let offset=0;for(const chunk of chunks){result.set(chunk,offset);offset+=chunk.byteLength;}}
   const metrics={bodyBytes:length,initialCapacity,largestChunkBytes,peakOwnedBytes,avoidedFinalCopy:!!bytes&&length===bytes.byteLength};
   bytes=null;chunks=null;return {buffer:result.buffer,metrics};
  }
 };
}
