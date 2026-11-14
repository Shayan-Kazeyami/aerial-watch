import hashlib,json,pathlib
proof=json.loads(pathlib.Path('isolated-touch-selection-fix/patch-proof.json').read_text())
def patched(source):
 assert hashlib.sha256(source).hexdigest()=='91fcb25fbcc71e7e259dc603ba019d8c626e8506399dc14cf3c12075cc0fa4ee'
 assert source.count(b'near:camera.near,fill:.94')==1
 source=source.replace(b'near:camera.near,fill:.94',b'near:.1,fill:.94')
 assert hashlib.sha256(source).hexdigest()==proof['inputSHA256']
 assert source.count(proof['old'].encode())==1
 source=source.replace(proof['old'].encode(),proof['new'].encode())
 assert hashlib.sha256(source).hexdigest()==proof['candidateSHA256']
 return source
