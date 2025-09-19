
import bpy, bmesh, math
from mathutils import Vector

# --- Parameters ---
w = 1.0      # width
h = 0.6      # height
r = 0.06     # corner radius (iOS-like)
t = 0.01     # thickness
corner_steps = 24

# --- Clean scene (optional) ---
for obj in list(bpy.data.objects):
    obj.select_set(True)
bpy.ops.object.delete(use_global=False, confirm=False)

# --- Create mesh ---
mesh = bpy.data.meshes.new("BlackCardMesh")
obj = bpy.data.objects.new("BlackCard", mesh)
bpy.context.collection.objects.link(obj)
bm = bmesh.new()

def arc(cx, cy, start, end, steps):
    for i in range(steps + 1):
        a = start + (end - start) * (i / steps)
        yield (cx + r * math.cos(a), cy + r * math.sin(a))

ctr_tr = ( w/2 - r,  h/2 - r)
ctr_tl = (-w/2 + r,  h/2 - r)
ctr_bl = (-w/2 + r, -h/2 + r)
ctr_br = ( w/2 - r, -h/2 + r)

outline = []
outline += list(arc(ctr_tr[0], ctr_tr[1], 0.0, math.pi/2, corner_steps))
outline += list(arc(ctr_tl[0], ctr_tl[1], math.pi/2, math.pi, corner_steps))[1:]
outline += list(arc(ctr_bl[0], ctr_bl[1], math.pi, 3*math.pi/2, corner_steps))[1:]
outline += list(arc(ctr_br[0], ctr_br[1], 3*math.pi/2, 2*math.pi, corner_steps))[1:-1]

top_verts = [bm.verts.new((x, y, t/2)) for (x, y) in outline]
bmesh.ops.contextual_create(bm, geom=top_verts)
geom_extrude = bmesh.ops.extrude_face_region(bm, geom=list(bm.faces))["geom"]
for ele in geom_extrude:
    if isinstance(ele, bmesh.types.BMVert):
        ele.co.z -= t

bm.normal_update()
bm.to_mesh(mesh)
bm.free()

# --- Shade smooth ---
bpy.context.view_layer.objects.active = obj
bpy.ops.object.shade_smooth()

# --- Material (robust for Blender 3.x & 4.x) ---
mat = bpy.data.materials.new("BlackMaterial")
mat.use_nodes = True
nt = mat.node_tree

# Find Principled BSDF node
bsdf = nt.nodes.get("Principled BSDF")
if not bsdf:
    for n in nt.nodes:
        if getattr(n, "type", "") == 'BSDF_PRINCIPLED':
            bsdf = n
            break

if bsdf:
    # Base Color -> pure black
    try:
        bsdf.inputs["Base Color"].default_value = (0, 0, 0, 1)
    except KeyError:
        pass

    # Specular input name changed in Blender 4.x ("Specular IOR Level")
    for sock_name in ("Specular", "Specular IOR Level", "Specular IOR"):
        if sock_name in bsdf.inputs.keys():
            try:
                bsdf.inputs[sock_name].default_value = 0.03
            except Exception:
                pass
            break

    # Slightly matte surface
    if "Roughness" in bsdf.inputs.keys():
        bsdf.inputs["Roughness"].default_value = 0.6

obj.data.materials.append(mat)

# --- Simple camera & light ---
cam_data = bpy.data.cameras.new("Camera")
cam_obj = bpy.data.objects.new("Camera", cam_data)
bpy.context.collection.objects.link(cam_obj)
cam_obj.location = (0, -1.6, 0.5)
cam_obj.rotation_euler = (math.radians(70), 0, 0)

light_data = bpy.data.lights.new(name="KeyLight", type='AREA')
light_obj = bpy.data.objects.new(name="KeyLight", object_data=light_data)
bpy.context.collection.objects.link(light_obj)
light_obj.location = (1.2, -0.8, 1.2)
light_data.energy = 500

obj.location = (0, 0, 0)
bpy.context.view_layer.update()

print("✅ Black card created. File > Save As to make a .blend")
