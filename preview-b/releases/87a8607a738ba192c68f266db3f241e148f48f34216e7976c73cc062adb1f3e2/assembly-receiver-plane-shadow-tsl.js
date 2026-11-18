// r187 WebGPURenderer/TSL implementation. Caller supplies the same TSL module
// used by its node renderer; never load a second Three instance or GLSL patch.
export function createReceiverPlaneShadowFilter(TSL){
 const {Fn,vec2,vec3,float,texture,reference,renderGroup,dFdx,dFdy,abs,floor,fract,mix,dot,add,interleavedGradientNoise,screenCoordinate,vogelDiskSample}=TSL;
 if(!Fn||!vogelDiskSample||!dFdx)throw new TypeError('r187 TSL shadow API required');
 return Fn(({depthTexture,shadowCoord,shadow,depthLayer})=>{
  const size=reference('mapSize','vec2',shadow).setGroup(renderGroup),radius=reference('radius','float',shadow).setGroup(renderGroup);
  const dx=dFdx(shadowCoord).toVar(),dy=dFdy(shadowCoord).toVar();
  const det=dx.x.mul(dy.y).sub(dx.y.mul(dy.x)).toVar();
  const valid=abs(det).greaterThan(1e-16),safeDet=valid.select(det,float(1));
  const gradient=valid.select(vec2(dy.y.mul(dx.z).sub(dx.y.mul(dy.z)),dx.x.mul(dy.z).sub(dy.x.mul(dx.z))).div(safeDet),vec2(0)).toVar();
  const tap=uv=>{
   let depth=texture(depthTexture,uv);if(depthTexture.isArrayTexture)depth=depth.depth(depthLayer);
   return depth.compare(shadowCoord.z.add(dot(gradient,uv.sub(shadowCoord.xy))));
  };
  const bilinear=uv=>{
   const pixel=uv.mul(size).sub(.5),f=fract(pixel),base=floor(pixel).add(.5).div(size),step=vec2(1).div(size);
   return mix(mix(tap(base),tap(base.add(vec2(step.x,0))),f.x),mix(tap(base.add(vec2(0,step.y))),tap(base.add(step)),f.x),f.y);
  };
  const phi=interleavedGradientNoise(screenCoordinate.xy).mul(6.28318530718),scaled=radius.div(size);
  return add(...Array.from({length:5},(_,i)=>bilinear(shadowCoord.xy.add(vogelDiskSample(i,5,phi).mul(scaled))))).mul(.2);
 });
}
