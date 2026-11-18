import {installReceiverPlaneShadowStudy} from './assembly-receiver-plane-shadow.js';
import {createReceiverPlaneShadowFilter} from './assembly-receiver-plane-shadow-tsl.js';

// Premium-viewer default; backend selection remains independently optional.
// No QA UI, uniform A/B branch, clock changes, or capture instrumentation.
export function receiverPlaneFinishEnabled({node=false,atelier=false,requested=null}={}){
 if(requested==='baseline')return false;
 if(requested==='receiver')return true;
 return atelier;
}
export async function installReceiverPlaneFinish({renderer,key,enabled=false,loadTSL=()=>import('./vendor/three.tsl.js')}={}){
 const node=!!renderer.isWebGPURenderer;
 const audit={enabled,path:node?'node-TSL':'native-GLSL',revision:'receiver-plane-r187-r1',vogelCentres:5,effectiveDepthLocations:20,comparisonFetches:{baseline:5,corrected:20},performanceAcceptance:'pending GPU measurement',scope:'receiving-plane depth comparison only; original PCF radius, bias, map size and bilinear weights'};
 let restore=()=>{};
 if(enabled){
  if(node){const T=await loadTSL(),original=key.shadow.filterNode;key.shadow.filterNode=createReceiverPlaneShadowFilter(T);restore=()=>{key.shadow.filterNode=original;};}
  else restore=installReceiverPlaneShadowStudy();
 }
 return {audit,dispose:restore};
}
