import hashlib
ORIGINAL='91fcb25fbcc71e7e259dc603ba019d8c626e8506399dc14cf3c12075cc0fa4ee'
CANDIDATE='f890d65acb36f7bd3da53e3c5e5ed78b62a803bece14f196041696efec359a22'
def patched(source):
 assert hashlib.sha256(source).hexdigest()==ORIGINAL
 needle=b'near:camera.near,fill:.94'
 assert source.count(needle)==1
 result=source.replace(needle,b'near:.1,fill:.94')
 assert hashlib.sha256(result).hexdigest()==CANDIDATE
 return result
