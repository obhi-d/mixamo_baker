from pathlib import Path
import re
import logging
import bpy
from bpy_types import Object
from math import pi
from mathutils import Vector, Quaternion

log = logging.getLogger(__name__)
#log.setLevel('DEBUG')
unreal = {
    'Root': 'root',
    'Hips': 'pelvis',
    'Spine': 'spine_01',
    'Spine1': 'spine_02',
    'Spine2': 'spine_03',
    '~Shoulder': 'clavicle_~',
    '~Arm': 'upperarm_~',
    '~ForeArm': 'lowerarm_~',
    '~Hand': 'hand_~',
    'Neck1': 'neck_01',
    'Neck': 'neck_01',
    'Head': 'head',
    '~UpLeg': 'thigh_~',
    '~Leg': 'calf_~',
    '~Foot': 'foot_~',
    '~HandIndex1': 'index_01_~',
    '~HandIndex2': 'index_02_~',
    '~HandIndex3': 'index_03_~',
    '~HandMiddle1': 'middle_01_~',
    '~HandMiddle2': 'middle_02_~',
    '~HandMiddle3': 'middle_03_~',
    '~HandPinky1': 'pinky_01_~',
    '~HandPinky2': 'pinky_02_~',
    '~HandPinky3': 'pinky_03_~',
    '~HandRing1': 'ring_01_~',
    '~HandRing2': 'ring_02_~',
    '~HandRing3': 'ring_03_~',
    '~HandThumb1': 'thumb_01_~',
    '~HandThumb2': 'thumb_02_~',
    '~HandThumb3': 'thumb_03_~',
    '~ToeBase': 'ball_~',
    '~Wrist': 'wrist_~'
}

def remove_namespace(s=''):
    """function for removing all namespaces from strings, objects or even armatrure bones"""

    if type(s) == str:
        i = re.search(r"[:_]", s[::-1])
        if i:
            return s[-(i.start())::]
        else:
            return s

    elif type(s) == Object:
        if s.type == 'ARMATURE':
            for bone in s.data.bones:
                bone.name = remove_namespace(bone.name)
        s.name = remove_namespace(s.name)
        return 1
    return -1

def rename_to_unreal(s):
    """function for renaming the armature bones to a target skeleton"""

    if s.type == 'ARMATURE':
        remove_namespace(s)
        for name, value in unreal.items():
            if '~' in name:
                src = name.replace('~', 'Left')
                dst = value.replace('~', 'l')
                rename_bone(s, [name[1:], name[1:] + '.L', src], dst)
                src = name.replace('~', 'Right')
                dst = value.replace('~', 'r')
                rename_bone(s, [name[1:], name[1:] + '.R', src], dst)
            else:
                rename_bone(s, [name], value)

def rename_to_mixamo(s):
    """function for renaming the armature bones to a target skeleton"""

    if s.type == 'ARMATURE':
        remove_namespace(s)
        for name, value in unreal.items():
            if '~' in value:
                src = value.replace('~', 'l')
                dst = name.replace('~', 'Left')
                rename_bone(s, [src], dst)
                src = value.replace('~', 'r')
                dst = name.replace('~', 'Right')
                rename_bone(s, [src], dst)
            else:
                rename_bone(s, [value], name)

def get_all_quaternion_curves(object):
    """returns all quaternion fcurves of object/bones packed together in a touple per object/bone"""
    fcurves = object.animation_data.action.fcurves
    if fcurves.find('rotation_quaternion'):
        yield (fcurves.find('rotation_quaternion', index=0), fcurves.find('rotation_quaternion', index=1), fcurves.find('rotation_quaternion', index=2), fcurves.find('rotation_quaternion', index=3))
    if object.type == 'ARMATURE':
        for bone in object.pose.bones:
            data_path = 'pose.bones["' + bone.name + '"].rotation_quaternion'
            if fcurves.find(data_path):
                yield (fcurves.find(data_path, index=0), fcurves.find(data_path, index=1),fcurves.find(data_path, index=2),fcurves.find(data_path, index=3))

