import * as THREE from './vendor/three.module.js';
import {FullScreenQuad} from './vendor/postprocessing/Pass.js';
import {overscanPlan,withExpandedProjection,resolveTransmissionResolution} from './assembly-overscan.js';
import {guardGPUMaterials} from './assembly-renderer.js';

export async function createGPUScenePipeline({renderer,scene,camera,GPU,identity,smaaRequested=false}){
  const TSL=await import('./vendor/three.tsl.js');
  const [{ssao},{bloom:makeBloom},{smaa:makeSMAA}]=await Promise.all([import('./vendor/tsl/display/SSAONode.js'),import('./vendor/tsl/display/BloomNode.js'),import('./vendor/tsl/display/SMAANode.js')]);
  const prepass=TSL.pass(scene,camera,{samples:0});prepass.transparent=false;
  prepass.setMRT(TSL.mrt({output:TSL.normalView}));
  const aoNode=ssao(prepass.getTextureNode('depth'),prepass.getTextureNode(),camera);
  aoNode.resolutionScale=1;aoNode.samples.value=24;aoNode.radius.value=1.2;
  const aoStrength=TSL.uniform(1),bloomStrength=TSL.uniform(0);
  // Match native WebGL's resolved transmission buffer so glass does not
  // magnify unsampled dial edges. This is independent of beauty/SMAA samples.
  // Hardware WebGPU retains its existing policy pending actual adapter QA.
  const transmissionSamples=renderer.backend?.isWebGLBackend?Math.min(4,renderer.capabilities?.maxSamples??4):0;
  const transmissionPass=TSL.pass(scene,camera,{samples:transmissionSamples});transmissionPass.transparent=false;
  transmissionPass.renderTarget.texture.generateMipmaps=true;
  transmissionPass.renderTarget.texture.minFilter=THREE.LinearMipmapLinearFilter;
  renderer.aerialTransmissionNode=transmissionPass.getTextureNode();
  // PassNode.setup()/compileAsync() restore options.samples into the target.
  // Keep the declared option and live target aligned with the existing AA policy.
  const scenePass=TSL.pass(scene,camera,{samples:smaaRequested?0:Math.min(4,renderer.capabilities?.maxSamples??4)});
  const setSamples=samples=>{
    scenePass.options.samples=samples;
    if(scenePass.renderTarget.samples!==samples){scenePass.renderTarget.samples=samples;scenePass.renderTarget.dispose();}
  };
  setSamples(scenePass.options.samples);
  // AO participates in opaque shading before the renderer captures transmission,
  // so sapphire refracts the AO together with the opaque scene, not a screen overlay.
  scenePass.contextNode=TSL.builtinAOContext(TSL.mix(1,aoNode.getTextureNode().sample(TSL.screenUV).r,aoStrength));
  transmissionPass.contextNode=scenePass.contextNode;
  const color=scenePass.getTextureNode();const bloomNode=makeBloom(color,.07,.25,1.8);
  let output=color.add(bloomNode.mul(bloomStrength));
  const smaa=smaaRequested?makeSMAA(output):null;if(smaa)output=smaa;
  const crop=TSL.uniform(new THREE.Vector2(1,1)),offset=TSL.uniform(new THREE.Vector2());
  const outputTexture=TSL.convertToTexture(output);
  const pipeline=new GPU.RenderPipeline(renderer,outputTexture.sample(TSL.uv().mul(crop).add(offset)));
  let plan;
  for(const pass of [prepass,scenePass,aoNode,bloomNode,...(smaa?[smaa]:[])]){const native=pass.setSize.bind(pass);pass.setSize=(w,h)=>native(plan?.renderWidth||w,plan?.renderHeight||h);}
  const transmissionSize=transmissionPass.setSize.bind(transmissionPass);
  transmissionPass.setSize=(w,h)=>{const scale=renderer.transmissionResolutionScale??1;transmissionSize(Math.floor((plan?.renderWidth||w)*scale),Math.floor((plan?.renderHeight||h)*scale));};
  let effectsWarmed=false;
  const syncEffects=()=>{
    prepass.updateBeforeType=aoNode.updateBeforeType=effectsWarmed&&aoStrength.value===0?TSL.NodeUpdateType.NONE:TSL.NodeUpdateType.FRAME;
    bloomNode.updateBeforeType=effectsWarmed&&bloomStrength.value===0?TSL.NodeUpdateType.NONE:TSL.NodeUpdateType.FRAME;
  };
  const ao={get enabled(){return aoStrength.value===1;},set enabled(v){aoStrength.value=v?1:0;syncEffects();},get kernelRadius(){return aoNode.radius.value;},set kernelRadius(v){aoNode.radius.value=v;},dispose(){aoNode.dispose();},_overrideVisibility(){},_visibilityCache:[]};
  const bloom={get enabled(){return bloomStrength.value===1;},set enabled(v){bloomStrength.value=v?1:0;syncEffects();},dispose(){bloomNode.dispose();}};
  const composer={renderTarget1:scenePass.renderTarget,renderTarget2:scenePass.renderTarget,passes:[bloom,...(smaa?[smaa]:[])],setSize(){},setPixelRatio(){},dispose(){prepass.dispose();transmissionPass.dispose();scenePass.dispose();pipeline.dispose();outputTexture.dispose?.();if(smaa?.textureNode?.isRTTNode)smaa.textureNode.dispose();},render(){guardGPUMaterials(scene,identity);pipeline.render();effectsWarmed=true;syncEffects();}};
  composer.aerialGPU={effects:{prepass,scenePass,aoNode,bloomNode},setSamples,syncEffects:()=>{effectsWarmed=true;syncEffects();},gpuRender:composer.render.bind(composer),gpuResize(p){plan=p;for(const target of [outputTexture,smaa?.textureNode])if(target?.isRTTNode){target.width=p.renderWidth;target.height=p.renderHeight;target.setSize(p.renderWidth,p.renderHeight);}crop.value.fromArray(p.crop);offset.value.fromArray(p.offset);}};
  composer.aerialTargets=()=>[
    {name:'opaque normal/depth prepass',target:prepass.renderTarget},{name:'opaque transmission',target:transmissionPass.renderTarget},{name:'beauty',target:scenePass.renderTarget},
    {name:'SSAO output',target:aoNode._aoRenderTarget},{name:'SSAO blur',target:aoNode._blurRenderTarget},
    {name:'bloom bright',target:bloomNode._renderTargetBright},
    ...bloomNode._renderTargetsHorizontal.map((target,i)=>({name:`bloom horizontal ${i}`,target})),...bloomNode._renderTargetsVertical.map((target,i)=>({name:`bloom vertical ${i}`,target})),
    ...(smaa?[{name:'SMAA edges',target:smaa._renderTargetEdges},{name:'SMAA weights',target:smaa._renderTargetWeights},{name:'SMAA blend',target:smaa._renderTargetBlend},{name:'color+bloom combine (r03 original)',target:smaa.textureNode.renderTarget}]:[])
    ,{name:'final output RTT (r03 original)',target:outputTexture.renderTarget}
  ];
  identity.postprocessing={ao:'r187 SSAONode built-in lighting context; not pixel-identical legacy SSAOPass',bloom:'r187 BloomNode',antialias:smaa?'r187 SMAANode':'MSAA',disabledEffects:'One initialization frame; then NONE update type suppresses inactive AO/prepass/bloom passes'};
  return {composer,ao,bloom,smaa,aoShadowReuse:null};
}

