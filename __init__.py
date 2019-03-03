# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 3
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

# <pep8 compliant>

bl_info = {
    "name": "SnappyHexMesh GUI",
    "author": "Tuomo Keskitalo",
    "blender": (2, 80, 0),
    "location": "3D View > SnappyHexMesh GUI",
    "description": "GUI for OpenFOAM SnappyHexMesh volume mesh generation tool",
    "warning": "Experimental, work in progress",
    "wiki_url": "https://github.com/tkeskita/snappyhexmesh_gui",
    "tracker_url": "https://github.com/tkeskita/snappyhexmesh_gui/issues",
    "support": 'COMMUNITY',
    "category": "Object",
    }

if "bpy" in locals():
    import importlib
    importlib.reload(op_gen)
    importlib.reload(op_export)
    importlib.reload(op_object)
else:
    import bpy
    import os.path
    from sys import float_info
    import math
    from . import (
        op_gen,
        op_export,
        op_object,
        )
    

# Common settings as property group
class SnappyHexMeshGUI_Settings(bpy.types.PropertyGroup):
    snappy_template_path: bpy.props.StringProperty(
        name="Template Path",
        description="Path to SnappyHexMeshDict Template",
        default=os.path.dirname(__file__) + "/skel/snappyHexMeshDictTemplate",
        maxlen=1024,
        subtype="FILE_PATH",
    )
    block_mesh_template_path: bpy.props.StringProperty(
        name="Block Mesh Template Path",
        description="Path to BlockMeshDict Template",
        default=os.path.dirname(__file__) + "/skel/blockMeshDictTemplate",
        maxlen=1024,
        subtype="FILE_PATH",
    )
    export_path: bpy.props.StringProperty(
        name="Export Path",
        description="Path to Export Case Files",
        default="//",
        maxlen=1024,
        subtype="DIR_PATH",
    )
    do_snapping: bpy.props.BoolProperty(
        name="Snapping Phase",
        description="Do Snapping Phase",
        default=True,
    )
    do_add_layers: bpy.props.BoolProperty(
        name="Add Layers Phase",
        description="Do Layer Addition Phase",
        default=False,
    )
    cell_side_length: bpy.props.FloatProperty(
        name="Cell Side Length",
        description="Length of Base Block Mesh Cell Side",
        default=0.1,
        precision=4,
        min=float_info.min, max=float_info.max
    )
    block_mesh_min: bpy.props.FloatVectorProperty(
        name="Block Mesh Minimum Coordinates",
        description="Minimum Coordinates for Block Mesh",
        precision=6,
    )
    block_mesh_max: bpy.props.FloatVectorProperty(
        name="Block Mesh Maximum Coordinates",
        description="Maximum Coordinates for Block Mesh",
        precision=6,
    )
    block_mesh_delta: bpy.props.IntVectorProperty(
        name="Block Mesh Divisions",
        description="Block Mesh Division Counts in X, Y and Z directions",
    )

# Object specific parameters
bpy.types.Object.shmg_include_in_export = bpy.props.BoolProperty(
    name="Include in export",
    description="Include mesh in export (SnappyHexMesh GUI)",
    default=True,
)
bpy.types.Object.shmg_surface_min_level = bpy.props.IntProperty(
    name="Minimum Surface Refinement Level",
    description="Minimum Cell Refinement Level for Surface",
    default=0, min=0, max=10,
)
bpy.types.Object.shmg_surface_max_level = bpy.props.IntProperty(
    name="Maximum Surface Refinement Level",
    description="Maximum Cell Refinement Level for Surface",
    default=0, min=0, max=10,
)
    
class SnappyHexMeshGUI_ToolBar:
    """Base Class for Add-on Tool Bar"""
    bl_label = "SnappyHexMesh GUI"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "SnappyHexMesh GUI"

    
class VIEW3D_PT_SnappyHexMeshGUI_Edit(bpy.types.Panel, SnappyHexMeshGUI_ToolBar):
    """Main Tool Bar in Edit Mode"""
    bl_idname = "VIEW3D_PT_snappyhexmeshgui_edit_mode"
    bl_context = "mesh_edit"
    
    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj and obj.type == 'MESH' and context.mode == 'EDIT_MESH'

    def draw(self, context):
        layout = self.layout
        box = layout.box()
        col = box.column(align=True)
        col.label(text="Not available", icon='ERROR')
        col.label(text="in Edit Mode")

    
