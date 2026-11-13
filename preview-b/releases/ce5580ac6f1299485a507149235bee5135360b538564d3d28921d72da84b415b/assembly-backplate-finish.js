import {cloneAssemblyMaterial} from './assembly-materials.js';
export const DARK_BACKPLATE_FINISH=Object.freeze({name:'Ruthenium / circular brushed charcoal',color:0x3f464d,metalness:1,roughness:.39,transmission:0,opacity:1});
export function createDarkBackplateFinish(source){
  const material=cloneAssemblyMaterial(source);
  material.name=DARK_BACKPLATE_FINISH.name;
  material.color.setHex(DARK_BACKPLATE_FINISH.color);
  material.metalness=1;material.roughness=.39;material.transmission=0;material.opacity=1;material.transparent=false;material.depthWrite=true;
  return material;
}
