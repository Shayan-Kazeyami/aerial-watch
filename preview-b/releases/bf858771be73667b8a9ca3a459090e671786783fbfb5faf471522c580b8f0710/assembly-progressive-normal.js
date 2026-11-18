// Private study: validate both segments before reconstructing the exact audited KTX.
const LOW_BYTES=4389472, HIGH_BYTES=12172852, HEADER_BYTES=584, LOW_HEADER_BYTES=560;
const LOW_SHA='5d8aa10702589424c1157d9a58a7f75aca265569d7c8fac09525a00af19455bc';
const FULL_SHA='bb022255b999645d468cc2b62100cef7c4226c3df136ab1732b40c107655d585';
const hex=bytes=>Array.from(new Uint8Array(bytes),x=>x.toString(16).padStart(2,'0')).join('');
const digest=async(bytes,cryptoImpl)=>hex(await cryptoImpl.subtle.digest('SHA-256',bytes));
export async function verifyLowNormal(low,{cryptoImpl=globalThis.crypto}={}) {
 if(!(low instanceof Uint8Array)||low.byteLength!==LOW_BYTES)throw Error('Low normal length mismatch');
 if(await digest(low,cryptoImpl)!==LOW_SHA)throw Error('Low normal identity mismatch');
 return low;
}
export async function reconstructNormal({low,high,header,cryptoImpl=globalThis.crypto}){
 await verifyLowNormal(low,{cryptoImpl});
 if(!(high instanceof Uint8Array)||high.byteLength!==HIGH_BYTES)throw Error('High normal length mismatch');
 if(!(header instanceof Uint8Array)||header.byteLength!==HEADER_BYTES)throw Error('Header length mismatch');
 const full=new Uint8Array(HEADER_BYTES+LOW_BYTES-LOW_HEADER_BYTES+HIGH_BYTES);
 full.set(header);full.set(low.subarray(LOW_HEADER_BYTES),HEADER_BYTES);full.set(high,HEADER_BYTES+LOW_BYTES-LOW_HEADER_BYTES);
 if(await digest(full,cryptoImpl)!==FULL_SHA)throw Error('Full normal identity mismatch');
 return full;
}
// Avoid an extra 12 MB concatenation during full-resolution reconstruction.
export async function reconstructNormalSegments({low,header,part0,part1,cryptoImpl=globalThis.crypto}){
 await verifyLowNormal(low,{cryptoImpl});
 if(!(header instanceof Uint8Array)||header.byteLength!==HEADER_BYTES)throw Error('Header length mismatch');
 if(!(part0 instanceof Uint8Array)||part0.byteLength!==8388608||!(part1 instanceof Uint8Array)||part1.byteLength!==3784244)throw Error('High segment length mismatch');
 const full=new Uint8Array(HEADER_BYTES+LOW_BYTES-LOW_HEADER_BYTES+part0.length+part1.length);
 full.set(header);full.set(low.subarray(LOW_HEADER_BYTES),HEADER_BYTES);let off=HEADER_BYTES+LOW_BYTES-LOW_HEADER_BYTES;full.set(part0,off);off+=part0.length;full.set(part1,off);
 if(await digest(full,cryptoImpl)!==FULL_SHA)throw Error('Full normal identity mismatch');return full;
}
