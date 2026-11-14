import pathlib,unittest,ast
ROOT=pathlib.Path(__file__).resolve().parent
class Contract(unittest.TestCase):
 def test_finite_single_attempt_arms_and_no_approval(self):
  s=(ROOT/'ab.py').read_text();ast.parse(s)
  self.assertEqual(s.count("await one_arm(p,'simple-WebGL2'"),1)
  self.assertEqual(s.count("await one_arm(p,'exact-viewer'"),1)
  self.assertIn("'passed':False",s);self.assertNotIn("['passed']=True",s)
  self.assertIn("':CDP-capture-dispatch'",s)
  self.assertIn("}),180)",s)
  self.assertNotIn('force=True',s);self.assertNotIn('route(',s)
 def test_control_has_real_gl_and_no_viewer_dependency(self):
  s=(ROOT/'control.html').read_text()
  self.assertIn("getContext('webgl2'",s);self.assertIn('gl.drawArrays',s)
  self.assertIn('requestAnimationFrame(render)',s);self.assertNotIn('assemblyInspect',s)
 def test_no_continuous_renderer_probe(self):
  s=(ROOT/'ab.py').read_text();self.assertNotIn('heartbeat',s.replace('heartbeat.',''))
  self.assertIn('interval=15',s)
if __name__=='__main__':unittest.main()
