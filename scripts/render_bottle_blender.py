#!/usr/bin/env python3
"""Render the Sauce squeeze-bottle hero using Blender 4.5+.

Creates a procedural, clearly marked fallback when the user GLB is not available
inside the isolated render worker. The original GLB is never overwritten.
"""
import bpy
import math
import os
import sys
from mathutils import Vector

BASE=os.path.dirname(os.path.abspath(__file__))
OUT=os.environ.get("SAUCE_RENDER_OUT", os.path.join(BASE,"../renders/sauce-bottle.png"))
SAMPLES=int(os.environ.get("SAUCE_SAMPLES","36"))
W=int(os.environ.get("SAUCE_WIDTH","880"))
H=int(os.environ.get("SAUCE_HEIGHT","1100"))

bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
for m in bpy.data.materials: bpy.data.materials.remove(m)

def rgba(h):
    h=h.strip("#")
    v=[int(h[i:i+2],16)/255 for i in (0,2,4)]
    return tuple((x/12.92 if x<.04045 else ((x+.055)/1.055)**2.4) for x in v)+(1.0,)

def material(name, col, rough=.25, coat=0.0, metallic=0):
    m=bpy.data.materials.new(name)
    m.diffuse_color=rgba(col)
    m.use_nodes=True
    p=m.node_tree.nodes.get("Principled BSDF")
    p.inputs["Base Color"].default_value=rgba(col)
    p.inputs["Roughness"].default_value=rough
    p.inputs["Metallic"].default_value=metallic
    p.inputs["Coat Weight"].default_value=coat
    p.inputs["Coat Roughness"].default_value=.13
    return m
red=material("SAUCE — rich red gloss plastic", "#a71109",.21,.55)
deepred=material("SAUCE — dark red seam", "#780c08",.22,.4)
highlight=material("SAUCE — bright red details", "#df2916",.19,.5)
cream=material("SAUCE — warm ivory printed label", "#fff0d6",.49)
paper=material("SAUCE — label thin border", "#a71814",.4)
cap=material("SAUCE — ivory injection mould plastic", "#f5dfbc",.32,.15)
capshadow=material("SAUCE — recessed cap", "#bd9a7c",.46)
ink=material("SAUCE — brand lettering", "#a4140e",.36)
black=material("SAUCE — black tag line", "#31201d",.53)

root=bpy.data.objects.new("Sauce / bottle master pivot",None)
bpy.context.scene.collection.objects.link(root)

def attach(ob, mat):
    if mat: ob.data.materials.append(mat)
    ob.parent=root
    return ob

def bevel_cube(name, loc, dims, radius, mat, seg=8):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    ob=bpy.context.object; ob.name=name
    ob.dimensions=dims
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    mod=ob.modifiers.new("Rounded moulded corners","BEVEL")
    mod.width=radius; mod.segments=seg
    mod.profile=.65
    ob.modifiers.new("Weighted normals","WEIGHTED_NORMAL")
    return attach(ob,mat)

def cylinder(name,loc,r,depth,mat,verts=96,axis=None):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts,radius=r,depth=depth,location=loc)
    ob=bpy.context.object; ob.name=name
    if axis: ob.rotation_euler=axis
    bpy.ops.object.shade_smooth()
    return attach(ob,mat)

# Single continuous rounded-rectangle squeeze shell.
# Each sample is (height from inverted nozzle, x-halfwidth, y-halfdepth, corner power)
profiles=[
 (.78,.29,.29,2.15),(.87,.38,.36,2.3),(1.02,.58,.42,2.7),
 (1.24,.80,.55,3.05),(1.49,.94,.61,3.1),(1.8,1.035,.635,3.2),
 (2.22,1.07,.63,3.25),(2.65,1.015,.60,3.15),(3.04,.89,.57,3.0),
 (3.31,.94,.58,3.0),(3.65,1.035,.63,3.1),(3.92,1.045,.66,3.2),
 (4.11,1.0,.65,3.15),(4.28,.88,.55,3.0),(4.41,.69,.44,2.8),
 (4.46,.60,.39,2.7)]
