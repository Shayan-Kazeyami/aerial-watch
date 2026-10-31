"""Dimensioned face construction. SVG axes are X right / Y down, units mm.
The movement is not traced or modified. Image contours are regularized.
"""
from pathlib import Path
import math,json,xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parent
R=16.4; cx=-7.998827934265137; cy=0.016291368752717972
segments=[((-3.8,-15.25),(-1.5,-14),(.05,-11.3),(-.2,-8.8)),((-.2,-8.8),(-.35,-6),(-3,-4),(-3.6,-1.9)),((-3.6,-1.9),(-4.2,.3),(-2.5,3.7),(-2.35,7.1)),((-2.35,7.1),(-2.2,10.2),(-3.7,13),(-5.3,14.35)),((-5.3,14.35),(-11.2,12.2),(-15.4,6.4),(-15.65,.5)),((-15.65,.5),(-15.7,-6.2),(-11.3,-12.4),(-3.8,-15.25))]
# Keep the inner crescent profile; place its endpoints on the exact outer arc.
arc_radius=15.7
segments=segments[:4]
top=tuple(v*arc_radius/math.hypot(*segments[0][0]) for v in segments[0][0])
bottom=tuple(v*arc_radius/math.hypot(*segments[-1][-1]) for v in segments[-1][-1])
segments[0]=(top,*segments[0][1:]);segments[-1]=(*segments[-1][:-1],bottom)
points=[]
for s in segments:
 for i in range(80):
  t=i/80;points.append(tuple((1-t)**3*s[0][j]+3*(1-t)**2*t*s[1][j]+3*(1-t)*t*t*s[2][j]+t**3*s[3][j] for j in (0,1)))
arc_start=math.atan2(bottom[1],bottom[0]);arc_end=math.atan2(top[1],top[0]);arc_delta=(arc_end-arc_start)%(2*math.pi)
arc_points=[(arc_radius*math.cos(arc_start+arc_delta*i/160),arc_radius*math.sin(arc_start+arc_delta*i/160)) for i in range(160)]
points+=arc_points
assert max(abs(math.hypot(*p)-arc_radius) for p in arc_points)<1e-10
def orient(a,b,c):return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
for i in range(len(points)):
 for j in range(i+2,len(points)):
  if i==0 and j==len(points)-1:continue
  a,b=points[i],points[(i+1)%len(points)];c,d=points[j],points[(j+1)%len(points)]
  assert not (orient(a,b,c)*orient(a,b,d)<0 and orient(c,d,a)*orient(c,d,b)<0),'self-intersection'
minimum_web=R-max(math.hypot(*p) for p in points)
assert minimum_web>.5,minimum_web
fmt=lambda p:f'{p[0]:.8f},{p[1]:.8f}'
aperture='M '+fmt(segments[0][0])+' '+' '.join('C '+' '.join(fmt(p) for p in s[1:]) for s in segments)+f' A {arc_radius},{arc_radius} 0 0 1 '+fmt(top)+' Z'
def circle(x,y,r):return f'M {x+r:.8f},{y:.8f} A {r},{r} 0 1 0 {x-r:.8f},{y:.8f} A {r},{r} 0 1 0 {x+r:.8f},{y:.8f} Z'
ns='http://www.w3.org/2000/svg';ET.register_namespace('',ns)
svg=ET.Element('{'+ns+'}svg',{'width':'34mm','height':'34mm','viewBox':'-17 -17 34 34','version':'1.1','data-units':'mm','data-revision':'B-SVG-03'})
def add(tag,attrs,parent=svg):return ET.SubElement(parent,'{'+ns+'}'+tag,{str(k):str(v) for k,v in attrs.items()})
add('title',{}).text='Aerial Left Crescent B — dimensioned face overlay'
add('desc',{}).text='Style adapted from the approved image. Regularized geometry, original movement pivot retained. No gears are represented. SVG Y is inverted relative to Blender Y. Not a manufacturing certification.'
add('metadata',{}).text=json.dumps({'dial_radius_mm':R,'seconds_pivot_blender_mm':[cx,-cy],'seconds_inner_radius_mm':3.1,'seconds_outer_radius_mm':4.1,'minimum_aperture_outer_web_mm':minimum_web,'outer_cutout_arc_radius_mm':arc_radius,'outer_cutout_arc_center_mm':[0,0],'marker_spacing_degrees':30,'seconds_spacing_degrees':6,'source':'Approved B art direction; fixed OM10 geometry is authoritative.'})
base=add('g',{'id':'dial-and-ring','fill':'#25262a'})
add('path',{'id':'dial','data-part':'dial','data-z':'3.36','data-thickness':'.22','fill-rule':'evenodd','d':circle(0,0,R)+' '+aperture+' '+circle(0,0,1.08)},base)
# Two real connecting tabs reach from the ring into the dial edge; no floating ring.
bridges=[]
for dy in (-2.5,2.5):
 y=cy+dy;xs=[]
 for a,b in zip(points,points[1:]+points[:1]):
  if min(a[1],b[1])<=y<max(a[1],b[1]):xs.append(a[0]+(y-a[1])*(b[0]-a[0])/(b[1]-a[1]))
 assert len(xs)==2
 start=cx+math.sqrt(4.1**2-dy**2)-.22;end=max(xs)+.22
 assert end>start
 bridges.append({'x':start,'y':y-.16,'width':end-start,'height':.32})
 add('rect',{'id':'ring-support-'+str(len(bridges)),'data-part':'support','data-z':'3.42','data-thickness':'.12',**bridges[-1]},base)
