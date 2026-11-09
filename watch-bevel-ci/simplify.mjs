import fs from 'node:fs';import {MeshoptSimplifier as S} from './deps/package/meshopt_simplifier.js'; await S.ready;
const read=(p,T)=>{const b=fs.readFileSync('watch-bevel/'+p);return new T(b.buffer,b.byteOffset,b.length/T.BYTES_PER_ELEMENT)};
const p=read('p.bin',Float32Array),a=read('a.bin',Float32Array),ix=read('root-ix.bin',Uint32Array),locks=read('locks.bin',Uint8Array);
for(const e of [.001,.002,.004,.008]){const [out,error]=S.simplifyWithAttributes(ix,p,3,a,5,[.5,.5,.5,.1,.1],locks,0,e,['LockBorder','ErrorAbsolute','RegularizeLight','PreserveFolds']);fs.writeFileSync(`watch-bevel/root-opt-${e}.bin`,out);console.log({e,before:ix.length/3,after:out.length/3,error})}
