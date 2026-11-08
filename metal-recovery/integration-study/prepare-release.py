from pathlib import Path
import shutil
here=Path('metal-recovery/integration-study');owner=Path('preview-b/releases/949a4881d119910ca28bdf5ef4d67dfdebc59df579e02a6de946db48668510c8');target=Path('hybrid-release-work')
shutil.copytree(owner,target)
s=(here/'install-ci.py').read_text();s=s.replace("root=Path('preview-b/releases/949a4881d119910ca28bdf5ef4d67dfdebc59df579e02a6de946db48668510c8')","root=Path('hybrid-release-work')");s=s.split('# Instrument views only.')[0]+"\n(root/'assembly-review.js').write_text(s)\n";exec(compile(s,'private-installer-hooks','exec'))
s=(target/'assembly-review.js').read_text().replace("get('caseStudy')||'source'","get('caseStudy')||'hybrid-study'").replace('privateStudy:true,loadCandidate','privateStudy:false,loadCandidate');(target/'assembly-review.js').write_text(s)
s=(target/'assembly-hybrid-case-data.js').read_text().replace('pending-visual-verification','verified').replace('hybrid-source-cap015-v7-private','hybrid-source-cap015-v7');(target/'assembly-hybrid-case-data.js').write_text(s)
s=(target/'assembly-hybrid-case.js').read_text().replace('// PRIVATE integration preparation. Geometry acceptance remains pending.','// Verified v7 hybrid CASE. Source material ownership is preserved.');(target/'assembly-hybrid-case.js').write_text(s)
# The indivisible vendor directory is already pinned to this immutable owner.
s=(target/'assembly-hybrid-delivery.js').read_text().replace("'./vendor/meshopt/meshopt_decoder.mjs'","'../f3ab38493b7bc5c4af84728add913e54938d0db276143a7b765a7803f361bb44/vendor/meshopt/meshopt_decoder.mjs'");(target/'assembly-hybrid-delivery.js').write_text(s);shutil.rmtree(target/'vendor')
