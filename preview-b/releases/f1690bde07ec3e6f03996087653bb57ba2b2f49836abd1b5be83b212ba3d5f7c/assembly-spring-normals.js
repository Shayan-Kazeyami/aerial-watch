// Scalar equivalent of indexed BufferGeometry.computeVertexNormals for the
// verified spring mesh. Retains Float32 rounding at each face accumulation.
export function updateSpringNormals(geometry){
 const p=geometry.attributes.position,n=geometry.attributes.normal,index=geometry.index;
 if(!index||p.isInterleavedBufferAttribute||n?.isInterleavedBufferAttribute||p.itemSize!==3||n?.itemSize!==3||!(p.array instanceof Float32Array)||!(n.array instanceof Float32Array)||n.count!==p.count){geometry.computeVertexNormals();return;}
 const pos=p.array,normal=n.array,indices=index.array;normal.fill(0);
 for(let i=0;i<indices.length;i+=3){const a=indices[i]*3,b=indices[i+1]*3,c=indices[i+2]*3;
  const cbx=pos[c]-pos[b],cby=pos[c+1]-pos[b+1],cbz=pos[c+2]-pos[b+2],abx=pos[a]-pos[b],aby=pos[a+1]-pos[b+1],abz=pos[a+2]-pos[b+2];
  const x=cby*abz-cbz*aby,y=cbz*abx-cbx*abz,z=cbx*aby-cby*abx;
  normal[a]+=x;normal[a+1]+=y;normal[a+2]+=z;normal[b]+=x;normal[b+1]+=y;normal[b+2]+=z;normal[c]+=x;normal[c+1]+=y;normal[c+2]+=z;
 }
 for(let i=0;i<normal.length;i+=3){const x=normal[i],y=normal[i+1],z=normal[i+2],inv=1/(Math.sqrt(x*x+y*y+z*z)||1);normal[i]=x*inv;normal[i+1]=y*inv;normal[i+2]=z*inv;}
 n.needsUpdate=true;
}
