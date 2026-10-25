import {Color,CustomBlending,FrontSide,HalfFloatType,NearestFilter,NoBlending,ShaderMaterial,Vector2,WebGLRenderTarget} from './vendor/three.module.js';
import {ASSEMBLY_REFRACTION_COVERAGE_GLSL} from './assembly-refraction.js';

// The opaque depth pass sees the original bore/screw position. Sapphire moves
// its colour in screen space. Multiplying unwarped AO over that colour makes
// a second dark outline. Record the visible glass's transmission UV and sample
// the AO field there too; geometry, IOR, thickness and ordinary AO stay intact.
export function createRefractionAwareAO({pass,scene,camera,getCrystals}){
  const mask=new WebGLRenderTarget(1,1,{type:HalfFloatType,minFilter:NearestFilter,magFilter:NearestFilter});
  const materials=new Map(),originalRenderPass=pass._renderPass,clearColor=new Color();
  let disposed=false;
  const composite=pass.copyMaterial.clone();
  composite.uniforms={tDiffuse:{value:null},tGlassUV:{value:mask.texture}};
  composite.fragmentShader=`uniform sampler2D tDiffuse;uniform sampler2D tGlassUV;varying vec2 vUv;
    void main(){vec4 glass=texture2D(tGlassUV,vUv);vec2 uv=glass.a>.5?vUv+glass.rg:vUv;
      vec4 ao=texture2D(tDiffuse,clamp(uv,vec2(0.),vec2(1.)));
      // Outside the captured viewport colour falls back to its original UV;
      // its contact shadow must follow the same bounded fallback.
      vec4 entryAO=texture2D(tDiffuse,vUv);
      gl_FragColor=mix(ao,entryAO,glass.a*(1.-glass.b));}`;
  function materialFor(mesh){
    if(!materials.has(mesh))materials.set(mesh,new ShaderMaterial({
      uniforms:{opaqueDepth:{value:null},resolution:{value:new Vector2()},transmissionSize:{value:new Vector2()},thickness:{value:0},ior:{value:1.76}},
      vertexShader:`varying vec3 worldPosition;varying vec3 viewNormal;varying vec3 modelScale;
        void main(){worldPosition=(modelMatrix*vec4(position,1.)).xyz;viewNormal=normalize(normalMatrix*normal);
          modelScale=vec3(length(modelMatrix[0].xyz),length(modelMatrix[1].xyz),length(modelMatrix[2].xyz));
          gl_Position=projectionMatrix*viewMatrix*vec4(worldPosition,1.);}`,
      fragmentShader:`uniform sampler2D opaqueDepth;uniform vec2 resolution;uniform vec2 transmissionSize;uniform float thickness;uniform float ior;uniform mat4 projectionMatrix;
        varying vec3 worldPosition;varying vec3 viewNormal;varying vec3 modelScale;
        ${ASSEMBLY_REFRACTION_COVERAGE_GLSL}
        void main(){vec2 pixelUV=gl_FragCoord.xy/resolution;
          if(gl_FragCoord.z>texture2D(opaqueDepth,pixelUV).x+.0000001)discard;
          vec3 n=normalize((vec4(normalize(viewNormal),0.)*viewMatrix).xyz);
          vec3 v=normalize(cameraPosition-worldPosition);
          vec3 ray=normalize(refract(-v,n,1./ior))*thickness*modelScale;
          vec4 exitClip=projectionMatrix*viewMatrix*vec4(worldPosition+ray,1.);
          vec2 sampleUV=exitClip.xy/exitClip.w*.5+.5;
          gl_FragColor=vec4(sampleUV-pixelUV,assemblyRefractionCoverage(sampleUV,transmissionSize,exitClip.w,pixelUV),1.);}`,
      side:FrontSide,depthTest:true,depthWrite:true,blending:NoBlending,toneMapped:false,
    }));
    return materials.get(mesh);
  }
  function renderUV(renderer,crystals){
    const width=Math.max(1,Math.floor(pass.width)),height=Math.max(1,Math.floor(pass.height));
    if(mask.width!==width||mask.height!==height)mask.setSize(width,height);
    const target=renderer.getRenderTarget(),alpha=renderer.getClearAlpha(),autoClear=renderer.autoClear;
    const background=scene.background,override=scene.overrideMaterial,shadowAuto=renderer.shadowMap.autoUpdate;
    renderer.getClearColor(clearColor);const color=clearColor.clone(),hidden=[],swapped=[];
    const keep=new Set(crystals);
    try{
      scene.traverse(object=>{if((object.isMesh||object.isPoints||object.isLine)&&object.visible&&!keep.has(object)){hidden.push(object);object.visible=false;}});
      for(const mesh of crystals){const source=mesh.material,material=materialFor(mesh);swapped.push([mesh,source]);
        material.uniforms.opaqueDepth.value=pass.normalRenderTarget.depthTexture;
        material.uniforms.resolution.value.set(width,height);
        // The colour pass uses the renderer's independently budgeted sapphire
        // buffer. Coverage must use that size, not the AO target's size.
        const size=renderer.getDrawingBufferSize?.(new Vector2())||new Vector2(width,height);
        material.uniforms.transmissionSize.value.copy(size).multiplyScalar(renderer.transmissionResolutionScale??1).floor();
        material.uniforms.thickness.value=source.thickness;material.uniforms.ior.value=source.ior;
        mesh.material=material;}
      scene.background=null;scene.overrideMaterial=null;renderer.shadowMap.autoUpdate=false;
      renderer.autoClear=false;renderer.setRenderTarget(mask);renderer.setClearColor(0,0);renderer.clear();renderer.render(scene,camera);
    }finally{
      swapped.forEach(([mesh,material])=>mesh.material=material);hidden.forEach(object=>object.visible=true);
      scene.background=background;scene.overrideMaterial=override;renderer.shadowMap.autoUpdate=shadowAuto;
      renderer.setRenderTarget(target);renderer.setClearColor(color,alpha);renderer.autoClear=autoClear;
    }
  }
  const wrapped=function(renderer,material,...args){
    if(disposed||material!==pass.copyMaterial||material.blending!==CustomBlending)return originalRenderPass.call(pass,renderer,material,...args);
    const crystals=getCrystals().filter(mesh=>mesh.visible&&!Array.isArray(mesh.material)&&mesh.material.transmission>0);
    if(!crystals.length)return originalRenderPass.call(pass,renderer,material,...args);
    renderUV(renderer,crystals);composite.uniforms.tDiffuse.value=material.uniforms.tDiffuse.value;
    composite.blending=CustomBlending;return originalRenderPass.call(pass,renderer,composite,...args);
  };
  pass._renderPass=wrapped;
  return {dispose(){if(disposed)return;disposed=true;if(pass._renderPass===wrapped)pass._renderPass=originalRenderPass;
    materials.forEach(material=>material.dispose());composite.dispose();mask.dispose();}};
}
