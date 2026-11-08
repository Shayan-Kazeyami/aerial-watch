from pathlib import Path
import shutil
root=Path('preview-b/releases/949a4881d119910ca28bdf5ef4d67dfdebc59df579e02a6de946db48668510c8')
here=Path('metal-recovery/integration-study')
for name in ['assembly-hybrid-case.js','assembly-hybrid-case-data.js','assembly-hybrid-delivery.js']:
 shutil.copyfile(here/('assembly-hybrid-case-data.compressed.js' if name=='assembly-hybrid-case-data.js' else name),root/name)
(root/'hybrid-case-assets').mkdir(exist_ok=True);shutil.copyfile('metal-recovery/cap-study/hybrid-field-v7.meshopt.glb.gz',root/'hybrid-case-assets/hybrid-field-v7.meshopt.glb.gz')
(root/'vendor/meshopt').mkdir(parents=True,exist_ok=True)
for file in ['meshopt_decoder.mjs','LICENSE.md','PROVENANCE.json']:shutil.copyfile(Path('metal-recovery/source/vendor/meshopt')/file,root/'vendor/meshopt'/file)
s=(root/'assembly-review.js').read_text()
def replace(old,new):
 global s
 assert s.count(old)==1,(old,s.count(old));s=s.replace(old,new)
replace('let capRefinement=null;', "let capRefinement=null,hybridCase=null;\nfunction hybridCaseSnapshot(){return hybridCase?{...hybridCase.audit,active:hybridCase.active,ownsGeometry:hybridCase.ownsGeometry}:{active:false};}")
replace('preserveCaseGeometry:!!parametricCase?.enabled||!!capRefinement?.active','preserveCaseGeometry:!!parametricCase?.enabled||!!capRefinement?.active||!!hybridCase?.active')
replace("    if(parametricCaseMode!=='fine-combined'){","    if(parametricCaseMode!=='fine-combined'&&parametricCaseMode!=='hybrid-study'){")
replace('    const root=(baseline.gltf||baseline).scene,disposeOriginal=ownedObjectTreeDisposer(root);\n    let replacement;',"    if(parametricCaseMode==='hybrid-study'){\n      const root=(baseline.gltf||baseline).scene,disposeOriginal=ownedObjectTreeDisposer(root);let replacement;\n      try{\n        const {installHybridCase,loadHybridCaseAsset}=await import('./assembly-hybrid-case.js');\n        replacement=await installHybridCase(root,{signal:lifecycle.signal,privateStudy:true,loadCandidate:()=>loadHybridCaseAsset(assetOptions())});\n        if(lifecycle.disposed||lifecycle.signal.aborted)throw new DOMException('Selected CASE load cancelled.','AbortError');\n        let disposed=false;objectDisposers.set(root,()=>{if(disposed)return;disposed=true;try{replacement.dispose();}finally{disposeOriginal();}});\n        hybridCase=replacement;\n      }catch(error){try{replacement?.dispose();}finally{disposeOriginal();}throw error;}\n      return baseline;\n    }\n    const root=(baseline.gltf||baseline).scene,disposeOriginal=ownedObjectTreeDisposer(root);\n    let replacement;")
replace('return {capRefinement:','return {hybridCase:hybridCaseSnapshot(),capRefinement:')
replace("reason:'separate combined CASE study'","reason:hybridCase?.active?'hybrid includes preserved source cap015':'separate combined CASE study'")
replace('window.assemblyInspect = () => ({viewportVisible:','window.assemblyInspect = () => ({hybridCase:hybridCaseSnapshot(),viewportVisible:')
# Instrument views only. No loader/direct geometry swaps in this QA hook.
s=s.replace('composer.render();','metalApply();composer.render();');s+='\n'+(here/'qa-hook.js').read_text();(root/'assembly-review.js').write_text(s)
