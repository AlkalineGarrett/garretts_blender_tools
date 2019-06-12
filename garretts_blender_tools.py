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

        if len(context.selected_objects) == 0:
            self.report({'ERROR'}, 'No objects selected. Two or more need to be selected to repel.')
            return {'CANCELLED'}

        if len(context.selected_objects) == 1:
            self.report({'ERROR'}, '1 object selected. Two or more need to be selected to repel.')
            return {'CANCELLED'}

        center_sum = Vector([0.0, 0.0, 0.0])
        radius_sum = 0.0
        for obj in context.selected_objects:
            center_sum += get_world_center(obj)
            # Get the length of the vector from center of the object to the
            #   first corner of the bounding box of the object
            # This will be fine for objects close to squares, but less
            #   consistent for elongated objects. It is simple, though.
            radius = (get_local_center(obj) - Vector(obj.bound_box[0])).length
            radius_sum =+ radius
        group_center = center_sum / len(context.selected_objects)
        avg_radius = radius_sum / len(context.selected_objects)

        for obj in context.selected_objects:
            # Get the vector from the group center to this object
            center_to_obj = get_world_center(obj) - group_center
            # Scale the vector
            #   Starting length: distance from group center to this object
            #   Ending length: average radius of the selected objects
            obj_translate = center_to_obj * avg_radius / center_to_obj.length
            obj.location += obj_translate

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

