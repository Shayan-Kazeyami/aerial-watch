import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
export function verifyThreadTopology(doc,buffer,meshIndex,expectedCount){
 const p=doc.meshes[meshIndex].primitives[0];
 function attribute(id,size){const a=doc.accessors[id],v=doc.bufferViews[a.bufferView],width={5126:4,5125:4,5123:2}[a.componentType];if(!width||v.byteStride)throw Error('Unsupported layout');const start=(v.byteOffset||0)+(a.byteOffset||0);if(start+a.count*size*width>buffer.length)throw Error('Attribute outside buffer');const read=a.componentType===5126?'readFloatLE':a.componentType===5125?'readUInt32LE':'readUInt16LE';return Array.from({length:a.count},(_,i)=>Array.from({length:size},(_,j)=>buffer[read](start+(i*size+j)*width)));}
 const positions=attribute(p.attributes.POSITION,3),raw=attribute(p.indices,1).flat(),canonical=[],vertices=[],lookup=new Map();
 for(const pos of positions){if(!pos.every(Number.isFinite))throw Error('Nonfinite vertex');const key=pos.join(',');if(!lookup.has(key)){lookup.set(key,vertices.length);vertices.push(pos);}canonical.push(lookup.get(key));}
 const parents=vertices.map((_,i)=>i),find=i=>{while(parents[i]!==i){parents[i]=parents[parents[i]];i=parents[i];}return i;},edges=new Map(),faces=[];
 if(raw.length%3)throw Error('Incomplete triangle');
 for(let i=0;i<raw.length;i+=3){const face=raw.slice(i,i+3).map(j=>{if(!Number.isInteger(j)||j<0||j>=positions.length)throw Error('Invalid index');return canonical[j];});if(new Set(face).size!==3)throw Error('Degenerate face');const [a,b,c]=face;const u=vertices[b].map((x,k)=>x-vertices[a][k]),v=vertices[c].map((x,k)=>x-vertices[a][k]);if(Math.hypot(u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0])===0)throw Error('Zero-area face');parents[find(b)]=find(a);parents[find(c)]=find(a);faces.push(face);for(const [x,y]of [[a,b],[b,c],[c,a]]){const key=x<y?x+','+y:y+','+x;const e=edges.get(key)||{count:0,balance:0};e.count++;e.balance+=x<y?1:-1;edges.set(key,e);}}
 for(const e of edges.values())if(e.count!==2||e.balance!==0)throw Error('Open or inconsistently wound edge');
 const components=new Map();for(const [a,b,c]of faces){const key=find(a),va=vertices[a],vb=vertices[b],vc=vertices[c];const volume=(va[0]*(vb[1]*vc[2]-vb[2]*vc[1])+va[1]*(vb[2]*vc[0]-vb[0]*vc[2])+va[2]*(vb[0]*vc[1]-vb[1]*vc[0]))/6;components.set(key,(components.get(key)||0)+volume);}
 if(components.size!==expectedCount)throw Error(`Expected ${expectedCount} stitches, found ${components.size}`);if([...components.values()].some(v=>v<=0))throw Error('Nonpositive stitch volume');return {components:components.size,triangles:faces.length,sourceVertices:positions.length,weldedVertices:vertices.length,minimumVolume:Math.min(...components.values()),closed:true,consistentWinding:true};
}
if(process.argv[1] && path.resolve(process.argv[1])===fileURLToPath(import.meta.url) && process.argv[2]){const root=process.argv[2],doc=JSON.parse(fs.readFileSync(root+'/leather.gltf')),bytes=fs.readFileSync(root+'/geometry.bin');console.log(JSON.stringify([verifyThreadTopology(doc,bytes,1,88),verifyThreadTopology(doc,bytes,3,44)],null,2));}
