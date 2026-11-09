from pathlib import Path
import sys
source=Path(sys.argv[1]); out=Path(sys.argv[2]); s=source.read_text()
def once(a,b):
 global s
 assert s.count(a)==1,(a[:90],s.count(a))
 s=s.replace(a,b)
once("import {createPresentationGate} from './assembly-presentation-gate.js';", "import {createPresentationGate} from './assembly-presentation-gate.js';\nimport {createPreparedAsset} from './assembly-prepared-asset.js';")
face="loadGLTFAsset(premiumFaceAsset(new URLSearchParams(location.search).get('face')),assetOptions())"
once(face+'.then(result=>{','preparedFace.take().then(result=>{')
start=s.index("  const leatherAsset=photoLeatherAsset(")
end=s.index("  leatherLoad.then(result=>{",start)
load=s[start:end]
assert load.count('\n')==2
leather=load.splitlines()[1].strip().removeprefix('const leatherLoad=').removesuffix(';')
asset=load.splitlines()[0].strip()
s=s[:start]+"  preparedLeather.take().then(result=>{"+s[end+len("  leatherLoad.then(result=>{"):]
block="""// Independent selected assets prepare while the baseline is loading. Adoption
// still waits for initializeBaseline, and the existing first-frame gate is unchanged.
const preparedFace=premiumRequested?createPreparedAsset({signal:lifecycle.signal,
 load:signal=>FACE,
 dispose:result=>disposeObjectTree(result.gltf.scene)}):null;
ASSET
const preparedLeather=createPreparedAsset({signal:lifecycle.signal,
 load:signal=>LEATHER,
 dispose:result=>disposeObjectTree(result.gltf.scene)});
resources.own('pending selected dial',()=>preparedFace?.dispose());
resources.own('pending selected leather',()=>preparedLeather.dispose());
""".replace('FACE',face.replace('assetOptions()','{...assetOptions(),signal}')).replace('ASSET',asset).replace('LEATHER',leather.replace('signal:lifecycle.signal','signal').replace('assetOptions()','{...assetOptions(),signal}'))
once("startupDiagnostics.mark('required-assets-start');", "startupDiagnostics.mark('required-assets-start');\n"+block)
line=next(line for line in s.splitlines() if line.startswith("}).catch(error=>{if(!lifecycle.disposed)fail(error.name==='TimeoutError'?"))
once(line,line.replace(',error);});',',error);preparedFace?.dispose();preparedLeather.dispose();});'))

out.write_text(s)
