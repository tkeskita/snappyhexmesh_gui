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
        export_path = gui.export_path

        # Get snappyHexMeshTemplate file
        featuresData, blockData, snappyData = \
            export_initialize(self, gui.surface_features_template_path, \
                              gui.block_mesh_template_path, \
                              gui.snappy_template_path, export_path)
        if featuresData is None or blockData is None or snappyData is None:
            return{'FINISHED'}

        # Carry out replacements to templates
        featuresData = export_surface_features_replacements(featuresData)
        blockData = export_block_mesh_replacements(blockData)
        n, snappyData = export_snappy_replacements(snappyData)

        # Write surfaceFeaturesDict
        outfilename = bpy.path.abspath(export_path) \
                      + "/system/surfaceFeaturesDict"
        outfile = open(outfilename, 'w')
        outfile.write(''.join(featuresData))
        outfile.close()

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


def export_initialize(self, surface_features_template_path, \
                      block_mesh_template_path, \
                      snappy_template_path, export_path):
    """Initialization routine. Reads contents of surfaceFeaturesDictTemplate,
    blockMeshDictTemplate, and snappyHexMeshDictTempalte files as text strings
    and creates directory structure undex export path if needed.
    """

    abspath = bpy.path.abspath(export_path)
    if not abspath:
        self.report({'ERROR'}, "No path set! Please save Blender file to "
                    "a case folder and try again")
        return None, None, None
    l.debug("Export path: %r" % abspath)

    l.debug("snappyHexMeshTemplate path: %r" % snappy_template_path)
    if not (os.path.isfile(snappy_template_path)):
        self.report({'ERROR'}, "Template not found: %r" \
                    % snappy_template_path)
        return None, None, None
    
    l.debug("blockMeshTemplate path: %r" % block_mesh_template_path)
    if not (os.path.isfile(block_mesh_template_path)):
        self.report({'ERROR'}, "Template not found: %r" \
                    % block_mesh_template_path)
        return None, None, None

    l.debug("surfaceFeaturesDictTemplate path: %r" % surface_features_template_path)
    if not (os.path.isfile(surface_features_template_path)):
        self.report({'ERROR'}, "Template not found: %r" \
                    % surface_features_template_path)
        return None, None, None

    # Create folder structure if needed
    if not (os.path.isdir(abspath)):
        os.mkdir(abspath)

    for p in ["/constant", "/constant/triSurface", "/system"]:
        if not (os.path.isdir(abspath + p)):
            os.mkdir(abspath + p)
        
    if not (os.path.isdir(abspath + '/system')):
        self.report({'ERROR'}, "Couldn't create folders under %r" % abspath)
        return None, None, None

    # Copy skeleton files if needed
    copy_skeleton_files()
    
    with open(snappy_template_path, 'r') as infile:
        snappyData = infile.readlines()

    with open(block_mesh_template_path, 'r') as infile:
        blockData = infile.readlines()

    with open(surface_features_template_path, 'r') as infile:
        featuresData = infile.readlines()

    return featuresData, blockData, snappyData

    
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


def get_header_text():
    """Returns dictionary header comment text"""
    import datetime
    return "// Exported by SnappyHexMesh GUI add-on for Blender v0.9" \
        + "\n// Source file: " + bpy.context.blend_data.filepath \
        + "\n// Export date: " + str(datetime.datetime.now())

def export_surface_features_replacements(data):
    """Carry out replacements for key words in surfaceFeaturesDictTemplate with
    settings from GUI.
    """

    data = subst_value("HEADER", get_header_text(), data)

    # List all mesh object STL names included in export
    d=''
    for i in bpy.data.objects:
        if i.type != 'MESH':
            continue
        if not i.shmg_include_in_export:
            continue
        if not i.shmg_include_feature_extraction:
            continue
        d += "   \"%s.stl\"\n" % i.name

    data = subst_value("FEATURESURFACES", d, data)
    return data

def export_block_mesh_replacements(data):
    """Carry out replacements for key words in blockMeshDictTemplate with
    settings from GUI.
    """

    gui = bpy.context.scene.snappyhexmeshgui

    data = subst_value("HEADER", get_header_text(), data)

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
    
    gui = bpy.context.scene.snappyhexmeshgui

    data = subst_value("HEADER", get_header_text(), data)
    
    data = subst_value("DO_SNAP", str(gui.do_snapping).lower(), data)
    data = subst_value("DO_ADD_LAYERS", str(gui.do_add_layers).lower(), data)

    n, geo = export_geometries()
    data = subst_value("GEOMETRY", geo, data)

    data = subst_value("FEATURES", export_surface_features(), data)
    data = subst_value("REFINEMENTSURFACES", export_refinement_surfaces(), data)
    data = subst_value("REFINEMENTREGIONS", "        ", data)
    data = subst_value("LAYERS", export_surface_layers(), data)
    
    data = subst_value("LOCATIONINMESH", get_location_in_mesh(), data)

    data = subst_value("MAXNONORTHO", str(gui.max_non_ortho), data)

    return n, data