add('path',{'id':'seconds-ring','data-part':'seconds-ring','data-z':'3.50','data-thickness':'.14','fill-rule':'evenodd','d':circle(cx,cy,4.1)+' '+circle(cx,cy,3.1)},base)
# A real sloped wall projects as a constant-width annular sector in this SVG.
wall_inner=14.9;inner_top=tuple(v*wall_inner/arc_radius for v in top);inner_bottom=tuple(v*wall_inner/arc_radius for v in bottom)
defs=add('defs',{});gradient=add('radialGradient',{'id':'gold-wall-shade','gradientUnits':'userSpaceOnUse','cx':0,'cy':0,'r':arc_radius},defs)
add('stop',{'offset':'94.9%','stop-color':'#89652f'},gradient);add('stop',{'offset':'100%','stop-color':'#d0b07a'},gradient)
# Continuous closed chamfer: broad outside arc narrows into the inner trim.
taper_angle=math.radians(18);inner_wall=[];widths=[]
area=sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(points,points[1:]+points[:1]));sign=1 if area>0 else -1
for i,p in enumerate(points):
 radius=math.hypot(*p);blend=0
 if abs(radius-arc_radius)<1e-5:
  phase=(math.atan2(p[1],p[0])-arc_start)%(2*math.pi);distance=min(phase,abs(arc_delta-phase));u=min(1,distance/taper_angle);blend=6*u**5-15*u**4+10*u**3
 width=.10+(.8-.10)*blend;widths.append(width)
 prev=points[i-1];nxt=points[(i+1)%len(points)];v1=(p[0]-prev[0],p[1]-prev[1]);v2=(nxt[0]-p[0],nxt[1]-p[1]);l1=math.hypot(*v1);l2=math.hypot(*v2)
 n1=(-sign*v1[1]/l1,sign*v1[0]/l1);n2=(-sign*v2[1]/l2,sign*v2[0]/l2);mid=(n1[0]+n2[0],n1[1]+n2[1]);length=math.hypot(*mid);mid=(mid[0]/length,mid[1]/length);factor=min(5,1/max(.2,mid[0]*n2[0]+mid[1]*n2[1]))
 inner_wall.append((p[0]+mid[0]*width*factor,p[1]+mid[1]*width*factor))
for i in range(len(inner_wall)):
 for j in range(i+2,len(inner_wall)):
  if i==0 and j==len(inner_wall)-1:continue
  a,b=inner_wall[i],inner_wall[(i+1)%len(inner_wall)];c,d=inner_wall[j],inner_wall[(j+1)%len(inner_wall)]
  assert not (orient(a,b,c)*orient(a,b,d)<0 and orient(c,d,a)*orient(c,d,b)<0),'inner wall self-intersection'