N=112
verts=[];faces=[]
for z,rx,ry,p in profiles:
    for j in range(N):
        a=2*math.pi*j/N
        co,si=math.cos(a),math.sin(a)
        x=rx * math.copysign(abs(co)**(2.0/p),co)
        y=ry * math.copysign(abs(si)**(2.0/p),si)
        verts.append((x,y,z))
for i in range(len(profiles)-1):
    for j in range(N):
        a=i*N+j;b=i*N+(j+1)%N;c=(i+1)*N+(j+1)%N;d=(i+1)*N+j
        faces.append((a,b,c,d))
verts.append((0,0,profiles[0][0]));verts.append((0,0,profiles[-1][0]))
for j in range(N):
    faces.append((len(verts)-2,j,(j+1)%N))
    faces.append((len(verts)-1,(len(profiles)-1)*N+(j+1)%N,(len(profiles)-1)*N+j))
mesh=bpy.data.meshes.new("contoured squeeze bottle shell");mesh.from_pydata(verts,[],faces);mesh.update()
body=bpy.data.objects.new("Sauce bottle / moulded shell",mesh);bpy.context.collection.objects.link(body);attach(body,red)
for face in mesh.polygons:face.use_smooth=True
bevel=body.modifiers.new("Subtle moulded edge radius","BEVEL");bevel.width=.024;bevel.segments=3
body.modifiers.new("Custom normals","WEIGHTED_NORMAL")

# Bottle top seam, with shallow glossy physical ridge.
bevel_cube("Upper body embossed base seam",(0,0,4.345),(1.43,.91,.15),.1,highlight)
bevel_cube("Lower pinch / mould seam",(0,0,1.04),(1.11,.79,.09),.045,deepred)

# Bottle neck and the nozzle are BELOW the inverted bottle.
cylinder("red lower neck",(0,0,.77),.365,.24,red)
cylinder("cap retaining ring",(0,0,.64),.44,.14,cap)
cylinder("cap lower rim",(0,0,.55),.49,.14,cap,112)
cylinder("cap cream cylindrical wall",(0,0,.42),.45,.31,cap,112)
cylinder("cap bottom rolled ring",(0,0,.244),.466,.065,cap,112)
# Fine injection-mould ribbing on cap (material detail without heavy textures)
for i in range(88):
    a=math.tau*i/88
    xx=.451*math.cos(a);yy=.451*math.sin(a)
    ob=cylinder("Ribbing %02d"%i,(xx,yy,.423),.011,.275,capshadow,8)
    ob.scale.x=.72;ob.scale.y=.72
cylinder("nozzle / neck end",(0,0,.177),.19,.17,cap)
cylinder("outlet dark channel",(0,0,.084),.115,.018,deepred)

# Real open flip-top attached by hinge to back-left of cap.
lid=cylinder("hinged flip-cap open lid",(-.75,-.04,.33),.465,.105,cap,96)
lid.rotation_euler=(math.radians(75),math.radians(5),math.radians(-14))
cylinder("open cap inner plug",(-.753,-.092,.29),.135,.038,capshadow,48,axis=(math.radians(75),0,0))
hinge=cylinder("flip hinge pivot",(-.45,.01,.50),.072,.22,cap,32,axis=(math.radians(90),0,0))

# curved rounded label: conform to front face, not a floating planar sticker
def front_y(x,z):
    # Most of our label sits where the center section is broadest. Use
    # smoothly interpolated profile rather than a flat piece intersecting the shell.
    zs=[p[0] for p in profiles]
    k=next((i for i in range(len(zs)-1) if zs[i]<=z<=zs[i+1]),len(zs)-2)
    z0,rx0,ry0,p0=profiles[k];z1,rx1,ry1,p1=profiles[k+1]
    f=max(0,min(1,(z-z0)/(z1-z0)))
    rx=rx0+(rx1-rx0)*f;ry=ry0+(ry1-ry0)*f
    pp=p0+(p1-p0)*f
    return -ry*max(.003,1-(abs(x)/rx)**pp)**(1/pp)

