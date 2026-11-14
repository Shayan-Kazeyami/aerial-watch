import pathlib,unittest,ast
ROOT=pathlib.Path(__file__).resolve().parent
class Contract(unittest.TestCase):
 def test_matched_source_preserves_visual_and_cleanup_failures(self):
  s=(ROOT/'matched.py').read_text();ast.parse(s)
  self.assertIn("'passed':False",s);self.assertNotIn("['passed']=True",s)
  self.assertIn("}),180)",s);self.assertIn("browser-close",s)
  self.assertIn("await one_arm(p,spec['label']",s)
  self.assertNotIn('await one_arm(p,\'simple-WebGL2\'',s)
 def test_actual_viewport_source_and_state_assertions(self):
  s=(ROOT/'matched.py').read_text()
  for fragment in ["['innerWidth']==W","['stage']['height']-expectedHeight","sourceSHA256","frameParameters","unmaskedRenderer","cameraComparability"]:self.assertIn(fragment,s)
 def test_full_detail_is_bounded_not_unbounded_retry(self):
  s=(ROOT/'matched.py').read_text();self.assertIn('range(36)',s)
  self.assertIn("'viewer:full-detail',wait_detail,185",s)
 def test_prior_cleanup_failure_stops_later_arm(self):
  s=(ROOT/'matched.py').read_text();self.assertIn("R['remainingArmsSkipped']",s)
  self.assertIn("assert data['observedRenderer']['unmaskedRenderer']",s)
if __name__=='__main__':unittest.main()