def quaternion_cleanup(object, prevent_flips=True, prevent_inverts=True):
    """fixes signs in quaternion fcurves swapping from one frame to another"""
    for curves in get_all_quaternion_curves(object):
        start = int(min((curves[i].keyframe_points[0].co.x for i in range(4))))
        end = int(max((curves[i].keyframe_points[-1].co.x for i in range(4))))
        for curve in curves:
            for i in range(start, end):
                curve.keyframe_points.insert(i, curve.evaluate(i)).interpolation = 'LINEAR'
        zipped = list(zip(
            curves[0].keyframe_points,
            curves[1].keyframe_points,
            curves[2].keyframe_points,
            curves[3].keyframe_points))
        for i in range(1, len(zipped)):
            if prevent_flips:
                rot_prev = Quaternion((zipped[i-1][j].co.y for j in range(4)))
                rot_cur = Quaternion((zipped[i][j].co.y for j in range(4)))
                diff = rot_prev.rotation_difference(rot_cur)
                if abs(diff.angle - pi) < 0.5:
                    rot_cur.rotate(Quaternion(diff.axis, pi))
                    for j in range(4):
                        zipped[i][j].co.y = rot_cur[j]
            if prevent_inverts:
                change_amount = 0.0
                for j in range(4):
                    change_amount += abs(zipped[i-1][j].co.y - zipped[i][j].co.y)
                if change_amount > 1.0:
                    for j in range(4):
                        zipped[i][j].co.y *= -1.0

def rename_bone(s, names, dst):
    for name in names:
        bone = s.data.bones.get(name)
        if bone:
            bone.name = dst
    
def bake_hips(src_armature, dst_armature, act_name, hips_to_root, use_x, use_y, use_z, use_rotation, on_ground, framerange):
    
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='DESELECT')
    dst_armature.select_set(True)
    bpy.context.view_layer.objects.active = dst_armature

    hips = None
    for hipname in ('Hips', 'mixamorig:Hips', 'mixamorig_Hips', 'pelvis'):
        hips = src_armature.pose.bones.get(hipname)
        if hips != None:
            break

    if hips == None:
        log.warning('WARNING I have not found any hip bone for %s and the conversion is stopping here',  root.pose.bones)
        raise ValueError("no hips found")

    hiplocation_world = src_armature.matrix_local @ hips.bone.head
    z_offset = hiplocation_world[2]

    if hips_to_root:
        bpy.ops.object.mode_set(mode='OBJECT')
        dst_armature.rotation_mode = 'QUATERNION'

        if use_z:        
            c_rootbaker_copy_z_loc = dst_armature.constraints.new(type='COPY_LOCATION')
            c_rootbaker_copy_z_loc.target = src_armature
            c_rootbaker_copy_z_loc.subtarget = hips.name
            c_rootbaker_copy_z_loc.use_x = False
            c_rootbaker_copy_z_loc.use_y = False
            c_rootbaker_copy_z_loc.use_z = True
            c_rootbaker_copy_z_loc.use_offset = True
            if on_ground:
                dst_armature.location[2] = -z_offset
                c_on_ground = dst_armature.constraints.new(type='LIMIT_LOCATION')
                c_on_ground.name = "On Ground"
                c_on_ground.use_min_z = True

        c_rootbaker_copy_loc = dst_armature.constraints.new(type='COPY_LOCATION')
        c_rootbaker_copy_loc.use_x = use_x
        c_rootbaker_copy_loc.use_y = use_y
        c_rootbaker_copy_loc.use_z = False
        c_rootbaker_copy_loc.target = src_armature
        c_rootbaker_copy_loc.subtarget = hips.name

        c_rootbaker_copy_rot = dst_armature.constraints.new(type='COPY_ROTATION')
        c_rootbaker_copy_rot.target = src_armature
        c_rootbaker_copy_rot.subtarget = hips.name
        c_rootbaker_copy_rot.use_y = False
        c_rootbaker_copy_rot.use_x = False
        c_rootbaker_copy_rot.use_z = use_rotation
               
        bpy.ops.object.select_all(action='DESELECT')
        dst_armature.select_set(True)
        bpy.context.view_layer.objects.active = dst_armature
        bpy.ops.nla.bake(frame_start=framerange[0], frame_end=framerange[1], step=1, only_selected=True, visual_keying=True,
                         clear_constraints=True, clear_parents=False, use_current_action=False, bake_types={'OBJECT'})
                

