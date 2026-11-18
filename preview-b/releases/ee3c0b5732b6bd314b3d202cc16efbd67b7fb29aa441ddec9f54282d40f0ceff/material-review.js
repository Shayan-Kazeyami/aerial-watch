import * as THREE from 'three';
import {EffectComposer} from 'three/addons/postprocessing/EffectComposer.js';
import {RenderPass} from 'three/addons/postprocessing/RenderPass.js';
import {OutputPass} from 'three/addons/postprocessing/OutputPass.js';
import {createAssemblyMaterials,createStudioEnvironment,ASSEMBLY_FINISH_SPECIFICATIONS} from './assembly-materials.js';
import {createAssemblyLighting} from './assembly-lighting.js';
import {resolveRenderResolution} from './assembly-resolution.js';
import {FINISH_REVIEW_SAMPLES,FINISH_REVIEW_CONTRACT,createFinishReviewSamples} from './material-review-model.js';

const $=id=>document.getElementById(id),params=new URLSearchParams(location.search);
let renderer,composer,finishes,neutralEnvironment,samples,lighting,observer,disposed=false;
let light=params.get('light')==='product'?'product':'neutral';
let selected=FINISH_REVIEW_SAMPLES.some(s=>s.kind===params.get('sample'))?params.get('sample'):'';
let resolution;
const scene=new THREE.Scene(),camera=new THREE.OrthographicCamera(-27,27,18,-18,.1,200),output=new OutputPass();

