#!/usr/bin/env python3
"""Restore only a verified seven-file private terminal overlay; no network or git."""
import hashlib,json,os,shutil,sys,tarfile,tempfile
from pathlib import Path
EXPECTED_ARCHIVE='2b6bc3af75ebdc5ea620d89486515ec8db09248c966e383da18544dc87926243'
EXPECTED_BYTES=5466042
FILES={
 'install-terminal-candidate.mjs':(9732,'163494db9cbdd697a4212982bd4c5d9d3f3a35fa85408803a27450e8f2a42964'),
 'candidate/leather.gltf':(12351,'e173702d5f279add7e8c726aea8f159f39245fa2a0a9f78764bb9dd6a12ac2cc'),
 'candidate/geometry.bin':(9096768,'c97e6e5e2f23acb65ccf0c10d0a844924fb161bb38d7966e72db43c7ced1bf29'),
 'hinge-candidate-integration.test.mjs':(2943,'4446476ae475a0c7f57d4731009271074f5a50244e89dd424d60c12e9f16391e'),
 'thread-optimization.test.mjs':(2806,'d8496b55c6a5c7e8ad1c2d62de980b543db66faf829901f934a2b89b53fc5e43'),
 'leather-rim-roll.test.mjs':(2327,'890952bd80235f9592300f065b5c5f8fa821eab89ab284c9635c34a20eebd798'),
 'terminal-ramp-integration.test.mjs':(6105,'2cb3729622fd98345aaa5daa3e56f3b4b4ae53f799b5f37185f71fc3758224bd'),
}
def main():
 if len(sys.argv)!=4:raise SystemExit('usage: restore-terminal.py INPUT_DIR EMPTY_OUTPUT_DIR RECEIPT_PATH')
 chunks=Path(sys.argv[1]);out=Path(sys.argv[2]);receipt=Path(sys.argv[3]);expected_names=[f'terminal-source.part-{i:02d}' for i in range(11)]
 if sorted(p.name for p in chunks.iterdir())!=expected_names:raise ValueError('Expected exactly parts 00..10, no other files')
 if out.exists():raise FileExistsError(f'Output already exists: {out}')
 out.parent.mkdir(parents=True,exist_ok=True);receipt.parent.mkdir(parents=True,exist_ok=True)
 with tempfile.TemporaryDirectory(prefix='.terminal-restore-',dir=out.parent) as td:
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
