#!/usr/bin/env python3
"""Restore only a verified seven-file private return-material overlay; no network or git."""
import hashlib,json,os,shutil,sys,tarfile,tempfile
from pathlib import Path
EXPECTED_ARCHIVE='0187ae01483b13d10deed5215edabb2dcbcfb6227a0907aeebd5b1dfff06bd78'
EXPECTED_BYTES=5480846
FILES={
 'install-return-material-candidate.mjs':(9952,'6ee98a8e34cbad2c095ff61f798fff30837b79a4e0802dfe211555d527e52c15'),
 'candidate/leather.gltf':(12350,'1d1555bca6404951101d32507b5e3f417baad474fed59a3a9b7706ade755bf5d'),
 'candidate/geometry.bin':(9123684,'ae62f1a0e32f2bbe0e2591dff0a0664d676102e12b8f71db8e5adc1912f309c4'),
 'hinge-candidate-integration.test.mjs':(2945,'a617447186a13ff1b2099c291070ccf8966174854a3e72495431c189db702707'),
 'thread-optimization.test.mjs':(2817,'15bc986adaf90d35df0985afaeb82bea798b4ac419f3e00009826f1d32bf142b'),
 'leather-rim-roll.test.mjs':(2327,'1d1f6603307b1ef87cf8018150abbd6fe5ab08368f9ed355722ef82724f1fb53'),
 'terminal-ramp-integration.test.mjs':(6117,'14cc5b9db71c6ca397e7400eb6330e337d830d019b59144aa62b1eeb4fe9a1c5'),
}
def main():
 if len(sys.argv)!=4:raise SystemExit('usage: restore-material.py INPUT_DIR EMPTY_OUTPUT_DIR RECEIPT_PATH')
 chunks=Path(sys.argv[1]);out=Path(sys.argv[2]);receipt=Path(sys.argv[3]);expected_names=[f'material-source.part-{i:02d}' for i in range(11)]
 if sorted(p.name for p in chunks.iterdir())!=expected_names:raise ValueError('Expected exactly parts 00..10, no other files')
 if out.exists():raise FileExistsError(f'Output already exists: {out}')
 out.parent.mkdir(parents=True,exist_ok=True);receipt.parent.mkdir(parents=True,exist_ok=True)
 with tempfile.TemporaryDirectory(prefix='.material-restore-',dir=out.parent) as td:
  archive=Path(td)/'overlay.tar.gz';digest=hashlib.sha256();total=0
  with archive.open('xb') as target:
   for name in expected_names:
    p=chunks/name
    if p.is_symlink() or not p.is_file():raise ValueError('Invalid chunk '+name)
    with p.open('rb') as src:
     while part:=src.read(1024*1024):
      total+=len(part)
      if total>EXPECTED_BYTES:raise ValueError('Archive exceeds expected length')
      digest.update(part);target.write(part)
  if total!=EXPECTED_BYTES or digest.hexdigest()!=EXPECTED_ARCHIVE:raise ValueError('Archive SHA256/length mismatch')
  stage=Path(td)/'source';stage.mkdir();seen=set();verified=[]
  with tarfile.open(archive,'r:gz') as tar:
   for member in tar:
    name=member.name
    if name not in FILES or name in seen or not member.isfile() or member.issym() or member.islnk():raise ValueError('Unexpected, duplicate or non-regular archive member: '+name)
    size,expected=FILES[name]
    if member.size!=size:raise ValueError('Member size mismatch: '+name)
    dest=stage.joinpath(*name.split('/'));dest.parent.mkdir(parents=True,exist_ok=True);h=hashlib.sha256();written=0;src=tar.extractfile(member)
    if src is None:raise ValueError('Unreadable member: '+name)
    with src,dest.open('xb') as target:
     while part:=src.read(1024*1024):
      written+=len(part)
      if written>size:raise ValueError('Oversized member: '+name)
      h.update(part);target.write(part)
    if written!=size or h.hexdigest()!=expected:raise ValueError('Member checksum mismatch: '+name)
    seen.add(name);verified.append({'path':name,'bytes':size,'sha256':expected})
  if seen!=set(FILES):raise ValueError('Archive member set mismatch: '+repr(sorted(set(FILES)-seen)))
  # Atomic visibility of a fully verified directory. Both are runner-local.
  os.rename(stage,out)
 result={'archiveSha256':EXPECTED_ARCHIVE,'archiveBytes':total,'chunks':expected_names,'members':sorted(verified,key=lambda x:x['path']),'published':False};receipt.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
