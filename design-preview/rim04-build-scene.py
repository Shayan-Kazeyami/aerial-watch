import bpy,bmesh,math,json,hashlib,struct,sys
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'rim-leather-r04.blend'))
def identity(o):
 h=hashlib.sha256()
 for v in o.data.vertices:h.update(struct.pack('<3d',*v.co))
 return [h.hexdigest(),[list(r) for r in o.matrix_world]]
source={o.name:identity(o) for o in bpy.context.scene.objects if o.type=='MESH' and ('sourceIndex' in o or o.get('assemblyId') in ['HOUR','MINUTE','SECONDS'])}
data=json.loads((ROOT/'rim04-profile.json').read_text());upper=data['upper'];lower=data['lower'];count=len(upper)
graphite=bpy.data.objects['SVG unified dial and seconds support'].data.materials[0];gold=bpy.data.objects['SVG broad sloped champagne wall'].data.materials[0]
for name in ['SVG unified dial and seconds support','SVG champagne aperture rim','SVG broad sloped champagne wall','SVG lower champagne rim lip']:bpy.data.objects.remove(bpy.data.objects[name],do_unlink=True)
def own(o,name,mat):
 o.name=name;o.data.materials.append(mat);o['premiumFacePart']=True;o['designRevision']='ASYMMETRIC-RIM-04';return o
def mesh_obj(name,verts,faces,mat):
 me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.update();bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free();o=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(o);return own(o,name,mat)
def prism(name,pts,z,depth):
 xy=[(x,-y) for x,y in pts];n=len(xy);return mesh_obj(name,[(x,y,h) for h in (z-depth/2,z+depth/2) for x,y in xy],[tuple(reversed(range(n))),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)],graphite)
def cylinder(name,r,z,d,xy=(0,0)):
 bpy.ops.mesh.primitive_cylinder_add(vertices=192,radius=r,depth=d,location=(*xy,z));return own(bpy.context.object,name,graphite)
def boolean(a,b,op):
 m=a.modifiers.new(op,'BOOLEAN');m.operation=op;m.solver='EXACT';m.object=b;bpy.context.view_layer.objects.active=a;bpy.ops.object.modifier_apply(modifier=m.name);bpy.data.objects.remove(b,do_unlink=True)
plate=cylinder('SVG unified dial and seconds support',16.4,3.36,.22);boolean(plate,prism('cutter',upper,3.4,5),'DIFFERENCE');boolean(plate,cylinder('bore',1.08,3.4,5),'DIFFERENCE')
# Preserve the original seconds attachment dimensions exactly; separate lane owns refinement.
import xml.etree.ElementTree as ET
svg=ET.parse(ROOT/'Aerial-Left-Crescent-Asymmetric-Rim-v4.svg').getroot()
for e in svg.iter():
 if e.get('data-part')=='support':
  x,y,w,h=[float(e.get(k)) for k in ('x','y','width','height')];boolean(plate,prism('support',[(x,y),(x+w,y),(x+w,y+h),(x,y+h)],float(e.get('data-z')),float(e.get('data-thickness'))),'UNION')
ring=cylinder('ring',4.1,3.50,.14,(-7.998827934265137,-.016291368752717972));boolean(ring,cylinder('ringbore',3.1,3.5,5,(-7.998827934265137,-.016291368752717972)),'DIFFERENCE');boolean(plate,ring,'UNION')
bpy.context.view_layer.objects.active=plate;m=plate.modifiers.new('Machined SVG edges','BEVEL');m.width=.025;m.segments=3;bpy.ops.object.modifier_apply(modifier=m.name)
# Intersect constant-angle left/right surfaces at every depth. Only the 0.20 mm
# corner fillet changes surface direction; no long endpoint correspondence ramp.
layers=data['depth_layers'];nv=len(layers)*count;verts=[]
for back in (False,True):
 for k,pts in enumerate(layers):
  z=3.47-.5*k/(len(layers)-1)-(.08 if back else 0)
  verts.extend((x,-y,z) for x,y in pts)
