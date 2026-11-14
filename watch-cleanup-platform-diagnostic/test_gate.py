import unittest,copy
from gate import accepted,EXPECTED
class GateTests(unittest.TestCase):
 def rows(self):return [{'case':n,'started':True,'before':{'state':'present'},'after':{'state':'absent'},'cleanup':{'status':'signals-completed-leader-reaped','leader_reaped':True,'errors':[]},'final_kill':'absent','final_returncode':0,'resistant_child_pid':123}for n in EXPECTED]
 def test_complete(self):self.assertTrue(accepted(self.rows()))
 def test_initial_eperm(self):
  r=self.rows();r[0]['before']={'state':'unverified','errno':1};self.assertFalse(accepted(r))
 def test_initial_absent_or_missing(self):
  for state in ['absent',None]:
   r=self.rows();r[0]['before']={'state':state};self.assertFalse(accepted(r))
 def test_case_completeness(self):
  r=self.rows()
  for x in [[],r[:1],r+[r[0]],[r[0],r[0]],None,[None,r[1]]]:self.assertFalse(accepted(x))
 def test_started(self):
  for v in [False,None,1]:
   r=self.rows();r[0]['started']=v;self.assertFalse(accepted(r))
 def test_cleanup_error_even_with_success_label(self):
  r=self.rows();r[0]['cleanup']['errors']=[{'errno':1}];self.assertFalse(accepted(r))
 def test_after_eperm(self):
  r=self.rows();r[0]['after']={'state':'unverified','errno':1};self.assertFalse(accepted(r))
 def test_final_failures(self):
  for k,v in [('final_kill',{'errno':1}),('final_wait_error','timeout'),('exception','x'),('final_returncode',None)]:
   r=self.rows();r[0][k]=v;self.assertFalse(accepted(r))
 def test_handshake_required(self):
  r=self.rows();del r[1]['resistant_child_pid'];self.assertFalse(accepted(r))
if __name__=='__main__':unittest.main()
