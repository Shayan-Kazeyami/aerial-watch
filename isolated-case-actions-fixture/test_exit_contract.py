"""AST-isolated exit-policy regression: never invokes main/Popen/browser/server."""
import ast,unittest
from pathlib import Path
R=Path(__file__).resolve().parent
class ExitContract(unittest.TestCase):
 def policy(self,file,report):
  tree=ast.parse((R/file).read_text());main=next(x for x in tree.body if isinstance(x,(ast.FunctionDef,ast.AsyncFunctionDef))and x.name=='main');node=main.body[-1];self.assertIsInstance(node,ast.Return)
  return eval(compile(ast.Expression(node.value),file,'eval'),{'report':report})
 def test_status_failclosed(self):
  for file,good in [('watchdog.py','BOOTSTRAP_ONLY_COMPLETED'),('browser_harness.py','BOOTSTRAP_ONLY_COMPLETED_NOT_LIFECYCLE_PASS')]:
   self.assertEqual(self.policy(file,{'status':good,'cleanup_errors':[]}),0)
   for status in ['STARTING','HOLD_HARNESS_RESULT','STOPPED','STOPPED_FIRST_FAILURE','HOLD_BROWSER_CLOSE_FAILED','HOLD_CLEANUP_FAILED','NOT_COMPLETED',None,'PASS']:
    self.assertNotEqual(self.policy(file,{'status':status,'cleanup_errors':[]}),0)
   self.assertNotEqual(self.policy(file,{'status':good,'cleanup_errors':['failure']}),0)
 def test_evidence_before_exit(self):
  for file in ['watchdog.py','browser_harness.py']:
   tree=ast.parse((R/file).read_text());main=next(x for x in tree.body if isinstance(x,(ast.FunctionDef,ast.AsyncFunctionDef))and x.name=='main');self.assertIsInstance(main.body[-2],ast.Try)
   final=main.body[-2].finalbody
   self.assertTrue(any(isinstance(x,ast.Call)and isinstance(x.func,ast.Attribute)and x.func.attr=='write_text'for n in final for x in ast.walk(n)))
   guard=tree.body[-1];self.assertIsInstance(guard,ast.If);self.assertIsInstance(guard.body[0],ast.Raise)
if __name__=='__main__':unittest.main()