faces=[]
for back in (0,1):
 for k in range(len(layers)-1):
  for i in range(count):
   a=back*nv+k*count+i;b=back*nv+k*count+(i+1)%count
   faces.append((a,b,b+count,a+count))
for k in (0,len(layers)-1):
 for i in range(count):
  a=k*count+i;b=k*count+(i+1)%count;faces.append((a,b,b+nv,a+nv))
rim=mesh_obj('SVG broad sloped champagne wall',verts,faces,gold);rim['rimRole']='sloped-wall';rim['sourceSvgSha256']=data['svg_sha256']
for p in rim.data.polygons:p.use_smooth=True
rim.data.set_sharp_from_angle(angle=math.radians(35))
# No bevel modifier over the small tangent corner: explicit closed profiles stay manifold.
def curve(name,pts,z,r):
 c=bpy.data.curves.new(name,'CURVE');c.dimensions='3D';c.bevel_depth=r;c.bevel_resolution=3;sp=c.splines.new('POLY');sp.points.add(len(pts)-1)
 for knot,(x,y) in zip(sp.points,pts):knot.co=(x,-y,z,1)
 sp.use_cyclic_u=True;o=bpy.data.objects.new(name,c);bpy.context.collection.objects.link(o);return own(o,name,gold)
curve('SVG champagne aperture rim',upper,3.49,.045);curve('SVG lower champagne rim lip',lower,2.97,.018)
def manifold(o):
 bm=bmesh.new();bm.from_mesh(o.data);nm=sum(not e.is_manifold for e in bm.edges);vol=bm.calc_volume(signed=True);bm.free();return {'nonmanifold_edges':nm,'signed_volume_mm3':vol}
deps=bpy.context.evaluated_depsgraph_get()
def tree(o):
 e=o.evaluated_get(deps);me=e.to_mesh();tr=BVHTree.FromPolygons([o.matrix_world@v.co for v in me.vertices],[tuple(p.vertices) for p in me.polygons],all_triangles=False);e.to_mesh_clear();return tr
rt=tree(rim);hits=[]
for name in source:
 o=bpy.data.objects[name]
 if not o.hide_render:
  overlap=rt.overlap(tree(o))
  if overlap:hits.append({'object':name,'triangle_pairs':len(overlap),'assemblyId':o.get('assemblyId'),'bounds':[[min((o.matrix_world@v.co)[i] for v in o.data.vertices),max((o.matrix_world@v.co)[i] for v in o.data.vertices)] for i in range(3)]})
assert all(identity(bpy.data.objects[n])==h for n,h in source.items())
audit={'source_meshes_unchanged':len(source),'source_identity_unchanged':True,'rim':manifold(rim),'dial':manifold(plate),'visible_source_intersections':hits,'right_wall_width_mm':.225,'left_wall_width_mm':.8,'shared_drop_mm':.5,'join_radius_mm':.2,'right_wall_angle_degrees':math.degrees(math.atan2(.5,.225)),'left_wall_angle_degrees':math.degrees(math.atan2(.5,.8)),'upper_geometry':data['upper_geometry'],'lower_geometry':data['lower_geometry'],'bounds_mm':[[min(v.co[i] for v in rim.data.vertices),max(v.co[i] for v in rim.data.vertices)] for i in range(3)],'limitations':['Static surface-overlap only; no manufacturing certification.','Seconds attachment unchanged; separate design lane.']}
(ROOT/'rim04-geometry-audit.json').write_text(json.dumps(audit,indent=2));print('RIM04_AUDIT',json.dumps(audit),flush=True)
scene=bpy.context.scene;scene.render.resolution_x=1200;scene.render.resolution_y=1200;scene.cycles.samples=48;scene.render.filepath=str(ROOT/'rim04-front.png');bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'rim04-asymmetric.blend'),compress=True)
if '--skip-render' not in sys.argv:bpy.ops.render.render(write_still=True)
