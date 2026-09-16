# THE WEIGHT OF 276 — data sculpture for web
# 276 rings, one per infant death (KATH MBU verified cohort).
# Ring radius/height pattern encodes age-at-death cohorts (real data):
#   41 within 24h (tightest, lowest), 178 within 1 week total, 96 after 1 week, 2 unrecorded (phantom rings, glass-only)
# Durable source: this script -> weight_of_276.blend -> weight_of_276.glb
import bpy, math, random, os

random.seed(276)
OUT = '/tmp/demo3d/build'
os.makedirs(OUT, exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene

# ---- Palette (editorial ink/paper/brass/teal) ----
def make_mat(name, color, metallic, rough, alpha=1.0, emit=None, emit_strength=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value = (*color, 1)
    bsdf.inputs['Metallic'].default_value = metallic
    bsdf.inputs['Roughness'].default_value = rough
    if alpha < 1.0:
        bsdf.inputs['Alpha'].default_value = alpha
        m.blend_method = 'BLEND'
    if emit is not None:
        bsdf.inputs['Emission Color'].default_value = (*emit, 1)
        bsdf.inputs['Emission Strength'].default_value = emit_strength
    return m

mat_ink    = make_mat('ink',    (0.045, 0.05, 0.058), 0.85, 0.32)
mat_brass  = make_mat('brass',  (0.72, 0.52, 0.22),   1.0,  0.24)
mat_glass  = make_mat('glass',  (0.92, 0.94, 0.95),   0.0,  0.06, alpha=0.28)
mat_teal   = make_mat('teal',   (0.06, 0.42, 0.42),   0.4,  0.3,  emit=(0.06, 0.75, 0.72), emit_strength=2.2)
mat_amber  = make_mat('amber',  (0.55, 0.32, 0.08),   0.7,  0.35, emit=(0.9, 0.55, 0.15), emit_strength=1.6)

# ---- Age cohorts from the verified cohort (274 recorded + 2 unrecorded) ----
# 41 within 24h; 136 more within 1 week (178 total); 96 after 1 week; 2 unrecorded
cohorts = (['24h']*41) + (['week1']*137) + (['later']*96) + (['unknown']*2)
random.shuffle(cohorts)  # position in stack is not the encode; the RING ITSELF encodes

RING_R, RING_TUBE = 1.0, 0.055
GAP = 0.012

def ring(material, z, major_r=RING_R, tube=RING_TUBE, verts=28):
    bpy.ops.mesh.primitive_torus_add(align='WORLD', location=(0, 0, z),
                                     major_radius=major_r, minor_radius=tube,
                                     major_segments=verts, minor_segments=10)
    o = bpy.context.active_object
    o.name = material.name
    o.data.materials.append(material)
    return o

# ---- Build the monolith: 276 rings, z from 0 upward ----
n = len(cohorts)
for i, c in enumerate(cohorts):
    z = i * (RING_TUBE*2 + GAP)
    if c == '24h':      # smallest, heaviest: ink, slightly smaller radius
        ring(mat_ink, z, RING_R*0.82)
    elif c == 'week1':  # brass core of the tower
        ring(mat_brass, z, RING_R*(0.95 + 0.10*math.sin(i*0.35)))
    elif c == 'later':  # ink, full radius
        ring(mat_ink, z, RING_R)
    else:               # 2 unrecorded: phantom glass rings w/ teal glow
        o = ring(mat_glass, z, RING_R*1.05, verts=32)
        glow = ring(mat_teal, z, RING_R*1.05, tube=0.012, verts=32)
        glow.parent = o

total_h = n * (RING_TUBE*2 + GAP)
print('RINGS', len([o for o in bpy.data.objects]), 'HEIGHT', round(total_h, 2))

# ---- Ground: dark reflective slab ----
bpy.ops.mesh.primitive_plane_add(size=60, location=(0, 0, -0.4))
ground = bpy.context.active_object
gm = make_mat('ground', (0.02, 0.022, 0.026), 0.6, 0.42)
ground.data.materials.append(gm)

# ---- Lighting: single dramatic rim + soft fill (studio, museum) ----
bpy.ops.object.light_add(type='AREA', location=(-7, -6, total_h*0.75))
key = bpy.context.active_object
key.data.energy = 4000; key.data.size = 8
key.rotation_euler = (math.radians(55), 0, math.radians(-38))

bpy.ops.object.light_add(type='AREA', location=(8, -3, total_h*0.5))
rim = bpy.context.active_object
rim.data.energy = 2400; rim.data.size = 5
rim.rotation_euler = (math.radians(70), 0, math.radians(150))

bpy.ops.object.light_add(type='AREA', location=(0, 7, total_h*0.35))
fill = bpy.context.active_object
fill.data.energy = 600; fill.data.size = 10
fill.rotation_euler = (math.radians(75), 0, 0)

# ---- World: near-black with haze ----
w = bpy.data.worlds.new('void'); scene.world = w
w.use_nodes = True
bg = w.node_tree.nodes['Background']
bg.inputs['Color'].default_value = (0.012, 0.013, 0.016, 1)
bg.inputs['Strength'].default_value = 0.6

# ---- Cameras: hero 3/4 view + straight-on editorial view ----
bpy.ops.object.camera_add(location=(16, -16, total_h*0.55),
                          rotation=(math.radians(72), 0, math.radians(45)))
cam_hero = bpy.context.active_object; cam_hero.name = 'cam_hero'
cam_hero.data.lens = 32
cam_hero = bpy.context.active_object; cam_hero.name = 'cam_hero'
bpy.ops.object.camera_add(location=(0, -30, total_h*0.5),
                          rotation=(math.radians(90), 0, 0))
cam_front = bpy.context.active_object; cam_front.name = 'cam_front'

# ---- Render helpers ----
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = 1024
scene.render.resolution_y = 1280
scene.eevee.taa_render_samples = 64

def shoot(cam, path):
    scene.camera = cam
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)

shoot(cam_hero, f'{OUT}/hero.png')
shoot(cam_front, f'{OUT}/front.png')

# ---- Export GLB (web) ----
# export web GLB without ground (scene floor handled by CSS/three.js)
ground.hide_render = True
bpy.ops.export_scene.gltf(filepath=f'{OUT}/weight_of_276.glb', export_format='GLB',
    export_draco_mesh_compression_enable=True, export_draco_mesh_compression_level=6,
    use_selection=False)
ground.hide_render = False
bpy.ops.wm.save_as_mainfile(filepath=f'{OUT}/weight_of_276.blend')
print('BUILD_OK')