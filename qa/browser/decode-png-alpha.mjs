import {inflateSync}from 'node:zlib';
export function decodePNGAlpha(bytes,points=[]){
 if(bytes.subarray(0,8).toString('hex')!=='89504e470d0a1a0a')throw Error('Not PNG');
 const wanted=new Set(points.map(p=>p.join(','))),samples=[];let width,height,color,depth,interlace;const idat=[];for(let o=8;o+12<=bytes.length;){const n=bytes.readUInt32BE(o),kind=bytes.toString('ascii',o+4,o+8);if(o+n+12>bytes.length)throw Error('Truncated PNG');const d=bytes.subarray(o+8,o+8+n);if(kind==='IHDR'){width=d.readUInt32BE(0);height=d.readUInt32BE(4);depth=d[8];color=d[9];interlace=d[12];}if(kind==='IDAT')idat.push(d);o+=n+12;if(kind==='IEND')break;}
 if(depth!==8||![2,6].includes(color)||interlace!==0)throw Error('Unsupported PNG layout; inspection remains unverified');
 const bpp=color===6?4:3,stride=width*bpp,raw=inflateSync(Buffer.concat(idat));if(raw.length!==(stride+1)*height)throw Error('PNG decoded byte length mismatch');
 let previous=Buffer.alloc(stride),row=Buffer.alloc(stride),mask=Buffer.alloc(Math.ceil(width*height/8)),nonOpaque=0,zeroAlpha=0;const paeth=(a,b,c)=>{const p=a+b-c,pa=Math.abs(p-a),pb=Math.abs(p-b),pc=Math.abs(p-c);return pa<=pb&&pa<=pc?a:pb<=pc?b:c;};
 for(let y=0;y<height;y++){const offset=y*(stride+1),filter=raw[offset];if(filter>4)throw Error('Invalid PNG filter');for(let i=0;i<stride;i++){const a=i>=bpp?row[i-bpp]:0,b=previous[i],c=i>=bpp?previous[i-bpp]:0;row[i]=(raw[offset+1+i]+(filter===0?0:filter===1?a:filter===2?b:filter===3?Math.floor((a+b)/2):paeth(a,b,c)))&255;}
 for(let x=0;x<width;x++){const p=y*width+x,a=bpp===4?row[x*bpp+3]:255;if(wanted.has(x+','+y))samples.push({png:[x,y],rgba:[row[x*bpp],row[x*bpp+1],row[x*bpp+2],a]});if(a!==255){nonOpaque++;mask[p>>3]|=1<<(p&7);}if(a===0)zeroAlpha++;}const tmp=previous;previous=row;row=tmp;}
 return {samples,width,height,pixels:width*height,nonOpaque,zeroAlpha,mask};
}
