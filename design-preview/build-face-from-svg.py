"""Build a reversible B-SVG-01 candidate directly from the dimensioned SVG.
Source movement objects are retained byte-for-byte in mesh coordinates and transforms.
"""
import bpy,bmesh,math,json,re,hashlib,struct,sys
from pathlib import Path
from mathutils import Vector
import xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parent
svg=ET.parse(ROOT/'Aerial-Left-Crescent-B-dimensioned.svg').getroot(); elements={e.get('id'):e for e in svg.iter() if e.get('id')}
meta=json.loads(svg.find('{http://www.w3.org/2000/svg}metadata').text)
letter_bounds=json.loads((ROOT/'svg-lettering-bounds.json').read_text())
svg_sha=hashlib.sha256((ROOT/'Aerial-Left-Crescent-B-dimensioned.svg').read_bytes()).hexdigest()
assert letter_bounds['__svg_sha256']==svg_sha,'Regenerate lettering bounds for the edited SVG.'
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'fixed-movement-cutaway-r01.blend'));baseline=set(o.name for o in bpy.context.scene.objects)
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'approved-b-face-r02.blend'))
def identity(o):
 h=hashlib.sha256()
 for v in o.data.vertices:h.update(struct.pack('<3d',*v.co))
 return {'vertices':h.hexdigest(),'matrix':[list(r) for r in o.matrix_world]}
source={o.name:identity(o) for o in bpy.context.scene.objects if o.type=='MESH' and ('sourceIndex' in o or o.get('assemblyId') in ['HOUR','MINUTE','SECONDS'])}
for o in list(bpy.context.scene.objects):
 if o.name not in baseline and o.type in {'MESH','CURVE','FONT'}:bpy.data.objects.remove(o,do_unlink=True)
graphite=bpy.data.materials['Graphite dial'];gold=bpy.data.materials['Muted champagne'];steel=bpy.data.materials['Satin steel'];authored=[]
def own(o,name,mat=graphite):
 o.name=name;o.data.materials.clear();o.data.materials.append(mat);o['premiumFacePart']=True;o['designRevision']='B-SVG-01';authored.append(o);return o
def cylinder(name,r,z,depth,xy=(0,0),mat=graphite):
 bpy.ops.mesh.primitive_cylinder_add(vertices=192,radius=r,depth=depth,location=(*xy,z));return own(bpy.context.object,name,mat)
def boolean(base,operand,operation):
 m=base.modifiers.new('SVG '+operation,'BOOLEAN');m.operation=operation;m.solver='EXACT';m.object=operand;bpy.context.view_layer.objects.active=base;bpy.ops.object.modifier_apply(modifier=m.name)
 if operand in authored:authored.remove(operand)
 bpy.data.objects.remove(operand,do_unlink=True)
