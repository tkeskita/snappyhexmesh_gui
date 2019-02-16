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
#    "wiki_url": "https://localhost/",
#    "tracker_url": "https://localhost/",
    "support": 'COMMUNITY',
    "category": "Object",
    }

if "bpy" in locals():
    import importlib
    importlib.reload(op_export)
else:
    import bpy
    from . import (
        op_export,
        )
    
import os.path
    
class SnappyHexMeshGUI_Settings(bpy.types.PropertyGroup):
    template_path: bpy.props.StringProperty(
        name="Template Path",
        description="Path to SnappyHexMeshDict Template",
        default=os.path.dirname(__file__) + "/snappyHexMeshDictTemplate",
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

    
class SnappyHexMeshGUI_ToolBar:
    bl_label = "SnappyHexMeshGUI"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "SnappyHexMesh GUI"

    
class VIEW3D_PT_SnappyHexMeshGUI_Edit(bpy.types.Panel, SnappyHexMeshGUI_ToolBar):
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
        col.label(text="in edit mode")

    
class VIEW3D_PT_SnappyHexMeshGUI_Object(bpy.types.Panel, SnappyHexMeshGUI_ToolBar):
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
        rowsub.label(text="SnappyHexMeshDict Template:")
        rowsub.prop(gui, "do_snapping", text="", icon='OBJECT_DATA')
        rowsub.prop(gui, "do_add_layers", text="", icon='OBJECT_DATA')
        rowsub = col.row()
        rowsub.prop(gui, "template_path", text="")

        rowsub = col.row()
        rowsub.label(text="Export Path:")
        rowsub = col.row()
        rowsub.prop(gui, "export_path", text="")

        row = layout.row()
        row.operator("object.snappyhexmeshgui_export", text="Export")

        
# Registration

classes = (
    VIEW3D_PT_SnappyHexMeshGUI_Object,
    VIEW3D_PT_SnappyHexMeshGUI_Edit,
    op_export.OBJECT_OT_snappyhexmeshgui_export,
    
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