def bake_bones(src_armature, dst_armature, act_name, hips_to_root, use_x, use_y, use_z, use_rotation, on_ground):

    frame_range = src_armature.animation_data.action.frame_range
    
    bake_hips(src_armature, dst_armature, act_name, hips_to_root, use_x, use_y, use_z, use_rotation, on_ground, frame_range)
    
    bpy.ops.object.mode_set(mode='POSE')
    process_later = []

    for dst in dst_armature.pose.bones:
        src = src_armature.pose.bones.get(dst.name)
        if src:
            dst.bone.select = True
            dst_armature.data.bones.active = dst.bone
            dst.rotation_mode = 'QUATERNION'
            c = dst.constraints.new(type='COPY_LOCATION')
            c.target = src_armature
            c.subtarget = src.name

            c = dst.constraints.new(type='COPY_ROTATION')
            c.target = src_armature
            c.subtarget = src.name

            bpy.ops.nla.bake(frame_start=frame_range[0], frame_end=frame_range[1], step=1, only_selected=True, visual_keying=True,
                        clear_constraints=True, clear_parents=False, use_current_action=True, bake_types={'POSE'})
            
            dst.bone.select = False
        elif dst.bone.use_deform:
            process_later.append(dst)

    for dst in process_later:
        dst.bone.select = True
        dst.rotation_mode = 'QUATERNION'
        dst_armature.data.bones.active = dst.bone
        bpy.ops.nla.bake(frame_start=frame_range[0], frame_end=frame_range[1], step=1, only_selected=True, visual_keying=True,
                     clear_constraints=True, clear_parents=False, use_current_action=True, bake_types={'POSE'})
        dst.bone.select = False


    bpy.ops.object.mode_set(mode='OBJECT')
    dst_armature.select_set(True)
    bpy.context.view_layer.objects.active = dst_armature
    dst_armature.animation_data.action.name = act_name
    
    quaternion_cleanup(dst_armature)

def clear_keyframes(dst_armature):
    
    bpy.ops.object.select_all(action='DESELECT')
    dst_armature.select_set(False)
    bpy.context.view_layer.objects.active = dst_armature
    
    old_type = bpy.context.area.type
        
    bpy.context.area.type = 'DOPESHEET_EDITOR'
    bpy.ops.object.mode_set(mode='POSE')
        
    for fc in dst_armature.animation_data.action.fcurves:
        fc.select = True
        key_count = 0
        for x in fc.keyframe_points:
            x.select_control_point=True
            key_count += 1
        if key_count > 1:
            bpy.ops.action.clean(channels=False)
        for x in fc.keyframe_points:
            x.select_control_point=False
        fc.select = False

    bpy.context.area.type = old_type
    bpy.ops.object.mode_set(mode='OBJECT')
    

def get_dst_armature(templ_path):

    files = []
    with bpy.data.libraries.load(templ_path) as (data_from, data_to):
        for name in data_from.objects:
            files.append({'name': name})

    bpy.ops.wm.append(directory=templ_path+"/Object/", files=files)

    for obj in bpy.data.objects:
        if obj.type == 'ARMATURE':
            return obj

def get_src_armature():

    for obj in bpy.context.selected_objects:
        if obj.type == 'ARMATURE':
            return obj

