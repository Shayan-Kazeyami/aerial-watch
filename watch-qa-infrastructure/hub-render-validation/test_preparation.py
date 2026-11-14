import unittest,json,hashlib
from pathlib import Path
Q=Path(__file__).resolve().parent
class Contract(unittest.TestCase):
 def test_all_fixture_bytes(self):
  for f in json.loads((Q/'IDENTITIES.json').read_text()):
   b=(Q/'fixture'/f['path']).read_bytes();self.assertEqual(len(b),f['bytes']);self.assertEqual(hashlib.sha256(b).hexdigest(),f['sha256'])
 def test_source_and_candidate_preserved(self):
  root=Q.parents[1];self.assertEqual((Q/'fixture/candidate-design.js').read_bytes(),(Q/'inputs/candidate-design.mjs').read_bytes().replace(b"'./three.mjs'",b"'./vendor/three.module.js'"))
 def test_required_gates(self):
  s=(Q/'fixture.js').read_text()
  for gate in ['ids.length!==5','foreground>=768*768*.01','result.aa===0&&result.ab===0','counts.at(-1)===baseline','gl.getError()===gl.NO_ERROR','Math.abs(p.x)<=.8','window.meta.width===768'] :self.assertIn(gate,s)
 def test_bounds_cleanup_and_no_remote(self):
  s=(Q/'run.py').read_text();self.assertIn('asyncio.timeout(300)',s);self.assertIn('browser.close()',s);self.assertIn("report['cleanupFailure']",s);self.assertNotIn('github',s);self.assertNotIn('retry',s)
if __name__=='__main__':unittest.main()
