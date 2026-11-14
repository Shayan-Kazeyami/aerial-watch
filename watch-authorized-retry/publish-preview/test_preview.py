import pathlib,tempfile,subprocess,os,unittest
from build_preview import assert_additive,wrapper_files,RID,push_command,BRANCH
class Tests(unittest.TestCase):
 def test_atomic_create_lease_rejects_intervening_branch(self):
  with tempfile.TemporaryDirectory()as d:
   p=pathlib.Path(d);bare=p/'remote.git';work=p/'work';work.mkdir()
   subprocess.run(['git','init','--bare','-q',str(bare)],check=True)
   def git(*a):return subprocess.check_output(['git','-C',str(work),*a],stderr=subprocess.DEVNULL)
   git('init','-q');git('config','user.email','test@example.invalid');git('config','user.name','test');git('remote','add','origin',str(bare))
   (work/'file').write_text('base');git('add','file');git('commit','-qm','base');base=git('rev-parse','HEAD').decode().strip()
   # A competing writer creates the branch after our preliminary absence check.
   git('push','-q','origin',base+':refs/heads/'+BRANCH)
   (work/'file').write_text('candidate');git('commit','-qam','candidate');candidate=git('rev-parse','HEAD').decode().strip()
   command=push_command(candidate);self.assertIn('--force-with-lease=refs/heads/'+BRANCH+':',command)
   result=subprocess.run(command,cwd=work,capture_output=True);self.assertNotEqual(result.returncode,0)
   self.assertEqual(git('ls-remote','origin','refs/heads/'+BRANCH).decode().split()[0],base)
 def test_existing_entries_preserved(self):
  old={'index.html':{'sha':'old'}};new={'new':{'sha':'new'}}
  assert_additive(old,{**old,**new},new)
  with self.assertRaises(AssertionError):assert_additive(old,{'index.html':{'sha':'changed'},**new},new)
  with self.assertRaises(AssertionError):assert_additive(old,{**old,**new,'extra':{'sha':'x'}},new)
 def test_wrapper_only_rebases_release_prefix(self):
  with tempfile.TemporaryDirectory()as d:
   p=pathlib.Path(d);old='./preview-b/releases/'+RID+'/atelier-preview.html'
   (p/'index.html').write_text('html '+old);(p/'watch-home-coordinated-successor.js').write_text('const RELEASE='+repr(old));(p/'watch-home-loading-v4.css').write_text('css')
   result=wrapper_files(p);self.assertIn(b'../../preview-b/releases/',result['index.html'])
   self.assertEqual(result['watch-home-loading-v4.css'],b'css')
 def test_real_temporary_git_tree_addition_does_not_touch_index(self):
  with tempfile.TemporaryDirectory()as d:
   def git(*a,env=None):return subprocess.check_output(['git','-C',d,*a],env=env)
   git('init','-q');git('config','user.email','test@example.invalid');git('config','user.name','test')
   p=pathlib.Path(d);(p/'index.html').write_text('old');git('add','index.html');git('commit','-qm','base');base=git('rev-parse','HEAD').strip()
   original=git('write-tree');(p/'new.txt').write_text('new');blob=git('hash-object','-w','new.txt').decode().strip()
   env={**os.environ,'GIT_INDEX_FILE':str(p/'temporary-index')};git('read-tree',base.decode(),env=env);git('update-index','--add','--cacheinfo','100644',blob,'new.txt',env=env)
   self.assertNotEqual(git('write-tree',env=env),original);self.assertEqual(git('write-tree'),original)
if __name__=='__main__':unittest.main()