function download(blob,name){
  const url=URL.createObjectURL(blob),anchor=document.createElement('a');anchor.href=url;anchor.download=name;anchor.click();
  setTimeout(()=>URL.revokeObjectURL(url),3000);
}
function configuration(){
  return {version:1,study:'Aerial Quality 01 / shared material comparison',light,sample:selected||null,
    contract:FINISH_REVIEW_CONTRACT,finishSpecifications:ASSEMBLY_FINISH_SPECIFICATIONS,
    camera:{type:'orthographic',position:camera.position.toArray(),quaternion:camera.quaternion.toArray(),left:camera.left,right:camera.right,top:camera.top,bottom:camera.bottom,near:camera.near,far:camera.far},
    render:{...resolution,drawingBuffer:[renderer.domElement.width,renderer.domElement.height],transmissionScale:renderer.transmissionResolutionScale,toneMapping:'ACESFilmic',exposure:renderer.toneMappingExposure},
    reproduction:`material-review.html?light=${light}${selected?`&sample=${selected}`:''}`};
}
function render(){if(!disposed&&composer)composer.render(0);}
function frame(){
  if(!renderer)return;
  const size=$('stage').getBoundingClientRect();
  resolution=resolveRenderResolution({width:size.width,height:size.height,quality:'detail',devicePixelRatio:devicePixelRatio,maxTextureSize:renderer.capabilities.maxTextureSize,maxSamples:renderer.capabilities.maxSamples});
  renderer.setPixelRatio(resolution.pixelRatio);renderer.setSize(size.width,size.height,false);
  composer.setPixelRatio(resolution.pixelRatio);composer.setSize(size.width,size.height);
  renderer.transmissionResolutionScale=resolution.transmissionScale;
  const aspect=size.width/size.height,baseHeight=selected?FINISH_REVIEW_CONTRACT.macroHeight:FINISH_REVIEW_CONTRACT.heroHeight;
  const height=Math.max(baseHeight,(selected?16:49)/aspect),width=height*aspect;
  camera.left=-width/2;camera.right=width/2;camera.top=height/2;camera.bottom=-height/2;
  const target=selected?samples.meshes[FINISH_REVIEW_SAMPLES.findIndex(s=>s.kind===selected)].position:new THREE.Vector3();
  camera.position.copy(target).add(new THREE.Vector3(0,0,80));camera.lookAt(target);camera.updateProjectionMatrix();
  $('render-size').textContent=`${renderer.domElement.width} × ${renderer.domElement.height} px · ${resolution.pixelRatio.toFixed(2)}× · ${resolution.samples}× MSAA`;
  render();
}
function setView(){
  const neutral=light==='neutral';
  scene.environment=neutral?neutralEnvironment.texture:finishes.environment;
  scene.background.set(neutral?0x303332:0x222726);
  lighting.applyShot(neutral?'neutral':'face',{instant:true});
  lighting.key.color.set(neutral?0xffffff:0xfff4e3);lighting.rim.color.set(neutral?0xffffff:0xd4e4ff);
  lighting.fill.color.set(neutral?0xffffff:0xe5edf5);lighting.hemisphere.color.set(neutral?0xffffff:0xe7edf4);
  lighting.hemisphere.groundColor.set(neutral?0x242424:0x1b1d1c);
  // Keep exposure/environment strength fixed so light colour and card shape are
  // assessed without automatic brightness compensation or a moving camera.
  scene.environmentIntensity=FINISH_REVIEW_CONTRACT.environmentIntensity;
  renderer.toneMappingExposure=FINISH_REVIEW_CONTRACT.exposure;
  $('neutral').setAttribute('aria-pressed',String(neutral));$('product').setAttribute('aria-pressed',String(!neutral));
  $('hero').setAttribute('aria-pressed',String(!selected));$('sample').value=selected;
  samples.meshes.forEach((mesh,i)=>{
    mesh.visible=!selected||FINISH_REVIEW_SAMPLES[i].kind===selected;
    // Every close-up occupies the same world position under the same lights.
    // The complete board restores its fixed comparison layout.
    mesh.position.set(selected?0:(i%3-1)*17,selected?0:(i<3?7.8:-7.8),0);
  });
  const caption=selected?FINISH_REVIEW_SAMPLES.find(s=>s.kind===selected).label:'All finishes';
  $('view-label').textContent=`${neutral?'Neutral':'Product'} / ${caption}`;
  history.replaceState(null,'',`?light=${light}${selected?`&sample=${selected}`:''}`);frame();
}
function dispose(){
  if(disposed)return;disposed=true;observer?.disconnect();samples?.dispose();lighting?.dispose();
  neutralEnvironment?.dispose();finishes?.dispose();output.dispose();composer?.passes.forEach(pass=>pass!==output&&pass.dispose?.());composer?.dispose();renderer?.dispose();
}
try{
  renderer=new THREE.WebGLRenderer({canvas:$('finish-canvas'),antialias:true,powerPreference:'high-performance'});
  renderer.toneMapping=THREE.ACESFilmicToneMapping;renderer.shadowMap.enabled=false;
  scene.background=new THREE.Color(0x303332);finishes=createAssemblyMaterials(renderer);neutralEnvironment=createStudioEnvironment(renderer,{neutral:true});
  samples=createFinishReviewSamples(finishes);scene.add(samples.group);lighting=createAssemblyLighting(scene,{renderer});lighting.floor.visible=false;
  composer=new EffectComposer(renderer);const samplesCount=Math.min(4,renderer.capabilities.maxSamples);
  composer.renderTarget1.samples=composer.renderTarget2.samples=samplesCount;composer.addPass(new RenderPass(scene,camera));composer.addPass(output);
  for(const sample of FINISH_REVIEW_SAMPLES){
    const option=document.createElement('option');option.value=sample.kind;option.textContent=sample.label;$('sample').append(option);
    const caption=document.createElement('div');caption.className='caption';const button=document.createElement('button');button.textContent=sample.label;button.addEventListener('click',()=>{selected=sample.kind;setView();});
    const note=document.createElement('p');note.textContent=sample.note;caption.append(button,note);$('caption-grid').append(caption);
  }
  $('neutral').addEventListener('click',()=>{light='neutral';setView();});$('product').addEventListener('click',()=>{light='product';setView();});
  $('hero').addEventListener('click',()=>{selected='';setView();});$('sample').addEventListener('change',event=>{selected=event.target.value;setView();});
  $('capture').addEventListener('click',()=>{
    // Capture immediately after rendering; never retain an expensive drawing
    // buffer between frames. No animation, random seed or elapsed clock exists.
    render();const stem=`aerial-finish-${light}-${selected||'all'}`;
    renderer.domElement.toBlob(blob=>{if(blob)download(blob,`${stem}.png`);},'image/png');
  });
  $('save-view').addEventListener('click',()=>{
    const config=configuration(),stem=`aerial-finish-${light}-${selected||'all'}`;
    download(new Blob([JSON.stringify(config,null,2)],{type:'application/json'}),`${stem}.json`);
  });
  renderer.domElement.addEventListener('webglcontextlost',event=>{event.preventDefault();$('failure').hidden=false;$('failure').textContent='The graphics context was interrupted. Reload this page to restore the comparison.';$('capture').disabled=true;$('save-view').disabled=true;});
  observer=new ResizeObserver(frame);observer.observe($('stage'));setView();
  // PMREM/material compilation completes in this render; render again on the
  // next paint so the first still includes any newly uploaded material state.
  requestAnimationFrame(render);
  addEventListener('pagehide',event=>{if(!event.persisted)dispose();});
}catch(error){
  $('failure').hidden=false;$('failure').textContent=`Material preview unavailable: ${error.message}`;$('capture').disabled=true;$('save-view').disabled=true;
  dispose();
}
