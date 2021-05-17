import bpy
from bpy.types import Operator, AddonPreferences
from bpy.props import StringProperty, IntProperty, BoolProperty


class MixamoBakerPreferences(AddonPreferences):
    # this must match the add-on name, use '__package__'
    # when defining this in a submodule of a python package.
    bl_idname = __name__

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
        box.row().prop(self, "filepath")
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
    bl_idname = "mixamo_baker.rename_to_mixamo"
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
        mixamo_baker.process_batch(addon_prefs.inpath, addon_prefs.outpath, addon_prefs.sk_path)
        return{ 'FINISHED'}


class MIXAMOBAKER_VIEW_3D_PT_panel(bpy.types.Panel):
    bl_label = "Mixamo Animation Baker"
    bl_idname = "MIXAMOBAKER_VIEW_3D_PT_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Mixamo"
    def draw(self, context):
        layout = self.layout
        preferences = context.preferences
        addon_prefs = preferences.addons[__name__].preferences
        box = layout.box()
        # Options for how to do the conversion
        box.row().prop(addon_prefs.sk_path)
        box.row().prop(addon_prefs.inpath)
        box.row().prop(addon_prefs.outpath)
        box.row().operator("mixamo_baker.bake")

classes = (
    MixamoBakerPreferences,
    OBJECT_OT_RenameToUnreal,
    OBJECT_OT_RenameToMixamo,
    MIXAMOBAKER_VIEW_3D_PT_panel,
)
#register, unregister = bpy.utils.register_classes_factory(classes)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()

        