wall_path=aperture+' M '+' L '.join(fmt(p) for p in reversed(inner_wall))+' Z'
add('path',{'id':'angled-outer-wall','data-part':'sloped-wall','data-outer-radius':arc_radius,'data-inner-radius':wall_inner,'data-top-z':3.47,'data-bottom-z':2.97,'data-thickness':.12,'data-start-angle':arc_start,'data-sweep-angle':arc_delta,'data-taper-angle':taper_angle,'data-min-width':.10,'data-min-thickness':.025,'data-segments':len(points),'data-closed-band':'true','fill-rule':'evenodd','d':wall_path,'fill':'url(#gold-wall-shade)'})
add('polygon',{'id':'angled-wall-inner-edge','data-part':'wall-bottom-guide','data-widths':' '.join(f'{w:.8f}' for w in widths),'points':' '.join(fmt(p) for p in inner_wall),'fill':'none','stroke':'#b69868','stroke-width':'.04'})
add('path',{'id':'aperture-trim','data-part':'trim','data-z':'3.49','data-radius':'.075','d':aperture,'fill':'none','stroke':'#c7ab7c','stroke-width':'.15','stroke-linejoin':'round'})
for r in (3.1,4.1):add('circle',{'id':'seconds-edge-'+str(r),'data-part':'ring-edge','data-z':'3.56','data-radius':'.035','cx':cx,'cy':cy,'r':r,'fill':'none','stroke':'#c7ab7c','stroke-width':'.07'})
def radial_rect(x,y,r,w,l,a):
 # Tangent width and radial length, oriented exactly around the indicated pivot.
 u=(math.cos(a),math.sin(a));v=(math.sin(a),-math.cos(a));center=(x+r*v[0],y+r*v[1])
 return [(center[0]+s*w/2*u[0]+t*l/2*v[0],center[1]+s*w/2*u[1]+t*l/2*v[1]) for s,t in [(-1,-1),(1,-1),(1,1),(-1,1)]]
for h in range(7):
 p=radial_rect(0,0,14.65,.4,2.2,h*math.pi/6)
 assert max(math.hypot(*v) for v in p)<R
 add('polygon',{'id':f'hour-{h:02}','data-part':'hour-marker','data-z':'3.56','data-thickness':'.12','points':' '.join(fmt(v) for v in p),'fill':'#c7ab7c'})
for i in range(60):
 p=radial_rect(cx,cy,3.62,.06 if i%5==0 else .035,.45 if i%5==0 else .18,i*math.pi/30)
 radii=[math.hypot(x-cx,y-cy) for x,y in p];assert min(radii)>3.1 and max(radii)<4.1
 add('polygon',{'id':f'seconds-tick-{i:02}','data-part':'seconds-tick','data-z':'3.60','data-thickness':'.04','points':' '.join(fmt(v) for v in p),'fill':'#d0b486' if i%5==0 else '#bfc4c8'})
for text,y,size,spacing,color in [('AERIAL',.2,1.2,.32,'#c7ab7c'),('KAZEYAMI STUDIO',1.5,.52,.06,'#aeb4b8')]:
 add('text',{'id':'brand' if text=='AERIAL' else 'studio-name','data-part':'lettering','data-z':'3.49','x':'7','y':y,'font-family':'DejaVu Sans, sans-serif','font-size':size,'letter-spacing':spacing,'text-anchor':'middle','fill':color}).text=text
file=ROOT/'Aerial-Left-Crescent-B-Angled-Rim-v3.svg';ET.indent(svg);ET.ElementTree(svg).write(file,encoding='utf-8',xml_declaration=True)
audit={'revision':'B-SVG-03','units':'mm','aperture_samples':len(points),'aperture_self_intersections':0,'minimum_outer_web_mm':minimum_web,'outer_arc_radius_mm':arc_radius,'outer_arc_center_mm':[0,0],'constant_outer_rim_mm':R-arc_radius,'sloped_wall_radial_width_mm':arc_radius-wall_inner,'sloped_wall_drop_mm':.5,'wall_end_taper_degrees':18,'wall_inner_trim_width_mm':.10,'wall_is_continuous_closed_band':True,'sloped_wall_angle_degrees':math.degrees(math.atan2(.5,arc_radius-wall_inner)),'outer_arc_max_radial_error_mm':max(abs(math.hypot(*p)-arc_radius) for p in arc_points),'dial_radius_mm':R,'small_seconds_pivot_blender_mm':[cx,-cy],'small_seconds_ring_radii_mm':[3.1,4.1],'support_tabs':bridges,'hour_marker_count':7,'hour_spacing_degrees':30,'seconds_tick_count':60,'seconds_spacing_degrees':6,'seconds_tick_top_z_mm':3.62,'source_seconds_hand_min_z_mm':3.9000000953674316,'static_seconds_vertical_gap_mm':.2800000953674316,'limits':['2D construction validated; 3D conversion and full moving-clearance checks pending.','No gears moved or inferred from the image.','Support geometry is connected by design, not structurally certified.']}
(ROOT/'svg03-rim-face-audit.json').write_text(json.dumps(audit,indent=2)+'\n');print(json.dumps(audit,indent=2))