export function installOverscan({renderer,composer,scene,camera,identity,gpuRender,gpuResize,margin=.12}){
  let width=1,height=1,ratio=renderer.getPixelRatio(),plan;
  const nativeRender=composer.render.bind(composer),nativeSetSize=composer.setSize.bind(composer),nativeSetRatio=composer.setPixelRatio.bind(composer);
  let material,quad;
  if(!gpuRender){
    composer.renderToScreen=false;
    // Must run before replacing setSize: real EffectComposer.setPixelRatio calls this.setSize.
    nativeSetRatio(1);
    material=new THREE.ShaderMaterial({uniforms:{tDiffuse:{value:null},crop:{value:new THREE.Vector2(1,1)},offset:{value:new THREE.Vector2()}},vertexShader:'varying vec2 vUv;void main(){vUv=uv;gl_Position=vec4(position.xy,0.,1.);}',fragmentShader:'uniform sampler2D tDiffuse;uniform vec2 crop;uniform vec2 offset;varying vec2 vUv;void main(){gl_FragColor=texture2D(tDiffuse,vUv*crop+offset);}',depthTest:false,depthWrite:false,toneMapped:false});
    quad=new FullScreenQuad(material);
  }
  function resize(){
    const transmissionRequest=renderer.aerialTransmissionRequest||{scale:renderer.transmissionResolutionScale??1,maxPixels:Infinity};
    plan=overscanPlan({width,height,pixelRatio:ratio,margin,maxTextureSize:renderer.capabilities.maxTextureSize,transmissionScale:transmissionRequest.scale,budgetBytes:Math.max(384*1024*1024,Math.floor(width*ratio)*Math.floor(height*ratio)*192+128*1024*1024)});identity.overscan={...plan,budgetPolicy:'Existing quality-profile base allocation plus at most 128 MiB extra above 384 MiB; conservative estimate, not measured GPU memory.'};
    const transmission=resolveTransmissionResolution({renderWidth:plan.renderWidth,renderHeight:plan.renderHeight,requestedScale:transmissionRequest.scale,maxPixels:transmissionRequest.maxPixels,maxTextureSize:renderer.capabilities.maxTextureSize});
    renderer.transmissionResolutionScale=transmission.effectiveScale;
    identity.transmission={...transmission,revision:'expanded-target-budget-v1',scope:gpuRender?'dedicated opaque-only mipmapped node transmission target':'independent WebGL transmission target'};
    if(gpuResize){gpuResize(plan);}
    else{nativeSetSize(plan.renderWidth,plan.renderHeight);material.uniforms.crop.value.fromArray(plan.crop);material.uniforms.offset.value.fromArray(plan.offset);}
  }
  composer.setPixelRatio=value=>{ratio=value;resize();};composer.setSize=(w,h)=>{width=w;height=h;resize();};
  composer.render=()=>{
    if(!plan)resize();
    if(gpuRender){
      withExpandedProjection(camera,plan,()=>gpuRender(),{background:scene?.background});
    }else{
      const syncProjection=()=>{for(const pass of composer.passes)for(const material of [pass.ssaoMaterial,pass.depthRenderMaterial]){const u=material?.uniforms;u?.cameraProjectionMatrix?.value.copy(camera.projectionMatrix);u?.cameraInverseProjectionMatrix?.value.copy(camera.projectionMatrixInverse);}};
      try{withExpandedProjection(camera,plan,()=>{syncProjection();nativeRender();},{background:scene?.background});}finally{syncProjection();}
      material.uniforms.tDiffuse.value=composer.readBuffer.texture;
      const old=renderer.getRenderTarget();renderer.setRenderTarget(null);quad.render(renderer);renderer.setRenderTarget(old);
    }
  };
  const dispose=composer.dispose.bind(composer);composer.dispose=()=>{dispose();material?.dispose();quad?.dispose();};
  if(!composer.aerialTargets)composer.aerialTargets=()=>{
    const entries=[{name:'composer first',target:composer.renderTarget1},{name:'composer second',target:composer.renderTarget2}];
    for(const pass of composer.passes)for(const [key,value]of Object.entries(pass)){
      if(value?.isRenderTarget)entries.push({name:`${pass.constructor.name}.${key}`,target:value});
      else if(Array.isArray(value))value.forEach((target,i)=>{if(target?.isRenderTarget)entries.push({name:`${pass.constructor.name}.${key}[${i}]`,target});});
    }
    return entries;
  };
  return ()=>({...plan});
}
