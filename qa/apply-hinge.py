import pathlib,hashlib,tarfile,io
root=pathlib.Path('candidate');parts=pathlib.Path('qa/inputs/hinge-central')
b=b''.join((parts/f'{i:02d}.part').read_bytes() for i in range(11))
assert len(b)==5234404 and hashlib.sha256(b).hexdigest()=='2347fd01d7165161f2f777199109949cd06f08eef4ee4fbb3931686fc1b5ad66'
t=tarfile.open(fileobj=io.BytesIO(b),mode='r:gz');members=t.getmembers();assert len(members)==14
for m in members:
 p=pathlib.PurePosixPath(m.name);assert m.isfile() and not p.is_absolute() and '..' not in p.parts
existing=sorted(m.name for m in members if (root/m.name).exists());assert len(existing)==13
before='\n'.join(p+':'+hashlib.sha256((root/p).read_bytes()).hexdigest() for p in existing)
assert hashlib.sha256(before.encode()).hexdigest()=='b455782e6cc1ee07a8dcecc96df5d9e24c48cd9b40b42ec6809ee529d9e74c9f', 'Non-pristine source overlay rejected'
for m in members:
 p=root/m.name;p.parent.mkdir(parents=True,exist_ok=True);tmp=p.with_name(p.name+'.hinge-tmp');tmp.write_bytes(t.extractfile(m).read());tmp.replace(p)
print('Exact 14-file central hinge overlay verified and applied; not cap-junction repair.')
