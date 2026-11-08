// Node-only verification of exactly the locally pinned browser modules.
export async function resolve(specifier,context,next){
 const modules={'three':'three.module.js','three/webgpu':'three.webgpu.js','three/tsl':'three.tsl.js'};
 return Object.hasOwn(modules,specifier)?{url:new URL('../source/vendor/'+modules[specifier],import.meta.url).href,shortCircuit:true}:next(specifier,context);
}
