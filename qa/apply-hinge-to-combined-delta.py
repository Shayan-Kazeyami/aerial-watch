#!/usr/bin/env python3
"""Exact hinge14 -> combined delta. Default verifies without writing."""
from pathlib import Path
import hashlib,json,tarfile,argparse,os
RECEIPT=json.loads('{\n  "archiveName": "hinge-to-combined-delta.tar.gz",\n  "archiveSha256": "216ec569ae1b6eb70f69e95456ce526a62efa0500f3986359fea41e4a56a18c0",\n  "archiveBytes": 89072,\n  "baseline": "exact /tmp/hinge-cap-source (778green normalized hinge14 overlay)",\n  "files": [\n    {\n      "path": "assembly-recording.js",\n      "beforeSha256": "30bb8d3a54e3daaefe4835d5709af63b12da307b0c7e085d101a39ad7eb2a864",\n      "afterSha256": "5f8fc345104e03e87e358bcec9f24d19d1ae0cf0c7769e5753bb96cfcb7d4b4f",\n      "bytes": 11849\n    },\n    {\n      "path": "assembly-review.js",\n      "beforeSha256": "489a16d2349ccb2691f3d1724cf4a6b1e65f9ea8638902872e2903f3f2b269a9",\n      "afterSha256": "52eb488530ef8edc3f3f1535d8240b13e1ab295881abbb26a69e623aa9dce0b8",\n      "bytes": 114313\n    },\n    {\n      "path": "atelier-preview.js",\n      "beforeSha256": "ad2d8b19f4c2a269119f1b739432fc37792ca0409a1e1502340a917b08c1748b",\n      "afterSha256": "2056258d342b2b3d3239a53e6d9be5ef8cb69d29ab4735ac6b7fb5ff345f8382",\n      "bytes": 33575\n    },\n    {\n      "path": "deployment-manifest.json",\n      "beforeSha256": "cdb8b8cc848ab63a460f4f8434dfb5f772fa9dbcbd6c8d65fcd4d0d782840ca6",\n      "afterSha256": "db3beb94883534ec3a3079ad9120912f30c09de6adb51d54b4be5e1cce81a1d6",\n      "bytes": 58567\n    },\n    {\n      "path": "quality-study/viewer-revision.js",\n      "beforeSha256": "7e598a3a90ae6c4acc3fdd3383e6df5e3833109042aadea313f5f5eb2413bbf1",\n      "afterSha256": "71f80a33d3f7a0f921a008e4bbe7678af19a5e4136cfa571c48ac184d03f6766",\n      "bytes": 16181\n    },\n    {\n      "path": "quality-study/viewer-revision.json",\n      "beforeSha256": "571e4b7de6fc8fb5fb55aff8ef637a71a8b65c71156e41bc1a283cc082b35709",\n      "afterSha256": "5eee8293a5106230e23b6cd96e2b79f4d486117381641f4c928b7d064dc4e595",\n      "bytes": 20330\n    },\n    {\n      "path": "scripts/build-atelier-release.mjs",\n      "beforeSha256": "9daacc41891e7f109e3abd3a127f39088304d55cd3958080d984b8195dc026db",\n      "afterSha256": "fd4671ea08d970814cf6076a328690c3801f30f01cb1ac8995695e428f126cb7",\n      "bytes": 15360\n    },\n    {\n      "path": "tests/atelier-capture-handoff.test.mjs",\n      "beforeSha256": "9cf0ebce131615a7b8582da156001f9ad9d7784ddd3003ba8bbe1ca2bdb7bf9d",\n      "afterSha256": "6c1ce9c878c0bcdc7eebd8f889c9792bc062489e9620f0960b21ea8b05429980",\n      "bytes": 6627\n    },\n    {\n      "path": "tests/atelier-release-build.test.mjs",\n      "beforeSha256": "ea68caf2cdcbb251b3724a05675ef9f7375eb5ac0dd2ae81851f8f030cfd83bf",\n      "afterSha256": "ef1a68e9654b5fb4fc03d38dbe801b555a7af72302d7d09b3d8f95d008bf74ca",\n      "bytes": 13882\n    },\n    {\n      "path": "tests/gpu-timing-integration.test.mjs",\n      "beforeSha256": "695da0191349c3396682a1db711c87db89ab8a1083e3e194448b73e3a95c76da",\n      "afterSha256": "df919dd63beb1f07fbd947d9489238d62e405e285adb54bdbd9d4d9ab3fe4dc1",\n      "bytes": 3519\n    },\n    {\n      "path": "tests/recording.test.mjs",\n      "beforeSha256": "bcb3fe118c1fbf9146199185ac571d9938588c6241ed7a4e013de160906544a3",\n      "afterSha256": "dc5ce15895fcb1ffb353f977c4fdfddd962b50239ccf597c692b5b285b6f30df",\n      "bytes": 15917\n    }\n  ],\n  "protected": {\n    "leather-assets/r14/geometry.bin": "d473da297e6dd6565c8c98b3b3e36602f6ed7703c60e51a0205d2ac070825fb0",\n    "leather-assets/r14/leather.gltf": "864fb10cee26bdc3befde7c4a76c4368862ed6c97efb261c768668f493ca8b86",\n    "assembly-leather-authoring-identity.js": "46e3c68a788ff92ff97a06fa82461fb7536941ca448a195678ddaede611d3d0b",\n    "assembly-cap-refinement.js": "e594336c5e370bcbf7bbb7f4da79efd0952e3b3152c7412c4e09685956592ac5",\n    "assembly-cap-delta.js": "65f2a6dcde41da1a3c21c6109f2d36a5d13b076455496c60c53354843dd5a26c",\n    "rebuild/assembly.glb": "04335bab9e05f1610984ceeee355a80e06277ed1f3d7980355a9f8a2146fe6bf",\n    "assembly-escapement.js": "1a14264d953673ca83bb5c3a0307a5a1a1bbf5bf928fba2370867ca1e6209946"\n  },\n  "mustBeAbsent": [\n    "assembly-fork-contact-detour.js"\n  ],\n  "sourceDigest": "947d891f95f7be19219ca3c7f7f2ca78aeae52fef8d41d0a7d42e48421a48063",\n  "published": false\n}\n')
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  while b:=f.read(1048576):h.update(b)
 return h.hexdigest()