def export_geometries():
    """Creates geometry entries for snappyHexMeshDict and
    exports meshes in STL format to case/constant/triSurface folder.
    Returns number of exported meshes and the dictionary text string.
    """

    from .op_object import get_object_bbox_coords, get_surface_area

    n = 0 # Number of exported geometries
    # Collect dictionary string to d
    d = "geometry\n{\n"

    # First deselect every object, since STL export is done by selection
    for i in bpy.data.objects:
        i.select_set(False)

    for i in bpy.data.objects:
        if i.type != 'MESH':
            continue
        if not i.shmg_include_in_export:
            continue

        # Collect mesh min and max bounds and area to info string
        bb_min, bb_max = get_object_bbox_coords(i)
        bb_min_str = "        // Min Bounds = [%12.5e %12.5e %12.5e]\n" % (bb_min[0], bb_min[1], bb_min[2])
        bb_max_str = "        // Max Bounds = [%12.5e %12.5e %12.5e]\n" % (bb_max[0], bb_max[1], bb_max[2])
        area_str = "        // Area = %.5e\n" % get_surface_area(i)
        info_str = bb_min_str + bb_max_str + area_str

        # Add to dictionary string
        d += "    %s\n" % i.name \
             + "    {\n        type triSurfaceMesh;\n" \
             + "        file \"%s.stl\";\n" % i.name \
             + info_str + "    }\n"
        # Note to self: Tried to add export_geometry_regions inside d,
        # but it seems that regions are not used for STLs, so left out.

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

def export_geometry_regions(obj):
    """Creates regions for geometry entries in snappyHexMeshDict
    for object obj
    """

    # Collect dictionary string to d
    d = ""
    d += "        regions { " + str(obj.name) + " { " \
         + "name " + str(obj.name) + "; } }\n"
    return d


def export_refinement_surfaces():
    """Creates refinement surface entries for snappyHexMeshDict"""

    # Collect dictionary string to d
    d = ""

    for i in bpy.data.objects:
        if i.type != 'MESH':
            continue
        if not i.shmg_include_in_export:
            continue
        if not i.shmg_include_snapping:
            continue

        d += "        %s\n" % i.name \
             + "        {\n            level" \
             + " (%d " % i.shmg_surface_min_level \
             + "%d);\n" % i.shmg_surface_max_level \
             + "            patchInfo { type " + i.shmg_patch_info_type + "; }\n" \
             + get_face_zone_definitions(i) \
             + get_cell_zone_definitions(i) \
             + "        }\n"
    return d

def get_face_zone_definitions(obj):
    """Produces face zone dict entry addition for refinementSurfaces
    for object obj
    """

    d=""
    if (obj.shmg_face_zone_type == 'none'):
        return d

    d += 12*" " + "faceZone " + str(obj.name) + ";\n"
    d += 12*" " + "faceType " + str(obj.shmg_face_zone_type) + ";\n"
    return d

def get_cell_zone_definitions(obj):
    """Produces cell zone dict entry addition for refinementSurfaces
    for object obj
    """

    d=""
    if (obj.shmg_cell_zone_type == 'none'):
        return d

    d += 12*" " + "cellZone " + str(obj.name) + ";\n"
    d += 12*" " + "cellZoneInside " + str(obj.shmg_cell_zone_type) + ";\n"
    return d


def export_surface_features():
    """Creates surface features entries for snappyHexMeshDict"""

    # Collect dictionary string to d
    d = ""

    for i in bpy.data.objects:
        if i.type != 'MESH':
            continue
        if not i.shmg_include_in_export:
            continue
        if not i.shmg_include_feature_extraction:
            continue
        d += "        {\n            file \"" \
             + str(i.name) + ".eMesh\";\n" \
             + "            level %d;\n" % i.shmg_feature_edge_level \
             + "        }\n"
    return d

def export_surface_layers():
    """Creates surface layer entries for snappyHexMeshDict"""

    # Collect dictionary string to d
    d = ""

    for i in bpy.data.objects:
        if i.type != 'MESH':
            continue
        if not i.shmg_include_in_export:
            continue
        d += "        " + str(i.name) + "\n" \
             + "        {\n " \
             + "            nSurfaceLayers %d;\n" % i.shmg_surface_layers \
             + "        }\n"
    return d

def copy_skeleton_files():
    """Copies OpenFOAM skeleton files to case directory
    unless they already exist there
    """

    from shutil import copyfile
    export_path = bpy.context.scene.snappyhexmeshgui.export_path
    abspath = bpy.path.abspath(export_path)

    for i in ["controlDict", "fvSchemes", "fvSolution"]:
        filepath = abspath + "system/" + i
        if not (os.path.isfile(filepath)):
            sourcepath = os.path.dirname(__file__) + "/skel/" + i
            copyfile(sourcepath, filepath)
            l.debug("Copied skeleton file from: %s" % filepath)
    return None

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

class OBJECT_OT_snappyhexmeshgui_add_location_in_mesh_object(bpy.types.Operator):
    """Add Location in Mesh Object (SnappyHexMeshGUI)"""
    bl_idname = "object.snappyhexmeshgui_add_location_in_mesh_object"
    bl_label = "SnappyHexMeshGUI Add Location In Mesh Object"

    @classmethod
    def poll(cls, context):
        ob = context.active_object
        return (ob and ob.type == 'MESH' and context.mode == 'OBJECT')

    def execute(self, context):
        if not [i for i in bpy.data.objects if i.name == "Location In Mesh"]:
            bpy.ops.object.empty_add(type='SPHERE', radius=0.2, view_align=False)
            bpy.context.active_object.name = "Location In Mesh"
            self.report({'INFO'}, "Added Location In Mesh Object")
        else:
            self.report({'INFO'}, "Error: Location In Mesh Object already exists!")
        return {'FINISHED'}

def get_location_in_mesh():
    """Creates dictionary string for a user specified location in mesh.
    Coordinates of object "Location In Mesh" is used, or if it does not
    exist, zero coordinates.
    """
    d = "locationInMesh "
    for i in bpy.data.objects:
        if i.name == 'Location In Mesh':
            d += "(" + str(i.location.x) + " " + str(i.location.y) + " " + \
                 str(i.location.z) + ");"
            return d
    return d + "(0 0 0);"