class VIEW3D_PT_SnappyHexMeshGUI_Object(bpy.types.Panel, SnappyHexMeshGUI_ToolBar):
    """Main Tool Bar in Object Mode"""
    bl_idname = "VIEW3D_PT_snappyhexmeshgui_object_mode"
    bl_context = "objectmode"
    
    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj and obj.type == 'MESH' and context.mode == 'OBJECT'

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        gui = scene.snappyhexmeshgui

        col = layout.column()
        rowsub = col.row(align=True)
        rowsub.label(text="Options:")
        rowsub.prop(gui, "do_snapping", text="", icon='OBJECT_DATA')
        rowsub.prop(gui, "do_add_layers", text="", icon='OBJECT_DATA')

        rowsub = col.row()
        rowsub.label(text="Export Path:")
        rowsub = col.row()
        rowsub.prop(gui, "export_path", text="")

        rowsub = col.row()
        rowsub.label(text="Cell Length")
        rowsub.prop(gui, "cell_side_length", text="")

        row = layout.row()
        row.operator("object.snappyhexmeshgui_apply_locrotscale", text="Apply LocRotScale for All")
        row = layout.row()
        row.operator("object.snappyhexmeshgui_export", text="Export")


class VIEW3D_PT_SnappyHexMeshGUI_Object_Summary(bpy.types.Panel, SnappyHexMeshGUI_ToolBar):
    """Overall Summary Panel in Object Mode"""
    bl_idname = "VIEW3D_PT_snappyhexmeshgui_object_summary"
    bl_context = "objectmode"
    bl_label = "Export Summary"

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj and obj.type == 'MESH' and context.mode == 'OBJECT'

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        gui = scene.snappyhexmeshgui

        col = layout.column()

        # Global bounding box info
        bb_min, bb_max = op_object.get_global_bbox_coords()
        bb_min_str = "[%7.3f %7.3f %7.3f]" % (bb_min[0], bb_min[1], bb_min[2])
        bb_max_str = "[%7.3f %7.3f %7.3f]" % (bb_max[0], bb_max[1], bb_max[2])
        rowsub = col.row()
        rowsub.label(text="Global Bounds [min] [max]:")
        rowsub = col.row()
        rowsub.label(text=bb_min_str)
        rowsub = col.row()
        rowsub.label(text=bb_max_str)

        # Block mesh cell count
        bm_count = op_object.block_mesh_cell_count(bb_min, bb_max, gui)
        rowsub = col.row(align=True)
        rowsub.label(text="Block Mesh Count: %d" % bm_count)

        # List objects included in export
        rowsub = col.row(align=True)
        rowsub.label(text="Objects included:")
        for obj in bpy.data.objects:
            if obj.type != 'MESH':
                continue
            if not obj.shmg_include_in_export:
                continue
            rowsub = col.row(align=True)
            rowsub.label(text="    %r" % obj.name)

        
class VIEW3D_PT_SnappyHexMeshGUI_Object_Object(bpy.types.Panel, SnappyHexMeshGUI_ToolBar):
    """Object Setting Panel in Object Mode"""
    bl_idname = "VIEW3D_PT_snappyhexmeshgui_object_object"
    bl_context = "objectmode"
    bl_label = "Object Settings"
    
    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj and obj.type == 'MESH' and context.mode == 'OBJECT'

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        gui = scene.snappyhexmeshgui
        obj = context.object

        col = layout.column()
        rowsub = col.row(align=True)
        rowsub.label(text="Object: %r" % obj.name)

        # Bounding box info
        bb_min, bb_max = op_object.get_object_bbox_coords(obj)
        bb_min_str = "[%7.3f %7.3f %7.3f]" % (bb_min[0], bb_min[1], bb_min[2])
        bb_max_str = "[%7.3f %7.3f %7.3f]" % (bb_max[0], bb_max[1], bb_max[2])
        rowsub = col.row()
        rowsub.label(text="Object Bounds [min] [max]:")
        rowsub = col.row()
        rowsub.label(text=bb_min_str)
        rowsub = col.row()
        rowsub.label(text=bb_max_str)

        rowsub = col.row()
        rowsub.prop(obj, "shmg_include_in_export", text="Inlcude in Export")

        rowsub = col.row()
        rowsub.label(text="Surface Refinement Levels:")
        rowsub = col.row()
        rowsub.prop(obj, "shmg_surface_min_level", text="Min")
        rowsub.prop(obj, "shmg_surface_max_level", text="Max")
        
# Registration

classes = (
    VIEW3D_PT_SnappyHexMeshGUI_Object,
    VIEW3D_PT_SnappyHexMeshGUI_Edit,
    VIEW3D_PT_SnappyHexMeshGUI_Object_Object,
    VIEW3D_PT_SnappyHexMeshGUI_Object_Summary,
    op_export.OBJECT_OT_snappyhexmeshgui_export,
    op_export.OBJECT_OT_snappyhexmeshgui_apply_locrotscale,
    
    SnappyHexMeshGUI_Settings,
)
    
def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.snappyhexmeshgui = \
        bpy.props.PointerProperty(type = SnappyHexMeshGUI_Settings)
    
def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

    del bpy.types.Scene.snappyhexmeshgui

if __name__ == "__main__":
    register()
