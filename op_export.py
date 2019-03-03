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
        gui = bpy.context.scene.snappyhexmeshgui
        snappy_template_path = gui.snappy_template_path
        block_mesh_template_path = gui.block_mesh_template_path
        export_path = gui.export_path

        # Get snappyHexMeshTemplate file
        blockData, snappyData = \
            export_initialize(self, block_mesh_template_path, \
                              snappy_template_path, export_path)
        if blockData is None or snappyData is None:
            return{'FINISHED'}

        # Carry out replacements to templates
        blockData = export_block_mesh_replacements(blockData)
        n, snappyData = export_snappy_replacements(snappyData)

        # Write blockMeshDict
        outfilename = bpy.path.abspath(export_path) \
                      + "/system/blockMeshDict"
        outfile = open(outfilename, 'w')
        outfile.write(''.join(blockData))
        outfile.close()

        # Write result to snappyHexMeshDict
        outfilename = bpy.path.abspath(export_path) \
                      + "/system/snappyHexMeshDict"
        outfile = open(outfilename, 'w')
        outfile.write(''.join(snappyData))
        outfile.close()

        self.report({'INFO'}, "Exported %d meshes " % n \
                    + "to: %r" % export_path)
        return {'FINISHED'}


def export_initialize(self, block_mesh_template_path, \
                      snappy_template_path, export_path):
    """Returns content of template dictionary files as text strings
    and creates directory structure undex export path.
    """

    l.debug("snappyHexMeshTemplate path: %r" % snappy_template_path)
    if not (os.path.isfile(snappy_template_path)):
        self.report({'ERROR'}, "Template not found: %r" \
                    % snappy_template_path)
        return None
    
    l.debug("blockMeshTemplate path: %r" % block_mesh_template_path)
    if not (os.path.isfile(block_mesh_template_path)):
        self.report({'ERROR'}, "Template not found: %r" \
                    % block_mesh_template_path)
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
    
    with open(snappy_template_path, 'r') as infile:
        snappyData = infile.readlines()

    with open(block_mesh_template_path, 'r') as infile:
        blockData = infile.readlines()

    return blockData, snappyData

    
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


def export_block_mesh_replacements(data):
    """Carry out replacements for key words in blockMeshDictTemplate with
    settings from GUI.
    """

    import datetime
    gui = bpy.context.scene.snappyhexmeshgui

    header_text = "// Exported by SnappyHexMesh GUI add-on for Blender v0.1" \
                  + "\n// Source file: " + bpy.context.blend_data.filepath \
                  + "\n// Export date: " + str(datetime.datetime.now())
    data = subst_value("HEADER", header_text, data)

    data = subst_value("DX", str(gui.block_mesh_delta[0]), data)
    data = subst_value("DY", str(gui.block_mesh_delta[1]), data)
    data = subst_value("DZ", str(gui.block_mesh_delta[2]), data)

    data = subst_value("XMIN", "%.6g" % gui.block_mesh_min[0], data)
    data = subst_value("YMIN", "%.6g" % gui.block_mesh_min[1], data)
    data = subst_value("ZMIN", "%.6g" % gui.block_mesh_min[2], data)

    data = subst_value("XMAX", "%.6g" % gui.block_mesh_max[0], data)
    data = subst_value("YMAX", "%.6g" % gui.block_mesh_max[1], data)
    data = subst_value("ZMAX", "%.6g" % gui.block_mesh_max[2], data)

    return data

def export_snappy_replacements(data):
    """Carry out replacements for key words in snappyHexMeshTemplate with
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

    data = subst_value("FEATURES", "    features ();", data)
    
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
