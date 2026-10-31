from pathlib import Path
import math,json,xml.etree.ElementTree as ET,hashlib
ROOT=Path(__file__).resolve().parent
R=15.7
S=[[(-3.8,-15.25),(-1.5,-14),(.05,-11.3),(-.2,-8.8)],[(-.2,-8.8),(-.35,-6),(-3,-4),(-3.6,-1.9)],[(-3.6,-1.9),(-4.2,.3),(-2.5,3.7),(-2.35,7.1)],[(-2.35,7.1),(-2.2,10.2),(-3.7,13),(-5.3,14.35)]]
for i,j in [(0,0),(3,3)]:
 p=S[i][j];S[i][j]=tuple(v*R/math.hypot(*p) for v in p)
def evaluate(u):
 k=min(3,int(u));t=u-k;s=S[k]
 p=tuple((1-t)**3*s[0][j]+3*(1-t)**2*t*s[1][j]+3*(1-t)*t*t*s[2][j]+t**3*s[3][j] for j in (0,1))
 d=tuple(3*(1-t)**2*(s[1][j]-s[0][j])+6*(1-t)*t*(s[2][j]-s[1][j])+3*t*t*(s[3][j]-s[2][j]) for j in (0,1));l=math.hypot(*d)
 return p,(-d[1]/l,d[0]/l)
def offset(u,w):
 p,n=evaluate(u);return tuple(p[j]+w*n[j] for j in (0,1))
def profile(w,ro,r=.2):
 def f(u):return math.hypot(*offset(u,w+r))-(ro-r)
 roots=[]
 for a,b in [(0,1),(3,4)]:
  for _ in range(65):
   m=(a+b)/2
   if f(a)*f(m)<=0:b=m
   else:a=m
  roots.append((a+b)/2)
 ta,tb=roots;ca,cb=[offset(u,w+r) for u in roots]
 arc_a,arc_b=[tuple(v*ro/math.hypot(*c) for v in c) for c in (ca,cb)]
 right_a,right_b=[offset(u,w) for u in roots]
 def arc(c,a,b,r,n):
  aa=math.atan2(a[1]-c[1],a[0]-c[0]);bb=math.atan2(b[1]-c[1],b[0]-c[0]);d=(bb-aa)%(2*math.pi)
  assert d<math.pi if c!=(0,0) else True
  return [(c[0]+r*math.cos(aa+d*i/n),c[1]+r*math.sin(aa+d*i/n)) for i in range(n)]
 pts=arc(ca,arc_a,right_a,r,40)
 # Keep segment breakpoints aligned in both loops.
 for a,b,n in [(ta,.16,24),(.16,1,160),(1,2,160),(2,3,160),(3,3.84,160),(3.84,tb,24)]:
  pts += [offset(a+(b-a)*i/n,w) for i in range(n)]
 pts+=arc(cb,right_b,arc_b,r,40)
 anchor_b=(ro*math.cos(2.0),ro*math.sin(2.0));anchor_a=(ro*math.cos(4.4),ro*math.sin(4.4))
 pts+=arc((0,0),arc_b,anchor_b,ro,24)+arc((0,0),anchor_b,anchor_a,ro,400)+arc((0,0),anchor_a,arc_a,ro,24)
 return pts,{'right_trim_parameters':roots,'top_center':ca,'bottom_center':cb,'join_radius_mm':r,'outer_radius_mm':ro,'right_offset_mm':w}
upper,um=profile(0,15.7);lower,lm=profile(.225,14.9)
def cross(a,b,c):return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
def check(p):
 for i in range(len(p)):
  for j in range(i+2,len(p)):
   if i==0 and j==len(p)-1:continue
   a,b,c,d=p[i],p[(i+1)%len(p)],p[j],p[(j+1)%len(p)]
   assert not(cross(a,b,c)*cross(a,b,d)<-1e-14 and cross(c,d,a)*cross(c,d,b)<-1e-14),(i,j)
check(upper);check(lower)
fmt=lambda p:f'{p[0]:.9f},{p[1]:.9f}'
path=lambda p:'M '+' L '.join(map(fmt,p))+' Z'
svg=ET.parse(ROOT/'Aerial-Left-Crescent-B-Angled-Rim-v3.svg');es={e.get('id'):e for e in svg.getroot().iter() if e.get('id')};old=es['aperture-trim'].get('d');aperture=path(upper)
# Exact retained cubic commands plus tangent circular endpoint fillets; native mesh uses matching samples.
def split(s,t):
 a=[tuple((1-t)*s[i][j]+t*s[i+1][j] for j in (0,1)) for i in range(3)]
 b=[tuple((1-t)*a[i][j]+t*a[i+1][j] for j in (0,1)) for i in range(2)]
 c=tuple((1-t)*b[0][j]+t*b[1][j] for j in (0,1))
 return [s[0],a[0],b[0],c],[c,b[1],a[2],s[3]]
ta,tb=um['right_trim_parameters'];ca,cb=um['top_center'],um['bottom_center']
oa,ob=[tuple(v*15.7/math.hypot(*c) for v in c) for c in (ca,cb)]
segs=[split(S[0],ta)[1],S[1],S[2],split(S[3],tb-3)[0]]
aperture='M '+fmt(oa)+' A .2,.2 0 0 1 '+fmt(evaluate(ta)[0])+' '+' '.join('C '+' '.join(fmt(p) for p in s[1:]) for s in segs)+' A .2,.2 0 0 1 '+fmt(ob)+' A 15.7,15.7 0 0 1 '+fmt(oa)+' Z'
es['dial'].set('d',es['dial'].get('d').replace(old,aperture));es['aperture-trim'].set('d',aperture)
es['angled-outer-wall'].set('d',aperture+' '+path(list(reversed(lower))));es['angled-outer-wall'].set('data-min-width','.225');es['angled-outer-wall'].set('data-uniform-drop','.5');es['angled-outer-wall'].set('data-join-radius','.2');es['angled-outer-wall'].set('data-segments',str(len(upper)))
es['angled-outer-wall'].set('data-thickness','.08');es['angled-outer-wall'].set('data-min-thickness','.08');es['angled-outer-wall'].attrib.pop('data-taper-angle',None);es['aperture-trim'].set('data-radius','.045');es['aperture-trim'].set('stroke-width','.09')
es['angled-wall-inner-edge'].set('points',' '.join(map(fmt,lower)));es['angled-wall-inner-edge'].attrib.pop('data-widths',None)
svg.getroot().set('data-revision','ASYMMETRIC-RIM-04');out=ROOT/'Aerial-Left-Crescent-Asymmetric-Rim-v4.svg';ET.indent(svg);svg.write(out,encoding='utf-8',xml_declaration=True)
layers=[profile(.225*i/32,15.7-.8*i/32)[0] for i in range(33)]
data={'depth_layers':layers,'upper':upper,'lower':lower,'upper_geometry':um,'lower_geometry':lm,'source_cubics_svg_mm':S,'drop_mm':.5,'wall_thickness_mm':.08,'upper_z_mm':3.47,'svg_sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'profile_self_intersections':0}
(ROOT/'rim04-profile.json').write_text(json.dumps(data,indent=2))
bounds=json.loads((ROOT/'svg-lettering-bounds.json').read_text());bounds['__svg_sha256']=data['svg_sha256'];(ROOT/'rim04-lettering-bounds.json').write_text(json.dumps(bounds,indent=2))
print(um,lm)
