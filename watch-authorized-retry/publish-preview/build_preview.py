"""Prepare/push a NEW preview branch only. Never writes main or Pages settings."""
import pathlib,hashlib,json,subprocess,tempfile,os,datetime
Q=pathlib.Path('coordinated-release-successor')
RID='011614d052b49dd32652ec25e31bd471addef053bfda24510d7741485fe37192'
PREFIX='previews/watch-0116-20261114'
BRANCH='preview/watch-0116-20261114'
OUT=pathlib.Path('watch-authorized-retry/publish-preview/evidence')

def git(*args,env=None):
    return subprocess.check_output(['git',*args],env=env)
def tree_map(ref):
    result={}
    for entry in git('ls-tree','-rz',ref).split(b'\0'):
        if not entry:continue
        meta,path=entry.split(b'\t',1);mode,kind,sha=meta.decode().split()
        result[path.decode()]={'mode':mode,'type':kind,'sha':sha}
    return result
def assert_additive(before,after,additions):
    assert set(after)-set(before)==set(additions),'Unexpected new/deleted path set'
    for path,value in before.items():assert after.get(path)==value,('Existing path changed',path)
    for path,value in additions.items():assert after[path]==value,('Addition mismatch',path)
def file_hashes(path):
    size=path.stat().st_size;h=hashlib.sha256();g=hashlib.sha1(b'blob '+str(size).encode()+b'\0')
    with path.open('rb')as stream:
        while block:=stream.read(1024*1024):h.update(block);g.update(block)
    return size,h.hexdigest(),g.hexdigest()
def wrapper_files(stage):
    index=(stage/'index.html').read_bytes();loader=(stage/'watch-home-coordinated-successor.js').read_bytes()
    old=b'./preview-b/releases/'+RID.encode()+b'/'
    assert index.count(old)==1 and loader.count(old)==1
    return {'index.html':index.replace(old,b'../../preview-b/releases/'+RID.encode()+b'/'),
            'watch-home-coordinated-successor.js':loader.replace(old,b'../../preview-b/releases/'+RID.encode()+b'/'),
            'watch-home-loading-v4.css':(stage/'watch-home-loading-v4.css').read_bytes()}
def push_command(commit):
    ref='refs/heads/'+BRANCH
    # Empty expected value atomically requires the remote branch to be absent.
    return ['git','push','--force-with-lease='+ref+':','origin',commit+':'+ref]

def main():
    assert (Q/'release-id.txt').read_text().strip()==RID
    assert BRANCH.startswith('preview/') and PREFIX.startswith('previews/')
    OUT.mkdir(parents=True,exist_ok=True)
    subprocess.run(['git','fetch','--no-tags','--depth=1','origin','main'],check=True)
    base=git('rev-parse','refs/remotes/origin/main').decode().strip();before=tree_map(base)
    exists=subprocess.run(['git','ls-remote','--exit-code','--heads','origin','refs/heads/'+BRANCH],capture_output=True)
    assert exists.returncode==2,'Output preview branch exists or remote lookup failed; never overwrite'
    stage=Q/'staging';release=stage/'preview-b/releases'/RID
    manifest=json.loads((release/'deployment-manifest.json').read_text());assert manifest['releaseId']==RID
    additions={};file_proofs=[]
    def add(path,source,expected=None):
        assert path not in before and path not in additions,('Refuse overwrite',path)
        assert path.startswith('preview-b/releases/'+RID+'/') or path.startswith(PREFIX+'/'),path
        assert source.is_file() and not source.is_symlink()
        size,sha,blob=file_hashes(source)
        if expected:assert size==expected['sizeBytes'] and sha==expected['sha256'],path
        stored=git('hash-object','-w',str(source)).decode().strip();assert stored==blob
        additions[path]={'mode':'100644','type':'blob','sha':blob}
        file_proofs.append({'path':path,'sizeBytes':size,'sha256':sha,'gitBlob':blob})
    for spec in manifest['localFiles']:add('preview-b/releases/'+RID+'/'+spec['path'],release/spec['path'],spec)
    for spec in manifest['references']:
        path='preview-b/releases/'+spec['ownerReleaseId']+'/'+spec['path']
        source=stage/path;size,sha,blob=file_hashes(source)
        assert size==spec['sizeBytes'] and sha==spec['sha256'] and before[path]['sha']==blob,('Reference drift',path)
    for name in ['deployment-manifest.json','release-receipt.json']:add('preview-b/releases/'+RID+'/'+name,release/name)
    wrapper=OUT/'wrapper';wrapper.mkdir(exist_ok=True)
    for name,content in wrapper_files(stage).items():
        p=wrapper/name;p.write_bytes(content);add(PREFIX+'/'+name,p)
    info={'kind':'Experimental separate preview; existing default site unchanged','release':RID,'baseMain':base,
          'frozenQACommit':'48ca59ef81ee960ff78d598c3f512df96411848c',
          'limitations':'Primary five route gates passed; complementary UI/screenshot/cleanup timeouts remain unresolved. Not default release promotion or full visual acceptance.'}
    p=wrapper/'preview-info.json';p.write_text(json.dumps(info,indent=2)+'\n');add(PREFIX+'/preview-info.json',p)
    with tempfile.TemporaryDirectory(prefix='preview-index-')as directory:
        env={**os.environ,'GIT_INDEX_FILE':str(pathlib.Path(directory)/'index')}
        git('read-tree',base,env=env)
        for path,value in additions.items():git('update-index','--add','--cacheinfo',value['mode'],value['sha'],path,env=env)
        tree=git('write-tree',env=env).decode().strip()
    after=tree_map(tree);assert_additive(before,after,additions)
    subprocess.run(['git','config','user.name','github-actions[bot]'],check=True)
    subprocess.run(['git','config','user.email','41898282+github-actions[bot]@users.noreply.github.com'],check=True)
    commit=git('commit-tree',tree,'-p',base,'-m','Add immutable experimental Watch0116 preview; preserve every existing site path').decode().strip()
    proof={'time':datetime.datetime.now(datetime.timezone.utc).isoformat(),'baseMain':base,'tree':tree,'commit':commit,
           'outputBranch':BRANCH,'previewPrefix':PREFIX,'release':RID,'existingPathsPreserved':len(before),
           'newPaths':len(additions),'addedPaths':file_proofs,'referencesVerified':len(manifest['references']),
           'oldEntriesByteIdentityPreserved':True,'mainWritten':False,'pagesSettingsChanged':False,
           'previewURL':'https://shayan-kazeyami.github.io/aerial-watch/'+PREFIX+'/'}
    (OUT/'additive-proof.json').write_text(json.dumps(proof,indent=2))
    # Only a brand-new preview branch. Main publication is a separate connector action after review.
    subprocess.run(push_command(commit),check=True)
    print(json.dumps({k:v for k,v in proof.items()if k!='addedPaths'},indent=2))
if __name__=='__main__':main()
