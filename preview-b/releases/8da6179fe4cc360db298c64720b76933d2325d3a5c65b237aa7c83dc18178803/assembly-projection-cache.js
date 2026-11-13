// Cache screen-space work only while all projection inputs are exactly unchanged.
// No tolerance: even a subpixel transform or viewport shift invalidates the result.
export function createProjectionCache(compute) {
  let source=null, values=null, result='';
  const metrics={computations:0,hits:0};
  return {
    get(vertices,world,view,projection,rect) {
      const matrices=[world.elements,view.elements,projection.elements];
      const viewport=[rect.left,rect.top,rect.width,rect.height];
      let same=source===vertices&&values!==null,k=0;
      for(const matrix of matrices)for(const n of matrix){if(!values||values[k]!==n)same=false;k++;}
      for(const n of viewport){if(!values||values[k]!==n)same=false;k++;}
      if(same){metrics.hits++;return result;}
      source=vertices;values??=new Float64Array(52);k=0;
      for(const matrix of matrices)for(const n of matrix)values[k++]=n;
      for(const n of viewport)values[k++]=n;
      result=compute(vertices,rect);metrics.computations++;return result;
    },
    clear(){source=null;values=null;result='';},
    snapshot(){return {...metrics};}
  };
}
