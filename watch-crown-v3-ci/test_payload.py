import unittest,tempfile,pathlib,subprocess,sys,os,json,hashlib,shutil
SCRIPT=pathlib.Path(__file__).with_name('payload.py').resolve();prefixes=['watch-normal-stream-build/staging','watch-crown-key-build/staging']
class Tests(unittest.TestCase):
 def test_roundtrip_and_no_overwrite(self):
  with tempfile.TemporaryDirectory()as td:
   p=pathlib.Path(td)
   for pre in prefixes:
    for i in range(303):
     f=p/pre/str(i);f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes(str(i).encode())
   r=subprocess.run([sys.executable,str(SCRIPT),'pack'],cwd=p,capture_output=True,text=True,timeout=20);self.assertEqual(r.returncode,0,r.stderr);v=json.loads(r.stdout);env=dict(os.environ,EXPECTED_ARCHIVE_SHA256=v['archive_sha256'],EXPECTED_MANIFEST_SHA256=v['manifest_sha256'])
   r=subprocess.run([sys.executable,str(SCRIPT),'unpack'],cwd=p,env=env,capture_output=True,timeout=20);self.assertNotEqual(r.returncode,0)
   for pre in prefixes:shutil.rmtree(p/pre)
   r=subprocess.run([sys.executable,str(SCRIPT),'unpack'],cwd=p,env=env,capture_output=True,timeout=20);self.assertEqual(r.returncode,0,r.stderr)
   for pre in prefixes:
    for i in range(303):self.assertEqual((p/pre/str(i)).read_bytes(),str(i).encode())
 def test_bad_digest(self):
  with tempfile.TemporaryDirectory()as td:
   p=pathlib.Path(td);(p/'crown-payload').mkdir();(p/'crown-payload/payload.json').write_text('{}');(p/'crown-payload/payload.tar.gz').write_bytes(b'x')
   r=subprocess.run([sys.executable,str(SCRIPT),'unpack'],cwd=p,env=dict(os.environ,EXPECTED_ARCHIVE_SHA256='wrong',EXPECTED_MANIFEST_SHA256='wrong'),capture_output=True,timeout=10);self.assertNotEqual(r.returncode,0)
if __name__=='__main__':unittest.main()
