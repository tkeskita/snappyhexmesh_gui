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

# <pep8-80 compliant>

# ----------------------------------------------------------------------------
# Export functions
from .op_gen import *

# ----------------------------------------------------------------------------


class OBJECT_OT_snappyhexmeshgui_export(bpy.types.Operator):
    """Export (SnappyHexMeshGUI)"""
    bl_idname = "object.snappyhexmeshgui_export"
    bl_label = "SnappyHexMeshGUI Export"

    @classmethod
    def poll(cls, context):
        ob = context.active_object
        return (ob and ob.type == 'MESH' and context.mode == 'OBJECT')

    def execute(self, context):
        l.debug("Starting export")
        template_path = bpy.context.scene.snappyhexmeshgui.template_path
        export_path = bpy.context.scene.snappyhexmeshgui.export_path

        # Get template file
        data = export_initialize(self, template_path, export_path)
        if data is None:
            return{'FINISHED'}
        
        # Carry out replacements to template
        n, data = export_replacements(data)

        # Write result to snappyHexMeshDict
        outfilename = bpy.path.abspath(export_path) \
                      + "/system/snappyHexMeshDict"
        outfile = open(outfilename, 'w')
        outfile.write(''.join(data))
        outfile.close()
        
        self.report({'INFO'}, "Exported %d meshes " % n \
                    + "to: %r" % export_path)
        return {'FINISHED'}

def export_initialize(self, template_path, export_path):
    """Returns content of template dictionary file as text string
    and creates directory structure to export path.
    """

    l.debug("Template path: %r" % template_path)
    if not (os.path.isfile(template_path)):
        self.report({'ERROR'}, "Template not found: %r" % template_path)
        return None
    
    abspath = bpy.path.abspath(export_path)
    l.debug("Export path: %r" % abspath)
    if not abspath:
        self.report({'ERROR'}, "No path set! Please save Blender file to "
                    "a case folder and try again")
        return None

    # Create folder structure if needed
    if not (os.path.isdir(abspath)):
        os.mkdir(abspath)

    for p in ["/constant", "/constant/triSurface", "/system"]:
        if not (os.path.isdir(abspath + p)):
            os.mkdir(abspath + p)
        
    if not (os.path.isdir(abspath + '/system')):
        self.report({'ERROR'}, "Couldn't create folders under %r" % abspath)
        return None
    
    with open(template_path, 'r') as infile:
        data = infile.readlines()
        return data

    
def subst_value(keystr, val, data):
    """Substitute keystr (key word string) with val in 
    snappyHexMesh template data. keystr is the text in
    "//_TEXT_//" clauses in data.
    """

    restr = '//_' + keystr.upper() + '_//'
    newdata = []
    for line in data:
        newdata.append(line.replace(restr, val))
    return newdata


def export_replacements(data):
    """Carry out replacements for key words in template with 
    settings from GUI.
    """
    
    import datetime
    gui = bpy.context.scene.snappyhexmeshgui

    header_text = "// Exported by SnappyHexMesh GUI add-on for Blender v0.1" \
                  + "\n// Source file: " + bpy.context.blend_data.filepath \
                  + "\n// Export date: " + str(datetime.datetime.now())
    data = subst_value("HEADER", header_text, data)
    
    data = subst_value("DO_SNAP", str(gui.do_snapping).lower(), data)
    data = subst_value("DO_ADD_LAYERS", str(gui.do_add_layers).lower(), data)

    n, geo = export_geometries()
    data = subst_value("GEOMETRY", geo, data)
    
    return n, data

def export_geometries():
    """Creates geometry entries for snappyHexMeshDict and
    exports meshes in STL format to case/constant/triSurface folder.
    Returns number of exported meshes and the dictionary text string.
    """

    n = 0 # Number of exported geometries
    # Collect dictionary string to d
    d = "geometry\n{\n"

    # First deselect every object, since STL export is done by selection
    for i in bpy.data.objects:
        i.select_set(False)

    for i in bpy.data.objects:
        if i.type != 'MESH':
            continue

        if i.shmg_include_in_export:
            d += "    %s\n" % i.name \
                 + "    {\n        type triSurfaceMesh;\n" \
                 + "        file \"%s.stl\";\n    }\n" % i.name

            # Export mesh to constant/triSurface/name.stl
            export_path = bpy.context.scene.snappyhexmeshgui.export_path
            abspath = bpy.path.abspath(export_path)
            outpath = abspath + "/constant/triSurface/%s.stl" % i.name
            i.select_set(True)
            bpy.ops.export_mesh.stl(
                filepath=outpath, check_existing=False, \
                axis_forward='Y', axis_up='Z', filter_glob="*.stl", \
                use_selection=True, global_scale=1.0, use_scene_unit=True, \
                ascii=False, use_mesh_modifiers=True)
            i.select_set(False)
            n += 1
    d += "}"

    return n, d

class OBJECT_OT_snappyhexmeshgui_apply_locrotscale(bpy.types.Operator):
    """Apply LocRotScale (SnappyHexMeshGUI)"""
    bl_idname = "object.snappyhexmeshgui_apply_locrotscale"
    bl_label = "SnappyHexMeshGUI Apply LocRotScale"

    @classmethod
    def poll(cls, context):
        ob = context.active_object
        return (ob and ob.type == 'MESH' and context.mode == 'OBJECT')

    def execute(self, context):
        n = apply_locrotscale()
        self.report({'INFO'}, "LocRotScale applied to %d meshes" % n)
        return {'FINISHED'}

def apply_locrotscale():
    """Applies location, rotation and scale for all mesh objects"""

    for i in bpy.data.objects:
        i.select_set(False)

    n = 0
    for i in bpy.data.objects:
        if i.type != 'MESH':
            continue
        i.select_set(True)
        bpy.ops.object.transform_apply(location = True, scale = True, rotation = True)
        i.select_set(False)
        n += 1
    return n
