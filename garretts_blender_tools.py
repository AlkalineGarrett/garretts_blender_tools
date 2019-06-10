# Garrett's Blender Tools
# Copyright 2019 Garrett Jones

import bpy
from mathutils import Vector

bl_info = {
    "name": "Garrett\'s Blender Tools",
    "description": "Tools for object manipulation and transformation",
    "author": "Garrett Jones",
    "version": (0,1),
    "location": "Object > Garrett\'s Blender Tools",
    "category": "Object",
}

def get_local_center(obj):
    return 0.125 * sum((Vector(b) for b in obj.bound_box), Vector())

def get_world_center(obj):
    return obj.matrix_world * get_local_center(obj)

class RepelObjectsOperator(bpy.types.Operator):
    """[GBP] Repel Objects"""
    bl_idname = "object.gbp_repel_objects_operator"
    bl_label = "[GBP] Repel Objects"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):

        obj1 = context.selected_objects[0]
        center1 = get_world_center(obj1)

        obj2 = context.selected_objects[1]
        center2 = get_world_center(obj2)

        obj1_translate = center1 - center2
        obj2_translate = center2 - center1

        # Gives length of the vector from center of object to corner of bounding box of the object
        trans_dist1 = (get_local_center(obj1) - Vector(obj1.bound_box[0])).length
        trans_dist2 = (get_local_center(obj2) - Vector(obj2.bound_box[0])).length
        # Average distance for the two objects
        trans_dist = (trans_dist1 + trans_dist2) / 2

        obj1_translate = obj1_translate * trans_dist / obj1_translate.length
        obj2_translate = obj2_translate * trans_dist / obj2_translate.length

        obj1.location += obj1_translate
        obj2.location += obj2_translate

        return {'FINISHED'}

class GBPMenu(bpy.types.Menu):
    bl_idname = 'object.gbp_menu'
    bl_label = 'Garrett\'s Blender Tools'

    def draw(self, context):
        layout = self.layout
        layout.operator(RepelObjectsOperator.bl_idname)

def menu_func(self, context):
    self.layout.menu(GBPMenu.bl_idname)

def register():
    bpy.utils.register_class(RepelObjectsOperator)
    bpy.utils.register_class(GBPMenu)
    bpy.types.VIEW3D_MT_object.append(menu_func)

def unregister():
    bpy.utils.unregister_class(RepelObjectsOperator)
    bpy.utils.unregister_class(GBPMenu)
    bpy.types.VIEW3D_MT_object.remove(menu_func)

if __name__ == "__main__":
    register()

