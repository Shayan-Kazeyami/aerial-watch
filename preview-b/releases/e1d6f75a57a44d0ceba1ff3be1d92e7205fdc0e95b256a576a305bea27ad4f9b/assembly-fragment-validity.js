// Reject only nonfinite raster depth on the identified Graphite dial material.
// Kept after all original derivative/lighting calculations so valid fragments
// retain the authored shading and derivative control flow.
export const GRAPHITE_FRAGMENT_VALIDITY_REVISION='graphite-finite-raster-depth-r1';
export function bindGraphiteFragmentValidity(material){
 if(material?.name!=='Graphite dial')return false;
 material.userData??={};
 if(material.userData.graphiteFragmentValidity===GRAPHITE_FRAGMENT_VALIDITY_REVISION)return false;
 const previous=material.onBeforeCompile,previousKey=material.customProgramCacheKey();
 material.onBeforeCompile=function(shader,...args){
  previous.call(this,shader,...args);
  const anchor='#include <opaque_fragment>';
  if(shader.fragmentShader.split(anchor).length!==2)throw Error('Graphite fragment validity: expected one opaque output anchor');
  shader.fragmentShader=shader.fragmentShader.replace(anchor,'if (isnan(gl_FragCoord.z) || isinf(gl_FragCoord.z)) discard;\n'+anchor);
 };
 material.customProgramCacheKey=()=>previousKey+'|'+GRAPHITE_FRAGMENT_VALIDITY_REVISION;
 material.userData.graphiteFragmentValidity=GRAPHITE_FRAGMENT_VALIDITY_REVISION;
 material.needsUpdate=true;
 return true;
}
