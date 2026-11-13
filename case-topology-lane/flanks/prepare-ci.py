import pathlib,shutil,json,hashlib
R=pathlib.Path('case-topology-lane');rid='b38ddef36d153be511c40fc6d51795308a50440635edf1c97c39a725120cfdd3';base=pathlib.Path('preview-b/releases')/rid
m=json.loads((base/'deployment-manifest.json').read_text())
for f in m['references']:
 src=pathlib.Path('preview-b/releases')/f['ownerReleaseId']/f['path'];b=src.read_bytes();assert len(b)==f['sizeBytes'] and hashlib.sha256(b).hexdigest()==f['sha256'];dst=base/f['path'];dst.parent.mkdir(parents=True,exist_ok=True)
 if not dst.exists():shutil.copyfile(src,dst)
s=(R/'decode.mjs').read_text().replace('marked-mesh-qa/recovery-b38ddef3/','').replace('../metal-recovery/source/vendor/meshopt/meshopt_decoder.mjs','../'+str(base)+'/vendor/meshopt/meshopt_decoder.mjs');(R/'decode-ci.mjs').write_text(s)
s=(R/'encode.mjs').read_text().replace('../metal-recovery/source/vendor/meshopt/','../'+str(base)+'/vendor/meshopt/');(R/'encode-ci.mjs').write_text(s.replace('hybrid-structured-side-r04-candidate','hybrid-structured-flanks-r05-candidate'))
shutil.copyfile(base/'assembly-hybrid-case-data.js',R/'baseline-data.js');s=(R/'baseline-data.js').read_text().replace('"url": "hybrid-case-assets/','"url": "/'+str(base)+'/hybrid-case-assets/');(R/'baseline-data.js').write_text(s)

for tag in ["opposite-positive","opposite-negative"]:
 d=R/tag;d.mkdir(exist_ok=True);(d/"current").symlink_to("../current",target_is_directory=True);(d/"labels.npy").symlink_to("../labels.npy")
