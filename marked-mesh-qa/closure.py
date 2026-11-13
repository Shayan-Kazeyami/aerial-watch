import pathlib,json,shutil,hashlib
root=pathlib.Path('preview-b/releases');base=root/pathlib.Path('marked-mesh-qa/release-id.txt').read_text().strip();m=json.loads((base/'deployment-manifest.json').read_text())
for f in m['references']:
 src=root/f['ownerReleaseId']/f['path'];b=src.read_bytes();assert len(b)==f['sizeBytes'] and hashlib.sha256(b).hexdigest()==f['sha256'];dst=base/f['path'];dst.parent.mkdir(parents=True,exist_ok=True)
 if not dst.exists():shutil.copyfile(src,dst)
print('Verified and materialized reference closure')
