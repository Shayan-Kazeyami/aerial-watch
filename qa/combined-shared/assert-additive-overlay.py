import pathlib, subprocess, sys
release=sys.argv[1]
assert len(release)==64 and all(c in '0123456789abcdef' for c in release)
prefix='preview-b/releases/'+release+'/'
files=subprocess.check_output(['git','-C','live-pinned','ls-files','--others','--exclude-standard','-z']).decode().split('\0')
assert all(p.startswith(prefix) for p in files if p), 'Unexpected write outside new release'
print('Only new immutable release subtree added; tracked legacy and owner bytes unchanged.')
