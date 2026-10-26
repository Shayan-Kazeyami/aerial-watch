// These source IDs describe the actual retained OM10 power path. This overlay
// changes emphasis only: it never changes positions, phases or visibility.
export const POWER_PATH = Object.freeze([
  {label:'Stored energy · barrel',ids:[81,82]},
  {label:'Wheel train · linked reductions',ids:[92,93,94,95,96,97]},
  {label:'Escapement · measured release',ids:[98,99]},
  {label:'Balance · regulating oscillator',ids:[133,134,135]},
]);
export const TOUR_SHOTS=Object.freeze(['showcase','face','interior','balance','train','lug']);
export const restoresExterior=view=>['showcase','three-quarter','front','back','side','face','lug','buckle'].includes(view);
export function createTourSequence(){
  let index=0,running=false,elapsed=0;
  return {
    snapshot:()=>({index,running,view:TOUR_SHOTS[index],count:TOUR_SHOTS.length}),
    stop(){running=false;elapsed=0;},
    start({reducedMotion=false}={}){index=0;elapsed=0;running=!reducedMotion;return this.snapshot();},
    step(direction=1){index=(index+direction%TOUR_SHOTS.length+TOUR_SHOTS.length)%TOUR_SHOTS.length;elapsed=0;return this.snapshot();},
    tick(delta){if(!running||!Number.isFinite(delta)||delta<=0)return null;elapsed+=delta;if(elapsed<7)return null;const steps=Math.floor(elapsed/7);elapsed%=7;index=(index+steps%TOUR_SHOTS.length)%TOUR_SHOTS.length;return this.snapshot();},
  };
}
export function sourceNeedsBaseline(part,replacedSources=new Set([0,155])){
  return replacedSources.has(part.sourceIndex)||['DIAL','CHAPTER','HOUR','MINUTE','SECONDS','SECONDS-STAFF','STRAP-UPPER','STRAP-LOWER'].includes(part.assemblyId);
}

// Validate everything before touching viewer state, so a malformed local file
// cannot leave a half-restored watch. Unknown diagnostic fields are ignored.
export function validateViewConfiguration(config,{qualities=['balanced','detail','studio','efficient']}={}){
  if(config?.version!==1||!config.camera||!config.options)throw new Error('Unsupported view file.');
  const vector=v=>Array.isArray(v)&&v.length===3&&v.every(n=>Number.isFinite(n)&&Math.abs(n)<=10000);
  const {position,target,zoom,fov=32}=config.camera;
  if(!vector(position)||!vector(target)||Math.hypot(...position.map((v,i)=>v-target[i]))<.001||!Number.isFinite(zoom)||zoom<.4||zoom>12||!Number.isFinite(fov)||fov<10||fov>100)throw new Error('Invalid camera.');
  const view=config.view||'face';
  if(![...TOUR_SHOTS,'front','side','back','three-quarter','buckle','winding','crown'].includes(view))throw new Error('Unknown saved view.');
  for(const key of ['openWork','finishes','crystals','movementOnly'])if(typeof config.options[key]!=='boolean')throw new Error(`Invalid ${key} option.`);
  const quality=config.options.quality||'detail';if(!qualities.includes(quality))throw new Error('Unknown rendering quality.');
  const {mechanism=0,hands=0,speed=1}=config.clock||{};
  if(![mechanism,hands].every(v=>Number.isFinite(v)&&v>=0)||!Number.isFinite(speed)||speed<=0||speed>1000)throw new Error('Invalid saved clock.');
  const crown=config.crown??{pulled:false,degrees:0};
  const settingSeconds=config.settingSeconds??0;if(!Number.isFinite(settingSeconds)||Math.abs(settingSeconds)>1e12)throw new Error('Invalid saved setting offset.');
  if(typeof crown.pulled!=='boolean'||!Number.isFinite(crown.degrees)||Math.abs(crown.degrees)>3600000)throw new Error('Invalid saved crown state.');
  const winding=config.winding?.state??{crownDegrees:crown.degrees,driveDegrees:0,ratchetRadians:0,pulled:crown.pulled,reverseFreewheel:false};
  if(!winding||![winding.crownDegrees,winding.driveDegrees,winding.ratchetRadians].every(Number.isFinite)||Math.abs(winding.crownDegrees)>1e12||Math.abs(winding.driveDegrees)>1e12||Math.abs(winding.crownDegrees-crown.degrees)>1e-8||winding.driveDegrees>0||typeof winding.pulled!=='boolean'||typeof winding.reverseFreewheel!=='boolean'||winding.pulled!==crown.pulled||(winding.pulled&&winding.reverseFreewheel)||Math.abs(winding.ratchetRadians+winding.driveDegrees*Math.PI/180*16/63)>1e-8)throw new Error('Invalid saved winding state.');
  return {view,camera:{position:[...position],target:[...target],zoom,fov},options:{...config.options,quality},clock:{mechanism,hands,speed},crown:{pulled:crown.pulled,degrees:crown.degrees},winding:{...winding},settingSeconds};
}
