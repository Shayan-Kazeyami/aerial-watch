"""Pure fail-closed diagnostic gate; never launches processes."""
EXPECTED=('ordinary_leader','exited_leader_resistant_descendant')
def accepted(rows):
 if not isinstance(rows,list) or len(rows)!=2:return False
 if any(not isinstance(r,dict) for r in rows):return False
 if sorted(r.get('case','') for r in rows)!=sorted(EXPECTED):return False
 for r in rows:
  c=r.get('cleanup',{})
  if r.get('started') is not True:return False
  if r.get('before',{}).get('state')!='present':return False
  if c.get('status')!='verified' or c.get('group_absent') is not True or c.get('leader_reaped') is not True or c.get('errors')!=[]:return False
  if r.get('after',{}).get('state')!='absent':return False
  if 'exception' in r or 'final_wait_error' in r:return False
  if r.get('final_kill') not in ('sent','absent'):return False
  if type(r.get('final_returncode')) is not int:return False
  if r['case']==EXPECTED[1] and (type(r.get('resistant_child_pid')) is not int or r['resistant_child_pid']<=0):return False
 return True
