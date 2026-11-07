from pathlib import Path
import sys,hashlib
r=Path(sys.argv[1]).resolve()
BEFORE={'scripts/build-atelier-release.mjs': '9daacc41891e7f109e3abd3a127f39088304d55cd3958080d984b8195dc026db', 'tests/atelier-release-build.test.mjs': 'ea68caf2cdcbb251b3724a05675ef9f7375eb5ac0dd2ae81851f8f030cfd83bf'}
AFTER={'scripts/build-atelier-release.mjs': 'fd4671ea08d970814cf6076a328690c3801f30f01cb1ac8995695e428f126cb7', 'tests/atelier-release-build.test.mjs': 'ef1a68e9654b5fb4fc03d38dbe801b555a7af72302d7d09b3d8f95d008bf74ca'}
for n,h in BEFORE.items():
 assert hashlib.sha256((r/n).read_bytes()).hexdigest()==h,'Unexpected tooling baseline: '+n
p=r/'scripts/build-atelier-release.mjs';s=p.read_text()
assert s.count(" ...['leather-qa-avif-gentle.gltf','color-avif-crf12.avif','roughness-avif-crf12.avif','normal-avif-crf6.avif'].map(name=>'leather-assets/r14/'+name),\n")==1
s=s.replace(" ...['leather-qa-avif-gentle.gltf','color-avif-crf12.avif','roughness-avif-crf12.avif','normal-avif-crf6.avif'].map(name=>'leather-assets/r14/'+name),\n"," ...R12_LEATHER_ASSETS,\n 'leather-assets/r14/outer-normal-2k.manifest.json','leather-assets/r14/normal-2048-existing-mips.ktx2',\n ...['leather-qa-avif-gentle.gltf','color-avif-crf12.avif','roughness-avif-crf12.avif','normal-avif-crf6.avif'].map(name=>'leather-assets/r14/'+name),\n",1)
assert s.count('export const ATELIER_ASSETS=Object.freeze([\n')==1
s=s.replace('export const ATELIER_ASSETS=Object.freeze([\n',"export const R12_LEATHER_ASSETS=Object.freeze(['leather.gltf','geometry.bin','original-0.png','original-1.jpg','original-2.jpg','original-3.jpg','original-4.jpg','outer-color-2k.ktx2','outer-roughness-2k.ktx2','outer-normal-4k.chunks.json','outer-normal-4k.ktx2.part0','outer-normal-4k.ktx2.part1'].map(name=>'quality-study/leather-r12/'+name));\nexport const ATELIER_ASSETS=Object.freeze([\n",1)
p.unlink();p.write_text(s)
p=r/'tests/atelier-release-build.test.mjs';s=p.read_text()
s+="\ntest('default assets retain full R12 compatibility closure and R14 progressive normal alternative',async()=>{\n const {ATELIER_ASSETS,R12_LEATHER_ASSETS,R14_LEATHER_ASSETS,validateAssetClosure}=await import('../scripts/build-atelier-release.mjs');\n for(const p of [...R12_LEATHER_ASSETS,...R14_LEATHER_ASSETS,'leather-assets/r14/outer-normal-2k.manifest.json','leather-assets/r14/normal-2048-existing-mips.ktx2'])assert.ok(ATELIER_ASSETS.includes(p),p);\n const buffers=new Map();for(const p of [...R12_LEATHER_ASSETS,...R14_LEATHER_ASSETS])buffers.set(p,await readFile(new URL('../'+p,import.meta.url)));\n const closure=validateAssetClosure(buffers);assert.equal(closure.gltfCount,2);assert.equal(closure.virtualTextures.length,2);\n for(const omitted of ['quality-study/leather-r12/geometry.bin','quality-study/leather-r12/original-1.jpg','quality-study/leather-r12/outer-normal-4k.ktx2.part1']){const incomplete=new Map(buffers);incomplete.delete(omitted);assert.throws(()=>validateAssetClosure(incomplete),/Unpackaged|chunk/);}\n const manifest=JSON.parse(await readFile(new URL('../leather-assets/r14/outer-normal-2k.manifest.json',import.meta.url)));assert.equal(manifest.bytes,4389472);assert.equal(manifest.sha256,'5d8aa10702589424c1157d9a58a7f75aca265569d7c8fac09525a00af19455bc');assert.equal(manifest.chunks.length,1);\n const lowPath='leather-assets/r14/'+manifest.chunks[0].uri;assert.ok(ATELIER_ASSETS.includes(lowPath));const low=await readFile(new URL('../'+lowPath,import.meta.url));assert.equal(low.length,manifest.bytes);assert.equal(sha(low),manifest.sha256);\n});\n"
p.unlink();p.write_text(s)
for n,h in AFTER.items():
 assert hashlib.sha256((r/n).read_bytes()).hexdigest()==h,'Tooling result mismatch: '+n
print('Default release dependency closure tooling overlay verified; runtime untouched.')
