"""Blender Cycles reference material study. Run inside Blender with -- arguments."""
import bpy
import math
import sys
from pathlib import Path

def make_mesh(name, verts, faces):
    mesh=bpy.data.meshes.new(name)
    mesh.from_pydata(verts,[],faces);mesh.update()
    obj=bpy.data.objects.new(name,mesh);bpy.context.collection.objects.link(obj)
    return obj

def rounded_loop(w,h,r,z,n=24):
    pts=[]
    for cx,cy,start in [(w-r,h-r,0),(-w+r,h-r,90),(-w+r,-h+r,180),(w-r,-h+r,270)]:
        for i in range(n):
            a=math.radians(start+90*i/(n-1))
            pts.append((cx+r*math.cos(a),cy+r*math.sin(a),z))
    return pts

def cover(w,h):
    # Closed optical solid: front plateau, continuously rolled shoulder, back.
    rings=[]
    for inset,z in [(0,-.055),(0,-.015),(.004,.012),(.014,.035),(.035,.059),
                    (.062,.079),(.096,.092),(.145,.098),(.26,.102),(.43,.104)]:
        rings.append(rounded_loop(w-inset,h-inset,max(.025,.135-inset*.55),z))
    n=len(rings[0]);verts=[p for ring in rings for p in ring];faces=[]
    faces.append(tuple(reversed(range(n))))
    for k in range(len(rings)-1):
        for j in range(n):faces.append((k*n+j,k*n+(j+1)%n,(k+1)*n+(j+1)%n,(k+1)*n+j))
    faces.append(tuple(range((len(rings)-1)*n,len(rings)*n)))
    obj=make_mesh('Continuous optical cover',verts,faces)
    for p in obj.data.polygons:p.use_smooth=len(p.vertices)==4
    mat=bpy.data.materials.new('Optical dielectric');mat.use_nodes=True
    nd=mat.node_tree.nodes;nd.clear();glass=nd.new('ShaderNodeBsdfGlass')
    glass.inputs['Color'].default_value=(1,1,1,1)
    glass.inputs['Roughness'].default_value=.018;glass.inputs['IOR'].default_value=1.46
    out=nd.new('ShaderNodeOutputMaterial');mat.node_tree.links.new(glass.outputs[0],out.inputs[0])
    obj.data.materials.append(mat)
    # The rear interface has an idealized anti-reflection coating: it
    # transmits/refracts but omits the second specular reflection. This
    # prevents double-imaged softboxes on the readable display.
    rear=bpy.data.materials.new('AR-coated rear dielectric');rear.use_nodes=True
    rn=rear.node_tree.nodes;rn.clear();ref=rn.new('ShaderNodeBsdfRefraction')
    ref.inputs['Color'].default_value=(1,1,1,1);ref.inputs['Roughness'].default_value=.0
    ref.inputs['IOR'].default_value=1.46
    ro=rn.new('ShaderNodeOutputMaterial');rear.node_tree.links.new(ref.outputs[0],ro.inputs[0])
    obj.data.materials.append(rear);obj.data.polygons[0].material_index=1
    return obj

def emission_plane(name,w,h,z,image=None,value=(1,1,1,1)):
    verts=rounded_loop(w,h,.135,z) if name=='Opaque source display' else [(-w,-h,z),(w,-h,z),(w,h,z),(-w,h,z)]
    obj=make_mesh(name,verts,[tuple(range(len(verts)))])
    mat=bpy.data.materials.new(name);mat.use_nodes=True;n=mat.node_tree.nodes;n.clear()
    emit=n.new('ShaderNodeEmission');emit.inputs['Color'].default_value=value
    out=n.new('ShaderNodeOutputMaterial');mat.node_tree.links.new(emit.outputs[0],out.inputs[0])
    if image:
        uv=obj.data.uv_layers.new()
        for i,(x,y,_) in enumerate(verts):uv.data[i].uv=(x/(2*w)+.5,y/(2*h)+.5)
        tex=n.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(image));tex.extension='EXTEND'
        mat.node_tree.links.new(tex.outputs['Color'],emit.inputs['Color'])
    obj.data.materials.append(mat);return obj

def softbox(name,loc,scale,rotation,power):
    bpy.ops.mesh.primitive_plane_add(size=2,location=loc,rotation=rotation)
    obj=bpy.context.object;obj.name=name;obj.scale=(*scale,1)
    mat=bpy.data.materials.new(name);mat.use_nodes=True;n=mat.node_tree.nodes;n.clear()
    e=n.new('ShaderNodeEmission');e.inputs['Color'].default_value=(.94,.97,1,1);e.inputs['Strength'].default_value=power
    o=n.new('ShaderNodeOutputMaterial');mat.node_tree.links.new(e.outputs[0],o.inputs[0]);obj.data.materials.append(mat)
    obj.visible_camera=False;obj.visible_diffuse=False;obj.visible_transmission=False;obj.visible_shadow=False

def main():
    src,sky,out,*rest=sys.argv[sys.argv.index('--')+1:]
    res=int(rest[0]) if rest else 960
    bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
    scene=bpy.context.scene
    scene.render.engine='CYCLES';scene.cycles.samples=64;scene.cycles.use_denoising=False
    scene.cycles.max_bounces=8;scene.cycles.transmission_bounces=6
    scene.render.resolution_x=res;scene.render.resolution_y=round(res*9/16);scene.render.resolution_percentage=100
    scene.render.threads_mode='FIXED';scene.render.threads=6
    scene.view_settings.view_transform='Standard';scene.view_settings.look='None'
    scene.world.use_nodes=True
    scene.world.node_tree.nodes.get("Background").inputs[0].default_value=(.20,.22,.25,1)
    scene.world.node_tree.nodes.get("Background").inputs[1].default_value=.65
    w,h=1.432,.895
    cover(w,h)
    emission_plane('Opaque source display',w,h,-.065,Path(src) if src not in ('black','white') else None, (0,0,0,1) if src=='black' else (1,1,1,1))
    emission_plane('Stationary cobalt environment',16/9,1,-.55,Path(sky) if sky!='black' else None,(0,0,0,1))
    softbox('Upper long softbox',(-.68,.79,2.5),(.64,.060),(0,0,math.radians(-2)),10.)
    softbox('Right strip',(2.0,.15,1.25),(.63,1.06),(0,math.radians(-48),0),14.)
    softbox('Left fill',(-1.95,.10,.9),(.52,1.0),(0,math.radians(48),0),10.)
    bpy.ops.object.camera_add(location=(0,0,6));cam=bpy.context.object;cam.data.type='ORTHO';cam.data.ortho_scale=32/9;scene.camera=cam
    scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_depth='16';scene.render.filepath=out
    bpy.ops.render.render(write_still=True)
if __name__=='__main__':main()
