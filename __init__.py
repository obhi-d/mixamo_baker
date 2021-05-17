
bl_info = {
    "name": "Mixamo Animation Baker",
    "author": "Abhishek Dey",
    "version": (1, 0, 0),
    "blender": (2, 80, 0),
    "location": "3D View > UI (Right Panel) > Mixamo Animation Tab",
    "description": ("Script to import Mixamo Animations into Armature for UE export"),
    "warning": "",  # used for warning icon and text in addons panel
    "wiki_url": "https://github.com/obhi-d/mixamo_import/wiki",
    "tracker_url": "https://github.com/enziop/mixamo_import/issues" ,
    "category": "Animation"
}

import bpy
from bpy.types import Operator, AddonPreferences
from bpy.props import StringProperty, IntProperty, BoolProperty
from . import mixamo_baker

class MixamoBakerPreferences(bpy.types.AddonPreferences):
    # this must match the add-on name, use '__package__'
    # when defining this in a submodule of a python package.
    bl_idname = __name__

    hips_to_root: bpy.props.BoolProperty(
        name="Bake Hips To Root",
        default=True)
    use_x: bpy.props.BoolProperty(
        name="Use X",
        description="If enabled, Horizontal motion is transfered to RootBone",
        default=True)
    use_y: bpy.props.BoolProperty(
        name="Use Y",
        description="If enabled, Horizontal motion is transfered to RootBone",
        default=True)
    use_z: bpy.props.BoolProperty(
        name="Use Z",
        description="If enabled, vertical motion is transfered to RootBone",
        default=True)
    on_ground: bpy.props.BoolProperty(
        name="On Ground",
        description="If enabled, root bone is on ground and only moves up at jumps",
        default=True)
    use_rotation: bpy.props.BoolProperty(
        name="Transfer Rotation",
        description="Whether to transfer roation to root motion. Should be enabled for curve walking animations. Can be disabled for straight animations with strong hip Motion like Rolling",
        default=True)
    sk_path: StringProperty(
        name="Skeleton Template",
        subtype='FILE_PATH',
    )
    inpath: StringProperty(
        name="Input Dir",
        subtype='DIR_PATH',
    )
    outpath: StringProperty(
        name="Output Dir",
        subtype='DIR_PATH',
    )

    def draw(self, context):
        layout = self.layout
        box = layout.box()
        box.row().prop(self, "sk_path")
        box.row().prop(self, "hips_to_root")
        box.row().prop(self, "inpath")
        box.row().prop(self, "outpath")


class OBJECT_OT_RenameToMixamo(bpy.types.Operator):
    bl_idname = "mixamo_baker.rename_to_mixamo"
    bl_label = "To Mixamo Armature"
    bl_description = "Renames bones to mixamo compatible armature"

    def execute(self, context):
        if bpy.context.object == None:
            self.report({'ERROR_INVALID_INPUT'}, "Error: no object selected.")
            return{ 'CANCELLED'}
        if bpy.context.object.type != 'ARMATURE':
            self.report({'ERROR_INVALID_INPUT'}, "Error: %s is not an Armature." % bpy.context.object.name)
            return{ 'CANCELLED'}
        mixamo_baker.rename_to_mixamo(bpy.context.object)
        return{ 'FINISHED'}


class OBJECT_OT_RenameToUnreal(bpy.types.Operator):
    bl_idname = "mixamo_baker.rename_to_unreal"
    bl_label = "To Unreal Armature"
    bl_description = "Renames bones from mixamo to unreal"

    def execute(self, context):
        if bpy.context.object == None:
            self.report({'ERROR_INVALID_INPUT'}, "Error: no object selected.")
            return{ 'CANCELLED'}
        if bpy.context.object.type != 'ARMATURE':
            self.report({'ERROR_INVALID_INPUT'}, "Error: %s is not an Armature." % bpy.context.object.name)
            return{ 'CANCELLED'}
        mixamo_baker.rename_to_unreal(bpy.context.object)
        return{ 'FINISHED'}

class OBJECT_OT_BatchBake(bpy.types.Operator):
    bl_idname = "mixamo_baker.bake"
    bl_label = "Bake Animations"
    bl_description = "Bake Animation"

    def execute(self, context):
        preferences = context.preferences
        addon_prefs = preferences.addons[__name__].preferences
        numfiles = mixamo_baker.process_batch(addon_prefs.inpath, addon_prefs.outpath, 
                                              addon_prefs.sk_path, addon_prefs.hips_to_root,
                                              addon_prefs.use_x, addon_prefs.use_y, addon_prefs.use_z, 
                                              addon_prefs.use_rotation, addon_prefs.on_ground)
        if numfiles == -1:
            self.report({'ERROR_INVALID_INPUT'}, 'Error: Not all files could be converted, look in console for more information')
            return{ 'CANCELLED'}
        self.report({'INFO'}, "%d files converted" % numfiles)
        return{ 'FINISHED'}


class MIXAMOBAKER_VIEW_3D_PT_panel(bpy.types.Panel):
    bl_label = "Mixamo Animation Baker"
    bl_idname = "MIXAMOBAKER_VIEW_3D_PT_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Mixamo"
    bl_description = "..."

    def draw(self, context):
        layout = self.layout
        preferences = context.preferences
        addon_prefs = preferences.addons[__name__].preferences
        box = layout.box()
        # Options for how to do the conversion
        box.row().prop(addon_prefs, "sk_path")
        box.row().prop(addon_prefs, "hips_to_root")
        box.row().prop(addon_prefs, "inpath")
        box.row().prop(addon_prefs, "outpath")
        box.row().operator("mixamo_baker.rename_to_mixamo")
        box.row().operator("mixamo_baker.rename_to_unreal")

        box = layout.box()
        split = box.split()
        col = split.column(align =True)
        col.prop(addon_prefs, "use_x", toggle =True)
        col.prop(addon_prefs, "use_y", toggle =True)
        col.prop(addon_prefs, "use_z", toggle =True)
        row = box.row()
        col.prop(addon_prefs, "use_rotation", toggle =True)
        row = box.row()
        if addon_prefs.use_z:
            col.prop(addon_prefs, "on_ground", toggle =True)

        box.row().operator("mixamo_baker.bake")

classes = (
    OBJECT_OT_RenameToUnreal,
    OBJECT_OT_RenameToMixamo,
    OBJECT_OT_BatchBake,
    MIXAMOBAKER_VIEW_3D_PT_panel,
)
#register, unregister = bpy.utils.register_classes_factory(classes)

def register():
    bpy.utils.register_class(MixamoBakerPreferences)
    for cls in classes:
        print("Registering: " + cls.bl_idname)
        bpy.utils.register_class(cls)

def unregister():
    for cls in classes:
        print("Unregistering: " + cls.bl_idname)
        bpy.utils.unregister_class(cls)
    bpy.utils.unregister_class(MixamoBakerPreferences)

if __name__ == "__main__":
    register()

        