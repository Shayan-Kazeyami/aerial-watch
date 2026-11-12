from PIL import Image,ImageChops,ImageStat
from pathlib import Path
import json
p=Path('explode-performance/evidence');r=json.loads((p/'report.json').read_text());r['comparison']={}
for state in ['assembled','exploded','partial','reassembled']:
 a=Image.open(p/f'baseline-{state}.png').convert('RGB');b=Image.open(p/f'candidate-{state}.png').convert('RGB');d=ImageChops.difference(a,b);m=sum(ImageStat.Stat(d).mean)/3
 r['comparison'][state]={'meanAbsolutePixelError':m,'pixels':a.width*a.height}
 x=r['modes']['baseline']['states'][state];y=r['modes']['candidate']['states'][state]
 assert x['explosion']==y['explosion'],state
 assert x['quality']==y['quality'] and x['triangles']==y['triangles'],state
 assert m<.1,(state,m)
r['passed']=True;(p/'report.json').write_text(json.dumps(r,indent=2));print(json.dumps(r['comparison'],indent=2))
