import unittest,json,pathlib
from map_census import map_rows
class MappingTests(unittest.TestCase):
 def setUp(self):self.rows=json.loads((pathlib.Path(__file__).parent/'TRACKER_INPUT.json').read_text())
 def mesh(self,id,name,collections=None,index=None):return {'id':id,'name':name,'collections':[{'name':c,'index':0}for c in collections or []],'userData':{}if index is None else {'sourceIndex':index},'effectivelyVisible':False,'batchSuppressedSource':False,'geometry':'g'}
 def test_scope_and_holds(self):
  result=map_rows(self.rows,[]);self.assertEqual(len(result),421);self.assertTrue(all(not r['finalized']and not r['adopted']for r in result));self.assertEqual(sum(r['current_observation']=='UNRESOLVED_OPTIMIZATION_REPRESENTATION'for r in result),5)
 def test_ambiguous_name_never_forced(self):
  row=next(r for r in self.rows if r['queue_id']=='q421-g411');m=self.mesh('1',row['historical_name'],['leather']);n={**m,'id':'2'};r=map_rows(self.rows,[{'label':'a','rows':[m,n]}]);r=next(x for x in r if x['queue_id']==row['queue_id']);self.assertEqual(r['current_observation'],'AMBIGUOUS_MULTIPLE_RUNTIME_OBJECTS')
 def test_source_collection_and_hidden_semantics(self):
  row=next(r for r in self.rows if r['source_index']is not None);m=self.mesh('one','arbitrary',['source'],row['source_index']);n=self.mesh('two','arbitrary',['openPlates'],row['source_index']);r=next(x for x in map_rows(self.rows,[{'label':'a','rows':[m,n]}])if x['queue_id']==row['queue_id']);self.assertEqual(len(r['runtime_candidates']),1);self.assertFalse(r['runtime_candidates'][0]['states'][0]['effectively_visible']);self.assertFalse(r['finalized'])
if __name__=='__main__':unittest.main()