a=argparse.ArgumentParser();a.add_argument('root');a.add_argument('archive');a.add_argument('--apply',action='store_true');a.add_argument('--check-result',action='store_true');args=a.parse_args()
assert not(args.apply and args.check_result)
root=Path(args.root).resolve();archive=Path(args.archive).resolve()
assert root.is_dir() and not(root/'.git').exists(),'ephemeral tree required'
if args.apply:
 allowed=Path(os.environ.get('RUNNER_TEMP','/tmp')).resolve();assert allowed in root.parents,'apply requires temporary runner tree'
 assert root.name not in ['hinge-cap-source','watch-combined-no-detour'],'preserve frozen verified candidates; apply to fresh runner copy'
assert sha(archive)==RECEIPT['archiveSha256'] and archive.stat().st_size==RECEIPT['archiveBytes'],'archive identity'
for p,h in RECEIPT['protected'].items():assert sha(root/p)==h,'protected source identity '+p
for p in RECEIPT['mustBeAbsent']:assert not(root/p).exists(),'detour must remain absent'
with tarfile.open(archive,'r:gz') as tf:
 members=tf.getmembers();expected={x['path']:x for x in RECEIPT['files']}
 assert len(members)==len(expected) and {m.name for m in members}==set(expected),'exact member set'
 payload={}
 for m in members:
  assert m.isfile() and not m.name.startswith('/') and '..' not in Path(m.name).parts
  row=expected[m.name];b=tf.extractfile(m).read();assert len(b)==row['bytes'] and hashlib.sha256(b).hexdigest()==row['afterSha256']
  target=root/m.name;assert not target.is_symlink() and all(not p.is_symlink() for p in target.parents if p!=root.parent),'symlink target'
  assert sha(target)==row['afterSha256' if args.check_result else 'beforeSha256'],'unexpected chain source '+m.name
  payload[m.name]=b
 if args.apply:
  # All archive and source guards completed before the first write. Replacements
  # break links; preserve all independent frozen source/candidate trees.
  for p,b in payload.items():
   target=root/p;tmp=target.with_suffix(target.suffix+'.combined-delta-tmp');assert not tmp.exists();tmp.write_bytes(b);tmp.replace(target)
  for p,row in expected.items():assert sha(root/p)==row['afterSha256']
if args.apply or args.check_result:
 revision=json.loads((root/'quality-study/viewer-revision.json').read_text());assert revision['digest']==RECEIPT['sourceDigest']
 # Frozen final generated outputs already describe these exact bytes. Do not
 # regenerate again here or import a component's unrelated generated outputs.
 manifest=json.loads((root/'deployment-manifest.json').read_text())
 for row in manifest['files']:
  p=root/row['path'];assert p.stat().st_size==row['sizeBytes'] and sha(p)==row['sha256'],'final manifest '+row['path']
print('Combined delta '+('applied' if args.apply else 'result verified' if args.check_result else 'applicability verified')+';11 exact project files; no publication')
