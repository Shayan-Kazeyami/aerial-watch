"""Conservative semantic joins; never equates a join with visual completion."""
import json,re,pathlib

def normalize(s):return re.sub(r'[^a-z0-9]+','_',s.lower()).strip('_')
def map_rows(tracker,snapshots):
 observed={}
 for snap in snapshots:
  for mesh in snap['rows']:
   entry=observed.setdefault(mesh['id'],{'mesh':mesh,'states':[]})
   entry['states'].append({'label':snap['label'],'effectively_visible':mesh['effectivelyVisible'],'batch_suppressed_source':mesh['batchSuppressedSource'],'geometry':mesh['geometry']})
 results=[]
 for row in tracker:
  q=row['queue_id'];name=row['historical_name'];members=[];method=None
  if q in ['q421-g419','q421-g420','q421-g421','q421-g407','q421-g408']:
   status='UNRESOLVED_OPTIMIZATION_REPRESENTATION';method='Name/ordinal deliberately not used for historical batch identity'
  else:
   for mid,o in observed.items():
    m=o['mesh'];collections={c['name'] for c in m['collections']}
    if row['source_index'] is not None:
     match='source'in collections and m['userData'].get('sourceIndex')==row['source_index'];why='exact sourceIndex within authoritative source collection'
    elif q=='q421-g317':match='backplate'in collections;why='explicit current backplate factory object reference'
    elif q=='q421-g1':match='floor'in collections;why='explicit current lighting floor object reference'
    else:
     expected='exterior' if row['family']=='assembly' else 'premiumFace' if row['family']=='face' else None
     if row['family'] is None:
      number=int(q.split('-g')[1]);expected='leather' if 411<=number<=418 else 'openPlates' if number in [409,410] else 'premiumFace' if 318<=number<=331 else '__unresolved_generated_owner__'
     match=normalize(m['name'])==normalize(name) and (expected is None or expected in collections)
     why='unique normalized name plus expected collection; semantic observation, not original raw geometry equivalence'
    if match:members.append({'runtime_id':mid,'runtime_name':m['name'],'collections':m['collections'],'states':o['states']});method=why
   status='OBSERVED_UNIQUE_SEMANTIC_OBJECT' if len(members)==1 else 'AMBIGUOUS_MULTIPLE_RUNTIME_OBJECTS' if members else 'NOT_JOINED_IN_CAPTURED_STATES'
  results.append({**row,'current_observation':status,'join_method':method,'runtime_candidates':members,'finalized':False,'adopted':False,'historical_geometry_equivalence_verified':False})
 assert len(results)==421 and len({r['queue_id']for r in results})==421
 return results
if __name__=='__main__':
 root=pathlib.Path(__file__).resolve().parent
 states=json.loads((root/'output/CENSUS.json').read_text());rows=map_rows(json.loads((root/'TRACKER_INPUT.json').read_text()),states)
 (root/'output/TRACKER_RUNTIME_OBSERVATIONS.json').write_text(json.dumps(rows,indent=2))
 from collections import Counter
 (root/'output/MAPPING_SUMMARY.json').write_text(json.dumps({'counts':dict(Counter(r['current_observation']for r in rows)),'finalized':0,'adopted':0,'source_statuses_unchanged':True,'scope':'Current semantic runtime observations only; no new geometry or visual approval'},indent=2))
