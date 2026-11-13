# Sauce Blender production setup — CPU-friendly, repeatable
# Use Blender 4.5 LTS: blender -b -t 2 --python render_sauce.py -- /path/to/source.glb
# When source is unavailable, produces a clearly identified procedural preview.
import bpy, math, os, sys
from mathutils import Vector
from math import sin, cos, pi

SCRIPT_ARGS = sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
SOURCE = SCRIPT_ARGS[0] if SCRIPT_ARGS else ""
OUT = os.environ.get("SAUCE_RENDER_DIR", os.getcwd())
os.makedirs(OUT, exist_ok=True)

bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)

def material(name, color, rough=.26, metallic=0, coat=.5):
    m=bpy.data.materials.new(name)
    m.diffuse_color=(*color,1)
    m.use_nodes=True
    b=m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value=(*color,1)
    b.inputs["Roughness"].default_value=rough
    b.inputs["Metallic"].default_value=metallic
    b.inputs["Coat Weight"].default_value=coat
    b.inputs["Coat Roughness"].default_value=.18
    return m

red=material("Sauce translucent lacquer red",(.44,.008,.009),.19,0,.68)
red_dark=material("Sauce dark tomato red",(.28,.006,.004),.23,0,.5)
cream=material("Sauce warm molded cap",(.87,.77,.61),.32,0,.18)
ivory=material("Sauce printed label stock",(.955,.88,.73),.49,0,.16)
ink=material("Sauce deep crimson label ink",(.38,.012,.009),.37)
gold=material("tiny warm metallic printing",(.61,.33,.18),.31,.3,.3)

assets=[]
source_used=False
if SOURCE and os.path.isfile(SOURCE):
    bpy.ops.import_scene.gltf(filepath=SOURCE)
    source_used=True
    assets=[o for o in bpy.context.scene.objects if o.type=="MESH"]
    for o in assets:
        o.name="Source H2.5 model — "+o.name
        # Remove problematic imported normal map if necessary via controlled inspection.
        for m in o.data.materials:
            if m and m.use_nodes:
                for node in m.node_tree.nodes:
                    if node.type=="BSDF_PRINCIPLED":
                        node.inputs["Roughness"].default_value=.24
                        node.inputs["Metallic"].default_value=0
                        node.inputs["Coat Weight"].default_value=.46
        for p in o.data.polygons:p.use_smooth=True
