# Garrett's Blender Tools
# Copyright 2019 Garrett Jones

import bpy
import bmesh
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


class SplitObjectOperator(bpy.types.Operator):
    """[GBP] Split object"""
    bl_idname = "object.gbp_split_object_operator"
    bl_label = "[GBP] Split Object"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = context.active_object

        if obj.mode != 'EDIT':
            self.report({'ERROR'}, 'Must be in edit mode.')
            return {'CANCELLED'}

        bm = bmesh.from_edit_mesh(obj.data)

        selected_face = None
        for f in bm.faces:
            if f.select:
                if selected_face:
                    self.report({'ERROR'}, 'Only one face can be selected for a splitting plane.')
                    return {'CANCELLED'}
                else:
                    selected_face = f

        if not selected_face:
            self.report({'ERROR'}, 'A face must be selected for a splitting plane.')
            return {'CANCELLED'}

        vtx = selected_face.verts[0]
        normal = selected_face.normal

        plane_co = vtx.co
        plane_no = normal

        geom = bm.verts[:] + bm.edges[:] + bm.faces[:]
        bisection = bmesh.ops.bisect_plane(bm, geom=geom, plane_co=plane_co, plane_no=plane_no)

        cut_edges = [e for e in bisection['geom_cut'] if isinstance(e, bmesh.types.BMEdge)]
        plane_edges = bmesh.ops.split_edges(bm, edges=cut_edges)['edges']

        # out_edges will be two edges that share a common vertex
        # There are three vertexes involved:
        #     1) the last vertex, which is on one end of an edge shared with the “in”
        #            vertex, and which has been visited already
        #     2) the in index, which should be common between the two edges, and is currently
        #            being visited
        #     3) the exit, which has not been visited yet
        # this function will return a tuple with the edge that leads to the exit vertex, and the exit vertex.
        def get_exit(out_edges, last_idx, in_idx):
            for edge in out_edges:
                for vert in edge.verts:
                    if vert.index != last_idx and vert.index != in_idx:
                        return (edge, vert.index)
            print('out_edges: {}, last_idx: {}, in_idx: {}'.format(out_edges, last_idx, in_idx))
            raise ValueError('get_exit: no exit found')

        # For all of the vertices in the edges of plane_edges, create a map from those
        #     vertices to the edges containing them, indexed by the vertex’s index
        vtx_edge_map = {}
        for edge in plane_edges:
            for vtx in edge.verts:
                if vtx.index not in vtx_edge_map:
                    vtx_edge_map[vtx.index] = []
                vtx_edge_map[vtx.index].append(edge)

        # set of which vertex indexes have been processed
        seen_indexes = set()
        loops = []
        for (start_idx, edge_list) in vtx_edge_map.items():
            # For each index we will try to traverse a loop, so many iterations will encounter
            #    indexes that were already processed
            if start_idx in seen_indexes:
                continue
            seen_indexes.add(start_idx)
            out_edges = edge_list
            loop = []
            in_idx = start_idx
            last_idx = None
            while True:
                # if a vertex has 0 or 1 out edges, then it can’t be part of a loop, so stop now
                if len(out_edges) < 2:
                    loop = None
                    break
                # find which edge leads to an index that hasn’t been visited yet
                (out_edge, out_idx) = get_exit(out_edges, last_idx, in_idx)
                seen_indexes.add(out_idx)
                loop.append(out_edge)
                last_idx = in_idx
                in_idx = out_idx
                # The loop is complete!
                if out_idx == start_idx:
                    break
                # This is weird... the loop leads out of the plane. Shouldn’t happen?
                if out_idx not in vtx_edge_map:
                    loop = None
                    break
                out_edges = vtx_edge_map[out_idx]
            if loop:
                loops.append(loop)

        bmesh.ops.edgeloop_fill(bm, edges=loops[0], mat_nr=0, use_smooth=False)
        bmesh.ops.edgeloop_fill(bm, edges=loops[1], mat_nr=0, use_smooth=False)

        bmesh.update_edit_mesh(obj.data)

        bpy.ops.mesh.separate(type='LOOSE')

        # TODO:
        # - delete splitting plane
        # - call 'repel'

        return {'FINISHED'}

class GBPObjectMenu(bpy.types.Menu):
    bl_idname = 'object.gbp_object_menu'
    bl_label = 'Garrett\'s Blender Tools'

    def draw(self, context):
        layout = self.layout
        layout.operator(RepelObjectsOperator.bl_idname)

class GBPMeshMenu(bpy.types.Menu):
    bl_idname = 'object.gbp_mesh_menu'
    bl_label = 'Garrett\'s Blender Tools'

    def draw(self, context):
        layout = self.layout
        layout.operator(SplitObjectOperator.bl_idname)

def object_menu_func(self, context):
    self.layout.menu(GBPObjectMenu.bl_idname)

def mesh_menu_func(self, context):
    self.layout.menu(GBPMeshMenu.bl_idname)

def register():
    bpy.utils.register_class(RepelObjectsOperator)
    bpy.utils.register_class(SplitObjectOperator)
    bpy.utils.register_class(GBPObjectMenu)
    bpy.utils.register_class(GBPMeshMenu)
    bpy.types.VIEW3D_MT_object.append(object_menu_func)
    bpy.types.VIEW3D_MT_edit_mesh.append(mesh_menu_func)

def unregister():
    bpy.utils.unregister_class(RepelObjectsOperator)
    bpy.utils.unregister_class(SplitObjectOperator)
    bpy.utils.unregister_class(GBPObjectMenu)
    bpy.utils.unregister_class(GBPMeshMenu)
    bpy.types.VIEW3D_MT_object.remove(object_menu_func)
    bpy.types.VIEW3D_MT_edit_mesh.remove(mesh_menu_func)

if __name__ == "__main__":
    register()