def round_outline(cx,cz,w,h,r,steps=14):
    pts=[]
    for ox,oz,lo,hi in [
        (cx+w/2-r,cz+h/2-r,0,90),
        (cx-w/2+r,cz+h/2-r,90,180),
        (cx-w/2+r,cz-h/2+r,180,270),
        (cx+w/2-r,cz-h/2+r,270,360)]:
        # corners order: start at top right -> top left -> lower left -> lower right
        for j in range(steps+1):
            a=math.radians(lo+(hi-lo)*j/steps)
            pts.append((ox+r*math.cos(a),oz+r*math.sin(a)))
    return pts

def make_patch(name,w,h,r,z,off,mat,ns=4):
    outline=round_outline(0,z,w,h,r,18)
    M=len(outline);V=[];F=[]
    for k in range(ns):
        t=(k+1)/ns
        for x,zz in outline:
            xx=x*t; zzz=z+(zz-z)*t
            V.append((xx,front_y(xx,zzz)-off,zzz))
    V.append((0,front_y(0,z)-off,z))
    for k in range(ns-1):
        for j in range(M):
            a=k*M+j;b=k*M+(j+1)%M;c=(k+1)*M+(j+1)%M;d=(k+1)*M+j
            F.append((a,b,c,d))
    for j in range(M):
        F.append((len(V)-1,(j+1)%M,j))
    m=bpy.data.meshes.new(name);m.from_pydata(V,[],F);m.update()
    uv_layer=m.uv_layers.new(name="PrintedLabelArtwork")
    for poly in m.polygons:
        for loop_id in poly.loop_indices:
            vi=m.loops[loop_id].vertex_index
            vx,vy,vz=m.vertices[vi].co
            uv_layer.data[loop_id].uv=(.5+vx/w,.5+(vz-z)/h)
    o=bpy.data.objects.new(name,m);bpy.context.collection.objects.link(o);attach(o,mat)
    for f in m.polygons:f.use_smooth=True
    ## Label is a single printed surface; extra thickness causes shadowing artifacts
    return o

## Single printed label only: avoids stacked, coplanar paper and border meshes

printed=material("Sauce label — printed professional artwork","#fff0d8",.5)
tex=printed.node_tree.nodes.new("ShaderNodeTexImage")
tex.image=bpy.data.images.load(os.path.abspath(os.path.join(BASE,"../renders/sauce-label.png")))
tex.interpolation="Linear"
bsdf=printed.node_tree.nodes.get("Principled BSDF")
printed.node_tree.links.new(tex.outputs["Color"],bsdf.inputs["Base Color"])
make_patch("SAUCE label — color-correct artwork",1.74,1.60,.25,2.83,.087,printed)

# brand text surface, deliberately rebuilt to avoid AI-distorted glyphs
serif="/usr/share/fonts/truetype/freefont/FreeSerifBoldItalic.ttf"
sans="/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf"
if not os.path.isfile(sans):sans="/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
font=bpy.data.fonts.load(serif) if os.path.isfile(serif) else None
font2=bpy.data.fonts.load(sans) if os.path.isfile(sans) else None

def text_obj(name, s, x,z, size, material, font_obj=None, stretch=1):
    curve=bpy.data.curves.new(name,"FONT")
    curve.body=s
    curve.size=size
    curve.align_x="CENTER"
    curve.align_y="CENTER"
    curve.extrude=.0008;curve.bevel_depth=.0003;curve.bevel_resolution=1
    if font_obj:curve.font=font_obj
    ob=bpy.data.objects.new(name,curve)
    bpy.context.collection.objects.link(ob)
    ob.location=(x,-.748,z)
    ob.rotation_euler=(math.pi/2,0,0)
    ob.scale.x=stretch
    attach(ob,material)
    return ob