def process_batch(src_dir, dst_dir, templ_path, hips_to_root, use_x, use_y, use_z, use_rotation, on_ground):

    source_dir = Path(src_dir)

    numfiles = 0
    
    bpy.context.scene.unit_settings.system = 'METRIC'
    bpy.context.scene.unit_settings.scale_length = .01

    for file in source_dir.iterdir():
        if not file.is_file():
            continue
        file_ext = file.suffix
        file_loader = {
            ".fbx": lambda filename: bpy.ops.import_scene.fbx(
                filepath=str(filename), axis_forward='-Z',
                axis_up='Y', directory="",
                filter_glob="*.fbx", ui_tab='MAIN',
                use_manual_orientation=False, 
                global_scale=1.0,
                bake_space_transform=False,
                use_custom_normals=True,
                use_image_search=True,
                use_alpha_decals=False, decal_offset=0.0,
                use_anim=True, anim_offset=1.0,
                use_custom_props=True,
                use_custom_props_enum_as_string=True,
                ignore_leaf_bones=True,
                force_connect_children=False,
                automatic_bone_orientation=False,
                primary_bone_axis='Y',
                secondary_bone_axis='X',
                use_prepost_rot=True),
            ".dae": lambda filename: bpy.ops.wm.collada_import(
                filepath=str(filename), filter_blender=False,
                filter_backup=False, filter_image=False,
                filter_movie=False, filter_python=False,
                filter_font=False, filter_sound=False,
                filter_text=False, filter_btx=False,
                filter_collada=True, filter_alembic=False,
                filter_folder=True, filter_blenlib=False,
                filemode=8, display_type='DEFAULT',
                sort_method='FILE_SORT_ALPHA',
                import_units=False, fix_orientation=True,
                find_chains=True, auto_connect=True,
                min_chain_length=0)
        }
        
        if not file_ext in file_loader:
            continue
        numfiles += 1
        
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.delete(use_global=True)

        # remove all datablocks
        for mesh in bpy.data.meshes:
            bpy.data.meshes.remove(mesh, do_unlink=True)
        for material in bpy.data.materials:
            bpy.data.materials.remove(material, do_unlink=True)
        for action in bpy.data.actions:
            bpy.data.actions.remove(action, do_unlink=True)

        # import Template
        dst_armature = get_dst_armature(templ_path)
        bpy.ops.object.select_all(action='DESELECT')

        # import FBX
        file_loader[file_ext](file)
        src_armature = get_src_armature()

        rename_to_unreal(src_armature)

        act_name = file.stem.replace(' ', '_')

        # Bake
        bake_bones(src_armature, dst_armature, act_name, hips_to_root, use_x, use_y, use_z, use_rotation, on_ground)
        
        bpy.ops.object.select_all(action='SELECT')
        dst_armature.select_set(False)
        bpy.context.view_layer.objects.active = src_armature
        bpy.ops.object.delete(use_global=True)
        
        # remove all datablocks
        for mesh in bpy.data.meshes:
            bpy.data.meshes.remove(mesh, do_unlink=True)
        for material in bpy.data.materials:
            bpy.data.materials.remove(material, do_unlink=True)

        for action in bpy.data.actions:
            if action != dst_armature.animation_data.action:
                print('Deleting Action: ' + action.name)
                bpy.data.actions.remove(action, do_unlink=True)
        for armature in bpy.data.armatures:
            if armature != dst_armature.data:
                bpy.data.armatures.remove(armature, do_unlink=True)
                   
        clear_keyframes(dst_armature)

        # Export
        dst_dir = Path(dst_dir)
        output_file = dst_dir.joinpath(file.stem + ".fbx")
        bpy.ops.export_scene.fbx(filepath=str(output_file),
                                 use_selection=False,
                                 apply_unit_scale=False,
                                 add_leaf_bones=False,
                                 axis_forward='-Z',
                                 axis_up='Y',
                                 mesh_smooth_type='FACE',
                                 use_armature_deform_only=True)

        # Cleanup
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.delete(use_global=False)

        for action in bpy.data.actions:
            bpy.data.actions.remove(action, do_unlink=True)

    return numfiles

