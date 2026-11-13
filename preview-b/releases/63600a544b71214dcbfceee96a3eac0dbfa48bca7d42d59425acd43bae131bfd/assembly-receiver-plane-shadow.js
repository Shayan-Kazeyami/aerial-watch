import {ShaderChunk} from './vendor/three.module.js';

// Opt-in diagnostic/candidate for macro self-shadow bands. Keep the map, kernel,
// normal/depth bias, actual occluders and material response unchanged. Compare
// every PCF tap against the receiving plane at the sampled texel's centre,
// rather than comparing all neighbouring texels to the centre fragment depth.
export function receiverPlaneShadowChunk(source=ShaderChunk.shadowmap_pars_fragment){
  if(source.includes('sampler2DShadow shadowMap')&&source.includes('vogelDiskSample'))return receiverPlaneShadowChunk187(source);
  const start=source.indexOf('\tfloat getShadow('),end=source.indexOf('\tvec2 cubeToUV(',start);
  if(start<0||end<0)throw new Error('Receiver-plane shadow: unsupported shader layout');
  let body=source.slice(start,end);
  const anchor='shadowCoord.z += shadowBias;';
  if(!body.includes(anchor))throw new Error('Receiver-plane shadow: missing depth anchor');
  body=body.replace(anchor,`${anchor}
    vec3 receiverDx=dFdx(shadowCoord.xyz), receiverDy=dFdy(shadowCoord.xyz);
    float receiverDet=receiverDx.x*receiverDy.y-receiverDx.y*receiverDy.x;
    vec2 receiverGradient=vec2(0.);
    if(abs(receiverDet)>1.e-16)receiverGradient=vec2(
      receiverDy.y*receiverDx.z-receiverDx.y*receiverDy.z,
      receiverDx.x*receiverDy.z-receiverDy.x*receiverDx.z)/receiverDet;`);
  let count=0;
  body=body.replace(/texture2DCompare\( shadowMap, (.*?), shadowCoord\.z \)/g,(_,uv)=>{
    count++;return `receiverPlaneCompare( shadowMap, ${uv}, shadowCoord, shadowMapSize, receiverGradient )`;
  });
  if(count!==34)throw new Error(`Receiver-plane shadow: expected 34 PCF/basic comparisons, found ${count}`);
  const helper=`
  float receiverPlaneCompare(sampler2D depths,vec2 uv,vec4 centre,vec2 mapSize,vec2 gradient){
    vec2 sampleCentre=(floor(uv*mapSize)+.5)/mapSize;
    float receiverDepth=centre.z+dot(gradient,sampleCentre-centre.xy);
    return texture2DCompare(depths,uv,receiverDepth);
  }
`;
  return source.slice(0,start)+helper+body+source.slice(end);
}
export function installReceiverPlaneShadowStudy(){
 const original=ShaderChunk.shadowmap_pars_fragment,patched=receiverPlaneShadowChunk(original);
 ShaderChunk.shadowmap_pars_fragment=patched;
 return ()=>{if(ShaderChunk.shadowmap_pars_fragment===patched)ShaderChunk.shadowmap_pars_fragment=original;};
}

// r187's PCF uses five Vogel taps, each hardware bilinear (four comparisons).
// Reconstruct those same 20 weighted comparisons explicitly so each corner
// receives its own plane depth, rather than leaving within-tap slope acne.
export function receiverPlaneShadowChunk187(source){
 const start=source.indexOf('float getShadow( sampler2DShadow'),end=source.indexOf('#elif defined( SHADOWMAP_TYPE_VSM )',start);
 if(start<0||end<0)throw new Error('Receiver-plane r187: unsupported shader layout');
 let body=source.slice(start,end),count=0;
 body=body.replace('bool inFrustum =',`vec3 receiverDx=dFdx(shadowCoord.xyz),receiverDy=dFdy(shadowCoord.xyz);
 float receiverDet=receiverDx.x*receiverDy.y-receiverDx.y*receiverDy.x;
 vec2 receiverGradient=vec2(0.);
 if(abs(receiverDet)>1.e-16)receiverGradient=vec2(receiverDy.y*receiverDx.z-receiverDx.y*receiverDy.z,receiverDx.x*receiverDy.z-receiverDy.x*receiverDx.z)/receiverDet;
 bool inFrustum =`);
 body=body.replace(/texture\( shadowMap, vec3\( (shadowCoord\.xy \+ vogelDiskSample\( \d, 5, phi \) \* radius), shadowCoord\.z \) \)/g,(_,uv)=>{count++;return `receiverPlaneCompare187(shadowMap,${uv},shadowCoord,shadowMapSize,receiverGradient)`;});
 if(count!==5)throw new Error('Receiver-plane r187: expected five Vogel taps');
 const helper=`float receiverPlaneTap187(sampler2DShadow depths,vec2 uv,vec4 centre,vec2 gradient){
 return texture(depths,vec3(uv,centre.z+dot(gradient,uv-centre.xy)));
 }
 float receiverPlaneCompare187(sampler2DShadow depths,vec2 uv,vec4 centre,vec2 size,vec2 gradient){
 vec2 p=uv*size-.5,f=fract(p),base=(floor(p)+.5)/size,stepUV=1./size;
 return mix(mix(receiverPlaneTap187(depths,base,centre,gradient),receiverPlaneTap187(depths,base+vec2(stepUV.x,0),centre,gradient),f.x),
 mix(receiverPlaneTap187(depths,base+vec2(0,stepUV.y),centre,gradient),receiverPlaneTap187(depths,base+stepUV,centre,gradient),f.x),f.y);
 }
 `;
 return source.slice(0,start)+helper+body+source.slice(end);
}
