import unittest
from unittest.mock import patch
from coordinator import cleanup_both,CleanupUnverified
class Tests(unittest.TestCase):
 def test_exact_bounds_both(self):
  with patch('coordinator.cleanup',return_value={'status':'verified'})as c:
   r=cleanup_both('D','S')
  self.assertEqual([x.args for x in c.call_args_list],[('D',),('S',)])
  self.assertTrue(all(x.kwargs=={'grace':.5,'post_grace':1.0}for x in c.call_args_list));self.assertEqual(set(r),{'driver','server'})
 def test_driver_failure_preserved_and_server_attempted(self):
  with patch('coordinator.cleanup',side_effect=[CleanupUnverified({'status':'unverified','errors':[{'errno':1}]}),{'status':'verified'}])as c:
   with self.assertRaises(CleanupUnverified)as e:cleanup_both('D','S')
  self.assertEqual(c.call_count,2);self.assertEqual(e.exception.report['failed'],['driver']);self.assertEqual(e.exception.report['processes']['driver']['errors'][0]['errno'],1)
 def test_both_fail_preserved(self):
  with patch('coordinator.cleanup',side_effect=[RuntimeError('D'),RuntimeError('S')]):
   with self.assertRaises(CleanupUnverified)as e:cleanup_both('D','S')
  self.assertEqual(e.exception.report['failed'],['driver','server'])
 def test_none_before_spawn(self):self.assertEqual(cleanup_both(None,None),{'driver':{'status':'not-started'},'server':{'status':'not-started'}})
if __name__=='__main__':unittest.main()
