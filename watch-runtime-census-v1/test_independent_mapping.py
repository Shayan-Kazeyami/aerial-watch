import sys,json,unittest
from pathlib import Path
sys.path.insert(0,str(Path('watch-runtime-census-v1').resolve()))
from map_census import map_rows
T=json.loads(Path('watch-runtime-census-v1/TRACKER_INPUT.json').read_text())
def mesh(uid,name,collections,index=None):return {'id':uid,'name':name,'collections':[{'name':c,'index':0}for c in collections],'userData':{}if index is None else {'sourceIndex':index},'effectivelyVisible':True,'batchSuppressedSource':False,'geometry':'g'}
def out(q,ms):return next(x for x in map_rows(T,[{'label':'test','rows':ms}])if x['queue_id']==q)
class NegativeMappings(unittest.TestCase):
 def test_duplicate_source_id_ambiguous(self):
  t=next(t for t in T if t['source_index']is not None);a=mesh('a','x',['source'],t['source_index']);b={**a,'id':'b'};self.assertEqual(out(t['queue_id'],[a,b])['current_observation'],'AMBIGUOUS_MULTIPLE_RUNTIME_OBJECTS')
 def test_wrong_family_no_join(self):
  t=next(t for t in T if t['family']=='face');self.assertEqual(out(t['queue_id'],[mesh('a',t['historical_name'],['exterior'])])['current_observation'],'NOT_JOINED_IN_CAPTURED_STATES')
 def test_unknown_source_not_name_alias(self):
  t=next(t for t in T if t['source_index']is not None);self.assertEqual(out(t['queue_id'],[mesh('a',t['historical_name'],['source'],99999)])['current_observation'],'NOT_JOINED_IN_CAPTURED_STATES')
 def test_repeat_runtime_identity_not_duplicate(self):
  t=next(t for t in T if t['source_index']is not None);a=mesh('a','x',['source'],t['source_index']);r=map_rows(T,[{'label':'one','rows':[a]},{'label':'two','rows':[a]}]);v=next(x for x in r if x['queue_id']==t['queue_id']);self.assertEqual(len(v['runtime_candidates']),1);self.assertEqual(len(v['runtime_candidates'][0]['states']),2);self.assertFalse(v['finalized'])
 def test_optimization_never_forced(self):
  for q in ['q421-g407','q421-g408','q421-g419','q421-g420','q421-g421']:
   t=next(t for t in T if t['queue_id']==q);self.assertEqual(out(q,[mesh('a',t['historical_name'],[])])['current_observation'],'UNRESOLVED_OPTIMIZATION_REPRESENTATION')
if __name__=='__main__':unittest.main()
