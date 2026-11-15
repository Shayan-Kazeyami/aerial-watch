import ast,math
from pathlib import Path
from PIL import Image
src=Path(__file__).with_name('driver.py').read_text();m=ast.parse(src);f=next(n for n in m.body if isinstance(n,ast.FunctionDef)and n.name=='target_stats');ns={'math':math};exec(compile(ast.Module(body=[f],type_ignores=[]),'driver.target_stats','exec'),ns);stats=ns['target_stats'];roi={'samples':[[x,y]for y in range(20)for x in range(20)]}
a=Image.new('RGBA',(20,20));
for y in range(20):
 for x in range(20):a.putpixel((x,y),(20+x*8,30+x*7,40+x*6,255))
s=stats(a,roi,True);assert s['range90']>100 and s['opaqueFraction']==1
for color in [(80,80,80,255),(0,0,0,255),(255,255,255,255),(20,70,180,0)]:
 b=Image.new('RGBA',(20,20),color)
 try:stats(b,roi,True)
 except AssertionError:pass
 else:raise AssertionError(('unacceptable-region-accepted',color))
 assert stats(b,roi,False)['samples']==400
print('PASS extracted actual driver ROI statistics: smooth opaque variation accepted, flat/black/white/transparent required regions rejected. Synthetic arithmetic only, no renderer proof.')