else:
    # Fallback: design reconstruction based on approved Sauce reference, not the Tripo mesh.
    # The finished render is not represented as a repair of the uploaded model.
    levels=[(0.00,.44,.24),(.08,.58,.29),(.22,.67,.32),(.48,.69,.34),
        (.72,.69,.35),(.92,.65,.34),(1.25,.61,.32),(1.57,.64,.33),
        (1.87,.67,.35),(2.17,.66,.35),(2.42,.60,.33),(2.67,.47,.29),
        (2.83,.36,.26),(2.97,.32,.245),(3.05,.31,.24)]
    # Smooth interpolation with Catmull-Rom across profile keypoints.
    def cat(a,b,c,d,t):
        return .5*((2*b)+(-a+c)*t+(2*a-5*b+4*c-d)*t*t+(-a+3*b-3*c+d)*t*t*t)
    rings=[]
    for j in range(len(levels)-1):
        A=levels[max(0,j-1)];B=levels[j];C=levels[j+1];D=levels[min(len(levels)-1,j+2)]
        for n in range(6):
            f=n/6
            rings.append(tuple(cat(A[k],B[k],C[k],D[k],f) for k in range(3)))
    rings.append(levels[-1])
    sectors=80
    v=[]
    for z,rx,ry in rings:
        for i in range(sectors):
            a=2*pi*i/sectors
            # Rounded rectangular bottle silhouette in plan.
            x=rx*math.copysign(abs(cos(a))**.72,cos(a))
            y=ry*math.copysign(abs(sin(a))**.72,sin(a))
            # Soft shoulder / front panel, avoids hard synthetic shape.
            v.append((x,y,z))
    f=[]
    for k in range(len(rings)-1):
        for i in range(sectors):
            a=k*sectors+i;b=k*sectors+(i+1)%sectors
            f.append((a,b,b+sectors,a+sectors))
    f.append(tuple(reversed(tuple(range(sectors)))))
    f.append(tuple((len(rings)-1)*sectors+i for i in range(sectors)))
    mesh=bpy.data.meshes.new("smooth Sauce bottle mesh")
    mesh.from_pydata(v,[],f)
    mesh.update()
    body=bpy.data.objects.new("Bottle body",mesh)
    bpy.context.collection.objects.link(body)
    body.data.materials.append(red)
    for p in mesh.polygons:p.use_smooth=True
    sub=body.modifiers.new("Photo-quality bottle smooth","SUBSURF")
    sub.levels=2
    sub.render_levels=1
    assets.append(body)

    def rounded_box(name,loc,scale,mat,bevel=.055):
        bpy.ops.mesh.primitive_cube_add(size=1,location=loc)
        o=bpy.context.object;o.name=name
        o.dimensions=scale
        bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
        b=o.modifiers.new("Molded radius","BEVEL");b.width=bevel;b.segments=7
        o.modifiers.new("Smooth normals","WEIGHTED_NORMAL")
        o.data.materials.append(mat)
        assets.append(o)
        return o

    # Front label artwork as a separate physically detachable geometry.
    rounded_box("Cream label card",(0,-.342,1.59),(1.15,.025,1.25),ivory,.14)
    # Inner printing border following label edges.
    def border_curve(name,coords,mat,rad=.007):
        cu=bpy.data.curves.new(name,"CURVE");cu.dimensions="3D";cu.resolution_u=24
        poly=cu.splines.new("POLY");poly.points.add(len(coords)-1)
        for point,xyz in zip(poly.points,coords):point.co=(*xyz,1)
        poly.use_cyclic_u=True;cu.bevel_depth=rad;cu.resolution_u=20;cu.bevel_resolution=3
        o=bpy.data.objects.new(name,cu);bpy.context.collection.objects.link(o)
        o.data.materials.append(mat);assets.append(o);return o
    def rounded_rect_points(w,h,r,zcenter,ym=-.364):
        pts=[]
        for cx,cz,theta in [(w/2-r,h/2-r,0),(-w/2+r,h/2-r,90),(-w/2+r,-h/2+r,180),(w/2-r,-h/2+r,270)]:
            for i in range(13):
                a=math.radians(theta+i*90/12)
                pts.append((cx+r*cos(a),ym,zcenter+cz+r*sin(a)))
        return pts
    border_curve("Label printed pinstripe",rounded_rect_points(1.07,1.16,.115,1.59),ink,.0047)

    def font_object(name,body,loc,sz,mat,align="CENTER"):
        cu=bpy.data.curves.new(name,"FONT");cu.body=body;cu.align_x=align;cu.align_y="CENTER";cu.size=sz
        for path in [
            "/home/user/sauce-vids/.local-fonts/Lobster-Regular.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSerif-BoldItalic.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSerif-BoldItalic.ttf",
            "/usr/share/fonts/truetype/liberation2/LiberationSerif-BoldItalic.ttf"]:
            if os.path.isfile(path):
                try:cu.font=bpy.data.fonts.load(path);break
                except:pass
        cu.extrude=.0003;cu.bevel_depth=.0002
        ob=bpy.data.objects.new(name,cu);bpy.context.collection.objects.link(ob)
        ob.location=loc;ob.rotation_euler[0]=pi/2
        ob.data.materials.append(mat)
        assets.append(ob);return ob
    font_object("Sauce exact typographic label","Sauce",(0,-.378,1.79),.32,ink)
    font_object("Sauce supporting tag","TURN RECORDINGS",(0,-.378,1.38),.10,ink)
    font_object("Sauce tag continuation","INTO DEMOS",(0,-.378,1.24),.11,ink)

    def cylinder(name,loc,radius,depth,mat,verts=96):
        bpy.ops.mesh.primitive_cylinder_add(vertices=verts,radius=radius,depth=depth,location=loc)
        o=bpy.context.object;o.name=name
        o.data.materials.append(mat)
        b=o.modifiers.new("Beveled injection molded edges","BEVEL");b.width=min(.05,depth*.28);b.segments=5
        o.modifiers.new("Clean normals","WEIGHTED_NORMAL")
        for p in o.data.polygons:p.use_smooth=True
        assets.append(o)
        return o
    cylinder("Neck collar",(0,0,3.02),.33,.15,red_dark)
    cylinder("Ivory flip cap",(0,0,3.20),.37,.35,cream)
    cylinder("Cap upper ridge",(0,0,3.392),.376,.055,cream)
    cylinder("Pour spout",(0,0,3.455),.10,.13,cream)
    cylinder("Red nozzle opening",(0,0,3.533),.050,.01,red_dark)
    # Separate flipped-open cap lid — prototype physical articulation.
    lid=rounded_box("Open flip lid",(0,.40,3.38),(.52,.42,.065),cream,.045)
    lid.rotation_euler[0]=-math.radians(48)
    cylinder("Flip hinge pin",(0,.34,3.40),.075,.11,cream,48)

    # Molded seams along both side panels.
    for x in [-.65,.65]:
        cu=bpy.data.curves.new("bottle side seam","CURVE");cu.dimensions="3D"
        sp=cu.splines.new("POLY");sp.points.add(35)
        for i,p in enumerate(sp.points):
            z=.18+2.58*i/35
            rx=.66-(max(0,z-2.3)*.28)
            p.co=(x*(rx/.66),-.03,z,1)
        cu.bevel_depth=.008;cu.bevel_resolution=2
        o=bpy.data.objects.new("Mold parting line",cu);bpy.context.collection.objects.link(o)
        o.data.materials.append(red_dark);assets.append(o)

    # Tiny printed tomato icon.
    bpy.ops.mesh.primitive_uv_sphere_add(segments=20,ring_count=12,radius=.045,location=(0,-.382,1.08))
    tomato=bpy.context.object;tomato.scale=(1,.2,.85);tomato.data.materials.append(red_dark);assets.append(tomato)