# DISABLED — painted in UV texture: text_obj("Sharp brand logotype", "Sauce",0,3.09,.54,ink,font,1.03)
# DISABLED — painted in UV texture: text_obj("Brand statement line one","TURN RECORDINGS",0,2.66,.126,black,font2,.93)
# DISABLED — painted in UV texture: text_obj("Brand statement line two","INTO DEMOS",0,2.49,.132,black,font2,1)
# DISABLED — painted in UV texture: text_obj("Small signature", "●",0,2.26,.12,ink,font2)
# brand underline surface just below script text
def front_curve(name, points, radius,mat):
    c=bpy.data.curves.new(name,"CURVE");c.dimensions="3D";c.resolution_u=36
    s=c.splines.new("BEZIER");s.bezier_points.add(len(points)-1)
    for k,(x,z) in enumerate(points):
        b=s.bezier_points[k];b.co=(x,-.755,z);b.handle_left_type="AUTO";b.handle_right_type="AUTO"
    c.bevel_depth=radius;c.bevel_resolution=4
    o=bpy.data.objects.new(name,c);bpy.context.collection.objects.link(o);attach(o,mat)
# DISABLED — painted in UV texture: front_curve("Sauce signature swoosh",[(-.48,2.89),(-.05,2.825),(.47,2.895)],.013,ink)

# Assemble heroic orientation: cap down, label readable, diagonal like a product ad.
root.rotation_euler=(math.radians(0),math.radians(-16),math.radians(-4))
root.location=(.12,0,.04)

# Groundless studio rig for clean alpha output
def area(name,loc,power,color,size,target=(0,0,2.5),size_y=None):
    bpy.ops.object.light_add(type="AREA",location=loc)
    l=bpy.context.object;l.name=name
    l.data.energy=power;l.data.color=color
    l.data.shape="RECTANGLE";l.data.size=size;l.data.size_y=size_y or size
    direction=Vector(target)-l.location;l.rotation_euler=direction.to_track_quat("-Z","Y").to_euler()

area("Large warm softbox",(-4.2,-5,7.5),650,(1,.86,.72),5, size_y=7)
area("Tall cool rim softbox",(4,3,5),930,(.92,.95,1),3,size_y=7)
area("Bottom cream bounce",(-2,-4,0),190,(1,.79,.58),3,size_y=4)
area("Shape accent right",(2.5,-3,2.4),190,(1,.94,.9),1.5,size_y=5)

world=bpy.data.worlds.new("Warm photography studio") if not bpy.data.worlds else bpy.data.worlds[0]
bpy.context.scene.world=world
world.use_nodes=True
world.node_tree.nodes.get("Background").inputs["Color"].default_value=(.36,.26,.2,1)
world.node_tree.nodes.get("Background").inputs["Strength"].default_value=.30

bpy.ops.object.camera_add(location=(2.3,-10.8,4.85))
cam=bpy.context.object;cam.name="Hero camera — transparent bottle"
aim=Vector((0,0,2.35))-cam.location
cam.rotation_euler=aim.to_track_quat("-Z","Y").to_euler()
cam.data.type="ORTHO";cam.data.ortho_scale=5.35
bpy.context.scene.camera=cam

scene=bpy.context.scene
scene.render.engine="CYCLES"
scene.cycles.device="CPU"
scene.cycles.samples=SAMPLES
scene.cycles.use_denoising=True
scene.render.resolution_x=W
scene.render.resolution_y=H
scene.render.resolution_percentage=100
scene.render.film_transparent=True
scene.view_settings.view_transform="AgX"
scene.render.image_settings.file_format="PNG"
scene.render.image_settings.color_mode="RGBA"
scene.render.image_settings.color_depth="8"
scene.render.filepath=OUT
os.makedirs(os.path.dirname(OUT),exist_ok=True)
print("RENDER_START",OUT,W,H,SAMPLES,flush=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.splitext(OUT)[0]+".blend")
bpy.ops.render.render(write_still=True)
print("RENDER_COMPLETE",OUT,os.path.getsize(OUT),flush=True)
