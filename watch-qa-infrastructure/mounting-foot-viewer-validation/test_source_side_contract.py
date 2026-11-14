from pathlib import Path
import unittest,json,ast
Q=Path(__file__).resolve().parent
class SourceOnly(unittest.TestCase):
 def test_no_candidate_actions(self):
  s=(Q/'browser-driver-source-side.py').read_text();self.assertNotIn('.activate()',s);self.assertNotIn('.prepare(',s);self.assertIn("report['accepted']=False",s);self.assertIn("frame(name,5)",s)
 def test_strict_gates_and_beforethrow_diagnostics(self):
  s=(Q/'camera-hook-source-side.js').read_text();self.assertIn("'rendered target ROI not framed'",s);self.assertLess(s.index('window.__mountingFootBlockerDiagnostic='),s.index("if(!visibleHits)throw"));self.assertIn('transmission:m.transmission??0',s);self.assertIn('const first=hits[0]',s)
 def test_source_geometry_not_packaged(self):
  r=Q/'qa-source-side-viewer/preview-b/releases/e79b22365b4874327d308eca789326fbea0da8d717ffca20da80b611e36b39c6';self.assertFalse(any(r.glob('qa-foot-*.json')));self.assertTrue((r/'assembly-review.js').exists())
 def test_arm_restore_and_cleanup(self):
  s=(Q/'browser-driver-source-side.py').read_text();ast.parse(s);self.assertIn('asyncio.timeout(600)',s);self.assertIn("'camera-restore'",s);self.assertIn('browser.close()',s);self.assertIn("report['cameraCleanupFailure']",s)
if __name__=='__main__':unittest.main()
