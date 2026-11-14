import unittest,copy
from gates import assert_snapshot,stable,FULL,assert_same_texture_bindings
class Tests(unittest.TestCase):
 def fixture(self):
  return {'detail':{'required':True,'ready':True,'phase':'full','installedDetail':'full','activeNormalIdentity':{'bytes':16562348,'sha256':FULL,'width':4096,'height':4096,'mipLevels':13,'verified':True}},'inspect':{'failed':False,'loading':False,'presentation':{'interactive':True},'finish':True,'crystals':True,'animation':False,'interiorAnimation':False,'renderQuality':'balanced','view':'front','inspectionDisplay':{}},'configuration':{'camera':{},'renderer':{},'premiumFace':{},'date':'one','progressiveNormalMetrics':{'ms':1}},'bindings':[{'name':'R14','visible':True,'effectiveVisible':True,'materials':[{'normalUUID':'one','width':4096,'height':4096,'mipLevels':13,'normalScale':[1,1]}]}]}
 def test_valid(self):assert_snapshot(self.fixture())
 def test_empty(self):
  s=self.fixture();s['bindings']=[]
  with self.assertRaises(AssertionError):assert_snapshot(s)
 def test_invisible(self):
  s=self.fixture();s['bindings'][0]['effectiveVisible']=False
  with self.assertRaises(AssertionError):assert_snapshot(s)
 def test_missing_map(self):
  s=self.fixture();s['bindings'][0]['materials'][0]['normalUUID']=None
  with self.assertRaises(AssertionError):assert_snapshot(s)
 def test_no_material(self):
  s=self.fixture();s['bindings'][0]['materials']=[]
  with self.assertRaises(AssertionError):assert_snapshot(s)
 def test_low_texture(self):
  s=self.fixture();s['bindings'][0]['materials'][0]['width']=2048
  with self.assertRaises(AssertionError):assert_snapshot(s)
 def test_same_page_binding_replacement_rejected(self):
  a=self.fixture();b=copy.deepcopy(a);assert_same_texture_bindings(a,b);b['bindings'][0]['materials'][0]['normalUUID']='replacement';self.assertEqual(stable(a),stable(b))
  with self.assertRaises(AssertionError):assert_same_texture_bindings(a,b)
 def test_stable_explicit(self):
  a=self.fixture();b=copy.deepcopy(a);b['configuration']['date']='two';b['configuration']['progressiveNormalMetrics']['ms']=2;b['bindings'][0]['materials'][0]['normalUUID']='two';self.assertEqual(stable(a),stable(b));b['configuration']['camera']={'zoom':2};self.assertNotEqual(stable(a),stable(b))
if __name__=='__main__':unittest.main()
