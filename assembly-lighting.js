import * as THREE from './vendor/three.module.js';

// All lengths, including shadow fit and AO kernels, use the scene's millimetres.
// A shared exposure and palette connect the product shots; macro light/shadow
// bounds concentrate the available texels rather than increasing every map.
export const ASSEMBLY_LIGHT_SHOTS=Object.freeze({
  hero:{focus:[0,-2,-12],key:[-40,55,70],rim:[42,16,-50],span:55,keyPower:1.05,rimPower:.5,fillPower:.24,environmentIntensity:.85,kernelRadius:1.1},
  face:{focus:[0,0,0],key:[-34,42,70],rim:[36,12,-36],span:24,keyPower:.92,rimPower:.42,fillPower:.30,environmentIntensity:.9,kernelRadius:.8},
  rear:{focus:[0,0,-1],key:[-30,45,-65],rim:[38,12,42],span:24,keyPower:1.02,rimPower:.45,fillPower:.28,environmentIntensity:.9,kernelRadius:.8},
  balance:{focus:[-3.514,8.063,-.4],key:[-17,26,-40],rim:[24,11,28],span:9,keyPower:.95,rimPower:.38,fillPower:.28,environmentIntensity:.95,kernelRadius:.4},
  train:{focus:[-7.2,-.7,-.2],key:[-24,28,-45],rim:[26,9,30],span:14,keyPower:1.0,rimPower:.4,fillPower:.26,environmentIntensity:.93,kernelRadius:.55},
  winding:{focus:[6.5,-3.5,-1.5],key:[-18,30,-45],rim:[27,12,25],span:12,keyPower:1.0,rimPower:.4,fillPower:.26,environmentIntensity:.93,kernelRadius:.5},
  neutral:{focus:[0,0,0],key:[-35,45,65],rim:[35,15,-45],span:30,keyPower:.8,rimPower:.25,fillPower:.38,environmentIntensity:.85,kernelRadius:.65},
});

function shotName(view){
  if(view==='interior'||view==='back'||view==='reverse')return 'rear';
  if(view==='front')return 'face';
  return Object.hasOwn(ASSEMBLY_LIGHT_SHOTS,view)?view:'hero';
}

export function createAssemblyLighting(scene,{renderer,onChange}={}){
  const hemisphere=new THREE.HemisphereLight(0xe7edf4,0x1b1d1c,.22);
  const key=new THREE.DirectionalLight(0xfff4e3,1),rim=new THREE.DirectionalLight(0xd4e4ff,.45);
  const fill=new THREE.DirectionalLight(0xe5edf5,.28);
  key.castShadow=true;key.shadow.mapSize.set(2048,2048);
  key.shadow.bias=-.000025;key.shadow.normalBias=.006;key.shadow.radius=2;
  const floor=new THREE.Mesh(new THREE.PlaneGeometry(2400,2400),new THREE.MeshStandardMaterial({color:0x151b20,roughness:.87,metalness:.06}));
  floor.name='Photographic studio floor';floor.rotation.x=-Math.PI/2;floor.position.y=-35.2;floor.receiveShadow=true;
  scene.add(hemisphere,key,key.target,rim,rim.target,fill,fill.target,floor);
  let goal,changing=false,disposed=false,current='face';

  function setShadowFit(profile){
    const shadow=key.shadow.camera,span=profile.span,distance=Math.hypot(...profile.key);
    Object.assign(shadow,{left:-span,right:span,top:span,bottom:-span,near:Math.max(1,distance-span*2-15),far:distance+span*2+20});
    shadow.updateProjectionMatrix();
    key.shadow.normalBias=span<=14?.003:.006;
    key.shadow.needsUpdate=true;
  }
  function applyShot(view,{instant=false}={}){
    current=shotName(view);const profile=ASSEMBLY_LIGHT_SHOTS[current],focus=new THREE.Vector3(...profile.focus);
    goal={focus,key:focus.clone().add(new THREE.Vector3(...profile.key)),rim:focus.clone().add(new THREE.Vector3(...profile.rim)),
      fill:focus.clone().add(new THREE.Vector3(8,16,current==='rear'||['balance','train','winding'].includes(current)?-55:55)),
      keyPower:profile.keyPower,rimPower:profile.rimPower,fillPower:profile.fillPower,environmentIntensity:profile.environmentIntensity,exposure:1.08};
    setShadowFit(profile);changing=true;
    if(instant)update(10);
    const settings={name:current,key,floor,rim,exposure:goal.exposure,environmentIntensity:goal.environmentIntensity,
      shadowTexelMM:profile.span*2/key.shadow.mapSize.x,
      ao:{kernelRadius:profile.kernelRadius,minDistance:.000015,maxDistance:.003}};
    onChange?.(settings);return settings;
  }
  function update(delta){
    if(!changing||!goal||disposed)return false;
    const factor=delta>=2?1:1-Math.exp(-Math.max(0,delta)*7);
    key.position.lerp(goal.key,factor);rim.position.lerp(goal.rim,factor);fill.position.lerp(goal.fill,factor);
    for(const light of [key,rim,fill])light.target.position.lerp(goal.focus,factor);
    key.intensity=THREE.MathUtils.lerp(key.intensity,goal.keyPower,factor);
    rim.intensity=THREE.MathUtils.lerp(rim.intensity,goal.rimPower,factor);
    fill.intensity=THREE.MathUtils.lerp(fill.intensity,goal.fillPower,factor);
    scene.environmentIntensity=THREE.MathUtils.lerp(scene.environmentIntensity,goal.environmentIntensity,factor);
    if(renderer)renderer.toneMappingExposure=THREE.MathUtils.lerp(renderer.toneMappingExposure,goal.exposure,factor);
    key.shadow.needsUpdate=true;
    const distance=Math.max(key.position.distanceTo(goal.key),rim.position.distanceTo(goal.rim),fill.position.distanceTo(goal.fill));
    if(distance<.0001&&Math.abs(key.intensity-goal.keyPower)<.00001)changing=false;
    return true;
  }
  applyShot('face',{instant:true});
  return {key,rim,fill,hemisphere,floor,applyShot,update,
    get shot(){return current;},
    dispose(){
      if(disposed)return;disposed=true;
      for(const object of [hemisphere,key,key.target,rim,rim.target,fill,fill.target,floor])object.removeFromParent();
      key.shadow.dispose();floor.geometry.dispose();floor.material.dispose();
    },
  };
}
