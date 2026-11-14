import pathlib,ast,unittest
ROOT=pathlib.Path(__file__).resolve().parent
class Contract(unittest.TestCase):
 def test_single_arm_and_no_release_approval(self):
  s=(ROOT/'diagnostic.py').read_text();ast.parse(s)
  self.assertEqual(s.count('await one_arm(p,label,'),1)
  self.assertIn("len(R['arms'])!=1",s);self.assertIn("'passed':False",s)
  self.assertNotIn("['passed']=True",s)
 def test_capture_and_cleanup_required(self):
  s=(ROOT/'diagnostic.py').read_text();self.assertIn("}),180)",s)
  self.assertIn("not a.get('unloadFailure')",s);self.assertIn("not a['cleanupFailure']",s)
  self.assertIn('normal_unload_then_close(page,browser',s)
 def test_independent_runner_matrix_is_not_mobile_claim(self):
  s=(ROOT/'workflow.yml').read_text();self.assertIn('release: [published-e79, frozen-0116]',s)
  self.assertNotIn('matrix.kind',s)
  self.assertIn("KIND='desktop'",(ROOT/'diagnostic.py').read_text())
if __name__=='__main__':unittest.main()