# Organize all parts under one animated pivot, for pose variation.
pivot=bpy.data.objects.new("Sauce hero transform",None)
bpy.context.collection.objects.link(pivot)
for o in assets:
    if o.parent is None:
        o.parent=pivot
pivot.location=(0,0,0)
if source_used:
    corners=[o.matrix_world @ Vector(c) for o in assets for c in o.bound_box]
    low=min(p.z for p in corners)
    high=max(p.z for p in corners)
    scale=3.1/max(high-low,1e-6)
    pivot.scale=(scale,scale,scale)
    pivot.location.z=-low*scale

# Camera and commercial softbox lighting.
world=bpy.context.scene.world
world.use_nodes=True
world.node_tree.nodes.get("Background").inputs["Color"].default_value=(.35,.31,.28,1)
world.node_tree.nodes.get("Background").inputs["Strength"].default_value=.42

def light(name,loc,power,size,color,shape="DISK"):
    bpy.ops.object.light_add(type="AREA",location=loc)
    o=bpy.context.object;o.name=name
    o.data.energy=power;o.data.shape=shape;o.data.size=size;o.data.color=color
    look=Vector((0,0,1.7))-o.location
    o.rotation_euler=look.to_track_quat("-Z","Y").to_euler()

light("Main key — large warm softbox",(1.2,-4.5,5.2),560,4.3,(1.0,.87,.79))
light("Soft warm front reflection",(-3.5,-1.5,2.8),360,2.4,(1.0,.87,.79))
light("Edge gloss rim",(1.4,2.6,4.8),670,2.3,(1,.84,.79))
light("Bottle base lift",(-2,2.5,.65),240,2.0,(.94,.72,.65))
bpy.ops.object.camera_add(location=(4,-9,3.85))
camera=bpy.context.object
camera.name="Sauce editorial camera"
direction=Vector((0,0,1.7))-camera.location
camera.rotation_euler=direction.to_track_quat("-Z","Y").to_euler()
camera.data.type="ORTHO"
camera.data.ortho_scale=4.2
bpy.context.scene.camera=camera

scene=bpy.context.scene
scene.render.engine="CYCLES"
scene.render.threads_mode="FIXED"
scene.render.threads=1
scene.cycles.device="CPU"
scene.cycles.samples=12
scene.cycles.use_denoising=False
scene.render.resolution_x=560
scene.render.resolution_y=740
scene.render.resolution_percentage=100
scene.render.film_transparent=True
scene.render.image_settings.color_mode="RGBA"
scene.render.image_settings.file_format="PNG"
scene.view_settings.view_transform="AgX"
scene.view_settings.look="AgX - Medium High Contrast"
scene.render.filepath=os.path.join(OUT,"sauce_bottle_studio.png")
bpy.ops.render.render(write_still=True)
print("RENDERED",scene.render.filepath,"from original GLB" if source_used else "PROCEDURAL PROXY")

# The approved hero uses a bottle tilted with its cap towards the lower-left.
pivot.rotation_euler=(math.radians(-8),math.radians(-149),math.radians(4))
# Rotate around optical center, rather than top/bottom, so it stays in frame.
pivot.location=(.4,.1,3.0)
camera.location=(4,-9,5.2)
direction=Vector((.0,0,1.55))-camera.location
camera.rotation_euler=direction.to_track_quat("-Z","Y").to_euler()
camera.data.ortho_scale=4.4
scene.render.filepath=os.path.join(OUT,"sauce_bottle_hero.png")
bpy.ops.render.render(write_still=True)
print("RENDERED",scene.render.filepath)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,"sauce_bottle_editable.blend"))
print("SOURCE_USED",source_used)
