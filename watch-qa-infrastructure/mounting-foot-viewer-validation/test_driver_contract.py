from pathlib import Path
import unittest,ast
Q=Path(__file__).resolve().parent
class DriverContract(unittest.TestCase):
 def test_candidate_path(self):
  for label in ['350','110','250']:self.assertTrue((Q.parents[1]/'isolated-mounting-feet-exact-index'/f'{label}.candidate.json').is_file())
 def test_required_identity_gates(self):
  s=(Q/'browser-driver.py').read_text();h=(Q/'camera-hook.js').read_text();self.assertIn("picks[0]['identity']==picks[1]['identity']==picks[2]['identity']",s);self.assertIn('materialIndex:first.face.materialIndex',h);self.assertIn('world:mesh.matrixWorld.toArray()',h);self.assertIn("shaderKey:m.customProgramCacheKey()",h)
 def test_syntax_and_bounds(self):
  ast.parse((Q/'browser-driver.py').read_text());ast.parse((Q/'prepare-viewer.py').read_text());s=(Q/'browser-driver.py').read_text();self.assertIn('asyncio.timeout(1200)',s);self.assertIn("report['primaryFailure']",s);self.assertIn("report['cleanupFailure']",s);self.assertIn('browser.close()',s)
if __name__=='__main__':unittest.main()