def prism(name,points,z,depth,mat=graphite):
 # Convert the SVG's downward Y to the source assembly's upward Y.
 xy=[(x,-y) for x,y in points];n=len(xy);verts=[(x,y,h) for h in (z-depth/2,z+depth/2) for x,y in xy]
 faces=[tuple(reversed(range(n))),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
 mesh=bpy.data.meshes.new(name);mesh.from_pydata(verts,[],faces);mesh.update();bm=bmesh.new();bm.from_mesh(mesh);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(mesh);bm.free()
 o=bpy.data.objects.new(name,mesh);bpy.context.collection.objects.link(o);return own(o,name,mat)
def cubic_path(d):
 tokens=re.findall(r'[MCZ]|[-+]?(?:\d*\.\d+|\d+)(?:[eE][-+]?\d+)?',d);i=0;out=[];current=None
 while i<len(tokens):
  command=tokens[i];i+=1
  if command=='M':current=(float(tokens[i]),float(tokens[i+1]));i+=2;out.append(current)
  elif command=='C':
   coords=list(map(float,tokens[i:i+6]));i+=6;a=current;b=coords[:2];c=coords[2:4];e=coords[4:6]
   for k in range(1,81):
    t=k/80;out.append(tuple((1-t)**3*a[j]+3*(1-t)**2*t*b[j]+3*(1-t)*t*t*c[j]+t**3*e[j] for j in (0,1)))
   current=e
  elif command!='Z':raise ValueError('Unsupported SVG path command '+command)
 if math.dist(out[0],out[-1])<1e-6:out.pop()
 return out
aperture=cubic_path(elements['aperture-trim'].get('d'))
def circles(e):
 number=r'([-+]?(?:\d*\.\d+|\d+))'
 found=re.findall(r'M\s*'+number+r','+number+r'\s*A\s*'+number+r','+number,e.get('d'))
 out=[]
 for x,y,rx,ry in found:
  x,y,rx,ry=map(float,(x,y,rx,ry));assert abs(rx-ry)<1e-7;out.append((x-rx,y,rx))
 return out
dial_element=elements['dial'];dial_circles=circles(dial_element);assert len(dial_circles)==2
outer,hole=dial_circles;assert abs(outer[0])+abs(outer[1])+abs(hole[0])+abs(hole[1])<1e-7
plate=cylinder('SVG unified dial and seconds support',outer[2],float(dial_element.get('data-z')),float(dial_element.get('data-thickness')))
boolean(plate,prism('SVG aperture cutter',aperture,3.4,5),'DIFFERENCE')
boolean(plate,cylinder('SVG centre bore',hole[2],3.4,5),'DIFFERENCE')
cx,cy=meta['seconds_pivot_blender_mm']
ring_element=elements['seconds-ring'];ring_circles=circles(ring_element);assert len(ring_circles)==2
for x,y,r in ring_circles:assert abs(x-cx)+abs(y+cy)<1e-6,'SVG ring moved away from source pivot.'
ring=cylinder('SVG seconds ring',ring_circles[0][2],float(ring_element.get('data-z')),float(ring_element.get('data-thickness')),(cx,cy));boolean(ring,cylinder('SVG seconds centre',ring_circles[1][2],3.5,5,(cx,cy)),'DIFFERENCE')
for e in svg.iter():
 if e.get('data-part')=='support':
  x,y,w,h=[float(e.get(k)) for k in ('x','y','width','height')];o=prism(e.get('id'),[(x,y),(x+w,y),(x+w,y+h),(x,y+h)],float(e.get('data-z')),float(e.get('data-thickness')))
  boolean(plate,o,'UNION')
boolean(plate,ring,'UNION')
# Apply an edge chamfer only to the new authored solid.
bpy.context.view_layer.objects.active=plate;m=plate.modifiers.new('Machined SVG edges','BEVEL');m.width=.025;m.segments=3;bpy.ops.object.modifier_apply(modifier=m.name)
for e in svg.iter():
 part=e.get('data-part')
 if part in {'hour-marker','seconds-tick'}:
  pts=[tuple(map(float,p.split(','))) for p in e.get('points').split()];o=prism('SVG '+e.get('id'),pts,float(e.get('data-z')),float(e.get('data-thickness')),gold if e.get('fill')!='#bfc4c8' else steel)
  if part=='hour-marker':m=o.modifiers.new('Baton edge facets','BEVEL');m.width=.035;m.segments=3
 elif part=='ring-edge':
  bpy.ops.mesh.primitive_torus_add(major_radius=float(e.get('r')),minor_radius=float(e.get('data-radius')),major_segments=192,minor_segments=8,location=(float(e.get('cx')),-float(e.get('cy')),float(e.get('data-z'))));own(bpy.context.object,'SVG '+e.get('id'),gold)
 elif part=='lettering':
  c=bpy.data.curves.new(e.get('id'),'FONT');c.body=e.text;c.align_x='CENTER';c.size=float(e.get('font-size'));c.space_character=1.22;c.extrude=.001;c.font=bpy.data.fonts.load('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf')
  o=bpy.data.objects.new('SVG '+e.get('id'),c);bpy.context.collection.objects.link(o);o.location=(float(e.get('x')),-float(e.get('y')),float(e.get('data-z')));own(o,o.name,gold if e.get('id')=='brand' else steel)
  bpy.context.view_layer.update();bounds=letter_bounds[e.get('id')];xs=[v[0] for v in o.bound_box];ys=[v[1] for v in o.bound_box]
  o.scale.x=bounds['width']/(max(xs)-min(xs));o.scale.y=bounds['height']/(max(ys)-min(ys))
  o.location.x=bounds['x']-min(xs)*o.scale.x;o.location.y=-(bounds['y']+bounds['height'])-min(ys)*o.scale.y
curve=bpy.data.curves.new('SVG aperture perimeter','CURVE');curve.dimensions='3D';curve.bevel_depth=float(elements['aperture-trim'].get('data-radius'));curve.bevel_resolution=3;sp=curve.splines.new('POLY');sp.points.add(len(aperture)-1)
for knot,(x,y) in zip(sp.points,aperture):knot.co=(x,-y,3.49,1)
sp.use_cyclic_u=True;o=bpy.data.objects.new('SVG champagne aperture rim',curve);bpy.context.collection.objects.link(o);own(o,o.name,gold)
# Face finish is regularized independently of the image's invented mechanics.
p=graphite.node_tree.nodes.get('Principled BSDF');p.inputs['Metallic'].default_value=.04;p.inputs['Roughness'].default_value=.55
for n in graphite.node_tree.nodes:
 if n.type=='BUMP':n.inputs['Strength'].default_value=.32;n.inputs['Distance'].default_value=.03
bm=bmesh.new();bm.from_mesh(plate.data);nonmanifold=sum(not e.is_manifold for e in bm.edges);unvisited=set(bm.verts);components=0
while unvisited:
 components+=1;stack=[unvisited.pop()]
 while stack:
  v=stack.pop()
  for edge in v.link_edges:
   other=edge.other_vert(v)
   if other in unvisited:unvisited.remove(other);stack.append(other)
bm.free();assert nonmanifold==0,nonmanifold;assert components==1,components
assert all(identity(bpy.data.objects[name])==data for name,data in source.items())
hand_bounds={}
for o in bpy.context.scene.objects:
 if o.type=='MESH' and o.get('assemblyId') in ['HOUR','MINUTE','SECONDS']:
  z=[(o.matrix_world@v.co).z for v in o.data.vertices];hand_bounds[o.get('assemblyId')]={'min_z_mm':min(z),'max_z_mm':max(z)}
assert hand_bounds['SECONDS']['min_z_mm']>3.62
report={'revision':'B-SVG-01','source_svg':'Aerial-Left-Crescent-B-dimensioned.svg','source_svg_sha256':svg_sha,'retained_source_meshes':len(source),'source_vertices_and_transforms_unchanged':True,'unified_dial_connected_components':components,'unified_dial_nonmanifold_edges':nonmanifold,'hand_bounds':hand_bounds,'seconds_tick_max_z_mm':3.62,'static_seconds_vertical_gap_mm':hand_bounds['SECONDS']['min_z_mm']-3.62,'scope':'Connected manifold authored dial/support solid and static hand-height checks. Not full dynamic collision or manufacturing certification.'}
(ROOT/'svg-face-3d-audit.json').write_text(json.dumps(report,indent=2)+'\n')
scene=bpy.context.scene;scene.cycles.samples=96;scene.render.resolution_x=900;scene.render.resolution_y=900;scene.render.resolution_percentage=100;scene.render.filepath=str(ROOT/'svg-face-r01-preview.png')
bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'svg-face-r01.blend'),compress=True)
print('SVG_3D_AUDIT',json.dumps(report),flush=True)
if '--skip-render' not in sys.argv:bpy.ops.render.render(write_still=True)
