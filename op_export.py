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
import bmesh

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
        from copy import deepcopy
        l.debug("Starting export")
        gui = bpy.context.scene.snappyhexmeshgui
        export_path = gui.export_path

        # Get snappyHexMeshTemplate file
        featuresData, blockData, snappyData, \
            decomposepardictData, createbafflesdictData, \
            meshqualitydictData = \
            export_initialize(self, gui.surface_features_template_path, \
                              gui.block_mesh_template_path, \
                              gui.snappy_template_path, \
                              gui.decomposepardict_template_path, \
                              gui.createbafflesdict_template_path, \
                              gui.meshqualitydict_template_path, \
                              export_path)
        if featuresData is None or blockData is None or snappyData is None \
           or decomposepardictData is None or createbafflesdictData is None \
           or meshqualitydictData is None:
            return{'FINISHED'}

        # Carry out replacements to templates other than snappyHexMeshDict
        framework = gui.openfoam_framework
        featuresData = export_surface_features_replacements(featuresData, framework)
        blockData = export_block_mesh_replacements(blockData, framework)
        decomposepardictData = export_decomposepardict_replacements(decomposepardictData)
        createbafflesdictData = export_createbafflesdict_replacements(createbafflesdictData)
        meshqualitydictData = export_meshqualitydict_replacements(meshqualitydictData)

        # Write surfaceFeaturesDict
        # openfoam.org uses surfaceFeaturesDict, openfoam.com surfaceFeatureExtract
        if framework == 'openfoam.org':
            outfilename = os.path.join(bpy.path.abspath(export_path), \
                                       'system', 'surfaceFeaturesDict')
        elif framework == 'openfoam.com':
            outfilename = os.path.join(bpy.path.abspath(export_path), \
                                       'system', 'surfaceFeatureExtractDict')
        else:
            raise Exception("unknown OpenFOAM framework" + framework)

        outfile = open(outfilename, 'w')
        outfile.write(''.join(featuresData))
        outfile.close()

        # Write blockMeshDict
        if gui.do_block_mesh:
            outfilename = os.path.join(bpy.path.abspath(export_path), \
                          'system', 'blockMeshDict')
            outfile = open(outfilename, 'w')
            outfile.write(''.join(blockData))
            outfile.close()

        # Write result to snappyHexMeshDicts
        dict_numbers = get_dict_numbers()
        # Always create base snappyHexMeshDict
        if 1 not in dict_numbers:
            dict_numbers.append(1)
        for i in dict_numbers:
            snappyDataCopy = deepcopy(snappyData)
            n, snappyDataCopy = export_snappy_replacements(snappyDataCopy, dict_number=i)
            if n==0:
                self.report({'ERROR'}, "Can't export object %r " % snappyDataCopy \
                            + " because it is not visible")
                return {'FINISHED'}

            snappy_filename = 'snappyHexMeshDict'
            if i > 1:
                snappy_filename += str(i)
            outfilename = os.path.join(bpy.path.abspath(export_path), \
                                       'system', snappy_filename)
            outfile = open(outfilename, 'w')
            outfile.write(''.join(snappyDataCopy))
            outfile.close()

        # Write decomposeParDict
        outfilename = os.path.join(bpy.path.abspath(export_path), \
                                   'system', 'decomposeParDict')
        outfile = open(outfilename, 'w')
        outfile.write(''.join(decomposepardictData))
        outfile.close()

        # Write createBafflesDict
        outfilename = os.path.join(bpy.path.abspath(export_path), \
                                   'system', 'createBafflesDict')
        outfile = open(outfilename, 'w')
        outfile.write(''.join(createbafflesdictData))
        outfile.close()

        # Write meshQualityDict
        outfilename = os.path.join(bpy.path.abspath(export_path), \
                                   'system', 'meshQualityDict')
        outfile = open(outfilename, 'w')
        outfile.write(''.join(meshqualitydictData))
        outfile.close()

        self.report({'INFO'}, "Exported %d meshes " % n \
                    + "to: %r" % export_path)
        return {'FINISHED'}

def get_dict_numbers():
    """Return list of dict numbers for layer addition"""

    dict_numbers = []
    for i in bpy.data.objects:
        if i.type != 'MESH':
            continue
        if not i.shmg_include_in_export:
            continue
        if i.shmg_surface_layers == -1:
            continue
        if i.shmg_dict_number in dict_numbers:
            continue
        dict_numbers.append(i.shmg_dict_number)
    return dict_numbers

def export_initialize(self, surface_features_template_path, \
                      block_mesh_template_path, \
                      snappy_template_path, \
                      decomposepardict_template_path, \
                      createbafflesdict_template_path, \
                      meshqualitydict_template_path, \
                      export_path):
    """Initialization routine. Reads contents of
    surfaceFeaturesDictTemplate, blockMeshDictTemplate,
    snappyHexMeshDictTemplate and decomposeParDict files as text
    strings and creates directory structure undex export path if
    needed.
    """

    abspath = bpy.path.abspath(export_path)
    if not abspath:
        self.report({'ERROR'}, "No path set! Please save Blender file to "
                    "a case folder and try again")
        return None, None, None, None, None, None
    l.debug("Export path: %r" % abspath)

    l.debug("snappyHexMeshTemplate path: %r" % snappy_template_path)
    if not (os.path.isfile(snappy_template_path)):
        self.report({'ERROR'}, "Template not found: %r" \
                    % snappy_template_path)
        return None, None, None, None, None, None
    
    l.debug("blockMeshTemplate path: %r" % block_mesh_template_path)
    if not (os.path.isfile(block_mesh_template_path)):
        self.report({'ERROR'}, "Template not found: %r" \
                    % block_mesh_template_path)
        return None, None, None, None, None, None

    l.debug("surfaceFeaturesDictTemplate path: %r" % surface_features_template_path)
    if not (os.path.isfile(surface_features_template_path)):
        self.report({'ERROR'}, "Template not found: %r" \
                    % surface_features_template_path)
        return None, None, None, None, None, None

    l.debug("decomposeParDictTemplate path: %r" % decomposepardict_template_path)
    if not (os.path.isfile(decomposepardict_template_path)):
        self.report({'ERROR'}, "Template not found: %r" \
                    % decomposepardict_template_path)
        return None, None, None, None, None, None

    l.debug("createBafflesParDictTemplate path: %r" % createbafflesdict_template_path)
    if not (os.path.isfile(createbafflesdict_template_path)):
        self.report({'ERROR'}, "Template not found: %r" \
                    % createbafflesdict_template_path)
        return None, None, None, None, None, None

    l.debug("meshQualityDictTemplate path: %r" % meshqualitydict_template_path)
    if not (os.path.isfile(meshqualitydict_template_path)):
        self.report({'ERROR'}, "Template not found: %r" \
                    % meshqualitydict_template_path)
        return None, None, None, None, None, None

    # Create folder structure if needed
    if not (os.path.isdir(abspath)):
        os.mkdir(abspath)

    for p in ['constant', 'system']:
        if not (os.path.isdir(os.path.join(abspath, p))):
            os.mkdir(os.path.join(abspath, p))

    if not (os.path.isdir(os.path.join(abspath, 'constant', 'triSurface'))):
        os.mkdir(os.path.join(abspath, 'constant', 'triSurface'))

    if not (os.path.isdir(os.path.join(abspath, 'system'))):
        self.report({'ERROR'}, "Couldn't create folders under %r" % abspath)
        return None, None, None, None, None, None

    # Copy skeleton files if needed
    copy_skeleton_files()
    
    with open(snappy_template_path, 'r') as infile:
        snappyData = infile.readlines()

    with open(block_mesh_template_path, 'r') as infile:
        blockData = infile.readlines()

    with open(surface_features_template_path, 'r') as infile:
        featuresData = infile.readlines()

    with open(decomposepardict_template_path, 'r') as infile:
        decomposepardictData = infile.readlines()

    with open(createbafflesdict_template_path, 'r') as infile:
        createbafflesdictData = infile.readlines()

    # Use disabled mesh quality dict if quality criteria are to be
    # disabled, and normal template otherwise
    gui = bpy.context.scene.snappyhexmeshgui
    if gui.disable_quality_criteria:
        file_path=os.path.join(os.path.dirname(__file__), 'skel', 'disabledMeshQualityDict')
        with open(file_path, 'r') as infile:
            meshqualitydictData = infile.readlines()
    else:
        with open(meshqualitydict_template_path, 'r') as infile:
            meshqualitydictData = infile.readlines()

    create_run(abspath)

    return featuresData, blockData, snappyData, decomposepardictData, \
        createbafflesdictData, meshqualitydictData

    
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
    return "// Exported by SnappyHexMesh GUI add-on for Blender v1.7" \
        + "\n// Source file: " + bpy.context.blend_data.filepath \
        + "\n// Export date: " + str(datetime.datetime.now())

def export_surface_features_replacements(data, framework):
	
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
        if i.name.endswith("_eMesh"):
            continue
        if (i.name + "_eMesh") in bpy.data.objects:
            continue
	
        if framework == 'openfoam.org':
            d += "    \"%s.stl\"\n" % i.name
        elif framework == 'openfoam.com':
            d += "%s.stl\n{\n    extractionMethod extractFromSurface;\n    extractFromSurfaceCoeffs { includedAngle 150; }\n    writeObj yes;\n}\n\n" % i.name
    if framework == 'openfoam.org':
        data = subst_value("FEATURESURFACES", "\nsurfaces\n(\n" + d + \
                           ");\n\nincludedAngle 150;\nwriteObj yes;\n", data)
    else:
        data = subst_value("FEATURESURFACES", d, data)
		
    return data

def export_block_mesh_replacements(data, framework):
    """Carry out replacements for key words in blockMeshDictTemplate with
    settings from GUI.
    """

    gui = bpy.context.scene.snappyhexmeshgui

    data = subst_value("HEADER", get_header_text(), data)

    if framework == 'openfoam.org':
        scale_command = "convertToMeters"
    elif framework == 'openfoam.com':
        scale_command = "scale"
    data = subst_value("EXPORT_SCALE_COMMAND", scale_command, data)
    data = subst_value("EXPORT_SCALE", "%.6g" % gui.export_scale, data)

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

def export_decomposepardict_replacements(data):
    """Carry out replacements for decomposeParDict."""

    gui = bpy.context.scene.snappyhexmeshgui
    data = subst_value("HEADER", get_header_text(), data)
    data = subst_value("NCPUS", str(gui.number_of_cpus), data)
    return data

def export_createbafflesdict_replacements(data):
    """Carry out replacements for createBafflesDict."""

    data = subst_value("HEADER", get_header_text(), data)
    d=''
    for i in bpy.data.objects:
        if i.type != 'MESH':
            continue
        if not i.shmg_include_in_export:
            continue
        if i.shmg_face_zone_type != 'internal':
            continue
        if i.name.endswith("_eMesh"):
            continue

        # Add entries of this object to createBafflesDict
        d += "    %s\n" % i.name \
             + "    {\n" \
             + "        type faceZone;\n" \
             + "        zoneName %s;\n\n" % i.name \
             + "        patches\n        {\n" \
             + "            owner\n            {\n" \
             + "                name %s;\n" % i.name \
             + "                type patch;\n" \
             + "            }\n\n" \
             + "            neighbour\n            {\n" \
             + "                name %s_2;\n" % i.name \
             + "                type patch;\n" \
             + "            }\n" \
             + "        }\n" \
             + "    }\n\n"

    data = subst_value("BAFFLE_ENTRIES", d, data)
    return data

def export_meshqualitydict_replacements(data):
    """Carry out replacements for meshQualityDict."""

    gui = bpy.context.scene.snappyhexmeshgui
    header_text = get_header_text()
    data = subst_value("HEADER", header_text, data)
    data = subst_value("MAX_NON_ORTHO", str(gui.max_non_ortho), data)
    data = subst_value("MAX_INTERNAL_SKEWNESS", str(gui.max_internal_skewness), data)
    data = subst_value("RELAXED_MAX_NON_ORTHO", str(gui.relaxed_max_non_ortho), data)
    data = subst_value("MIN_TWIST", "%g" % gui.min_twist, data)
    # Disabled relaxed min triangle twist for now. It does not seem to
    # play much role for layer addition.
    # data = subst_value("RELAXED_MIN_TWIST", "%g" % gui.relaxed_min_twist, data)

    return data

def export_snappy_replacements(data, dict_number):
    """Carry out replacements for key words in snappyHexMeshTemplate with
    settings from GUI. If second_add_layers is True, then this function
    creates the contents for Additional Layers Phase only.
    """
    
    gui = bpy.context.scene.snappyhexmeshgui
    framework = gui.openfoam_framework

    data = subst_value("HEADER", get_header_text(), data)
    
    if dict_number == 1:
        data = subst_value("DO_CASTELLATION", str(gui.do_castellation).lower(), data)
        data = subst_value("DO_SNAP", str(gui.do_snapping).lower(), data)
        if not gui.do_add_layers:
            data = subst_value("DO_ADD_LAYERS", "false", data)
        elif 1 in get_dict_numbers():
            data = subst_value("DO_ADD_LAYERS", "true", data)
        else:
            data = subst_value("DO_ADD_LAYERS", "false", data)
    else:
        data = subst_value("DO_CASTELLATION", "false", data)
        data = subst_value("DO_SNAP", "false", data)
        data = subst_value("DO_ADD_LAYERS", "true", data)

    n, geo = export_geometries()
    if n==0:
        return n, geo

    data = subst_value("GEOMETRY", geo, data)

    data = subst_value("FEATURES", export_surface_features(), data)
    data = subst_value("REFINEMENTSURFACES", export_refinement_surfaces(), data)
    data = subst_value("REFINEMENTREGIONS", export_refinement_volumes(), data)
    data = subst_value("LAYERS", export_surface_layers(dict_number), data)
    
    data = subst_value("LOCATIONINMESH", get_location_in_mesh(), data)

    data = subst_value("LAYER_FEATURE_ANGLE", "%g" % gui.surface_layer_feature_angle, data)
    # Disabled variable nSmoothSurfaceNormals for now
    # data = subst_value("NSMOOTH_SURFACE_NORMALS", str(get_nsmooth_surface_normals()), data)
    data = subst_value("FEATURE_SNAP_ITER", str(gui.feature_snap_iter), data)

    data = subst_value("EXPANSION_RATIO", "%g" % gui.surface_layer_expansion_ratio, data)
    data = subst_value("FINAL_THICKNESS", "%g" % gui.surface_layer_final_thickness, data)
    data = subst_value("MIN_THICKNESS", "%g" % gui.surface_layer_minimum_thickness, data)
    # Disable variable nOuterIter for now
    # data = subst_value("SHRINKING_OUTER_ITER", str(get_shrinking_outer_iter()), data)

    if framework == 'openfoam.org':
        data = subst_value("ANGLE","minMedianAxisAngle",data)
    else:
        data = subst_value("ANGLE","minMedialAxisAngle",data)

    return n, data

def get_max_number_of_layers():
    """Help function to calculate maximum number of layers.
    """

    max_value = 0;
    for i in bpy.data.objects:
        if i.type != 'MESH':
            continue
        if not i.shmg_include_in_export:
            continue
        if i.shmg_surface_layers > max_value:
            max_value = i.shmg_surface_layers
    return max_value

def get_nsmooth_surface_normals():
    """Calculates a value for nSmoothSurfaceNormals for layer addition phase.
    Looks like 3 times number of maximum layers works nicely.
    """

    max_value = get_max_number_of_layers()
    return (3 * max_value)

def get_shrinking_outer_iter():
    """Calculates a value for nOuterIter for layer addition phase.
    """

    from math import ceil
    # Maximum number of layers seems to give best layer coverage
    max_value = get_max_number_of_layers()
    return max_value

def export_geometries():
    """Creates geometry entries for snappyHexMeshDict and
    exports meshes in STL format to case/constant/triSurface folder.
    Returns number of exported meshes and the dictionary text string.
    """

    gui = bpy.context.scene.snappyhexmeshgui
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
        # Return error if object is not visible (it can't be exported)
        if not i.visible_get():
            return 0, i.name

        # Collect mesh min and max bounds and area to info string
        bb_min, bb_max = get_object_bbox_coords(i)
        bb_min_str = "        // Min Bounds = [%12.5e %12.5e %12.5e]\n" % (bb_min[0], bb_min[1], bb_min[2])
        bb_max_str = "        // Max Bounds = [%12.5e %12.5e %12.5e]\n" % (bb_max[0], bb_max[1], bb_max[2])
        area_str = "        // Area = %.5e\n" % get_surface_area(i)
        info_str = bb_min_str + bb_max_str + area_str

        # Add to dictionary string, except not edge mesh objects
        if not i.name.endswith("_eMesh"):
            d += "    %s\n" % i.name \
                + "    {\n        type triSurfaceMesh;\n" \
                + "        file \"%s.stl\";\n" % i.name \
                + info_str + "    }\n"
        # Note to self: Tried to add export_geometry_regions inside d,
        # but it seems that regions are not used for STLs, so left out.

        export_path = gui.export_path
        abspath = bpy.path.abspath(export_path)
        i.select_set(True)

        # Export normal meshes to constant/triSurface/name.stl
        if not i.name.endswith("_eMesh"):
            outpath = os.path.join(abspath, 'constant', 'triSurface', "%s.stl" % i.name)
            bpy.ops.export_mesh.stl(
                filepath=outpath, check_existing=False, \
                axis_forward='Y', axis_up='Z', filter_glob="*.stl", \
                use_selection=True, global_scale=gui.export_scale, use_scene_unit=True, \
                ascii=gui.export_stl_ascii, use_mesh_modifiers=True)
        # Edge meshes are exported to constant/triSurface/name.obj
        else:
            outpath = os.path.join(abspath, 'constant', 'triSurface', "%s.obj" % i.name)
            bpy.ops.wm.obj_export(
                filepath=outpath, check_existing=False, \
                forward_axis='Y', up_axis='Z', global_scale=gui.export_scale, \
                apply_modifiers=True, export_selected_objects=True, \
                export_materials=False, export_uv=False, export_normals=False
            )
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
        if i.name.endswith("_eMesh"):
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

def export_refinement_volumes():
    """Creates refinement regions (volumes) entries for snappyHexMeshDict"""

    # Collect dictionary string to d
    d = ""

    for i in bpy.data.objects:
        if i.type != 'MESH':
            continue
        if not i.shmg_include_in_export:
            continue
        if i.shmg_volume_type == 'none':
            continue
        if i.name.endswith("_eMesh"):
            continue

        d += "        %s\n" % i.name + "        {\n" \
             + "            mode " + str(i.shmg_volume_type) + ";\n" \
             + "            levels ((" + str(i.shmg_volume_level) \
             + " " + str(i.shmg_volume_level) + "));\n" \
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
        if i.name.endswith("_eMesh"):
            continue
        d += "        {\n            file \"" \
             + str(i.name) + ".eMesh\";\n" \
             + "            level %d;\n" % i.shmg_feature_edge_level \
             + "        }\n"
    return d

def export_surface_layers(dict_number):
    """Creates surface layer entries for snappyHexMeshDict file number dict_number"""

    # Collect dictionary string to d
    d = ""

    for i in bpy.data.objects:
        if i.type != 'MESH':
            continue
        if not i.shmg_include_in_export:
            continue
        if i.shmg_dict_number != dict_number:
            continue
        if i.name.endswith("_eMesh"):
            continue

        if i.shmg_surface_layers > 0:
            d += "        " + str(i.name) + "\n" \
                 + "        {\n " \
                 + "           nSurfaceLayers %d;\n" % i.shmg_surface_layers
            if i.shmg_specify_object_layer_properties:
                d += "            expansionRatio %g;\n" % i.shmg_obj_surface_layer_expansion_ratio
                d += "            finalLayerThickness %g;\n" % i.shmg_obj_surface_layer_final_thickness
                d += "            minThickness %g;\n" % i.shmg_obj_surface_layer_minimum_thickness
            d += "        }\n"

        if i.shmg_slave_side_layers:
            d += "        " + str(i.name) + "_slave\n" \
                 + "        {\n " \
                 + "           nSurfaceLayers %d;\n" % i.shmg_surface_layers
            if i.shmg_specify_object_layer_properties:
                d += "            expansionRatio %g;\n" % i.shmg_obj_surface_layer_expansion_ratio
                d += "            finalLayerThickness %g;\n" % i.shmg_obj_surface_layer_final_thickness
                d += "            minThickness %g;\n" % i.shmg_obj_surface_layer_minimum_thickness
            d += "        }\n"

    return d

def copy_skeleton_files():
    """Copies OpenFOAM skeleton files to case directory
    unless they already exist there
    """

    from shutil import copyfile
    export_path = bpy.context.scene.snappyhexmeshgui.export_path
    abspath = bpy.path.abspath(export_path)

    for i in ["controlDict", "fvSchemes", "fvSolution"]:
        filepath = os.path.join(abspath, 'system', i)
        if not (os.path.isfile(filepath)):
            sourcepath = os.path.join(os.path.dirname(__file__), 'skel', i)
            copyfile(sourcepath, filepath)
            l.debug("Copied skeleton file from: %s" % filepath)

    # Create empty case.foam file
    from pathlib import Path
    Path(os.path.join(abspath, "case.foam")).touch()
    return None

def create_run(abspath):
    """Creates a bash run script in the case directory
    """

    import os
    import stat
    gui = bpy.context.scene.snappyhexmeshgui

    if gui.openfoam_framework == 'openfoam.org':
        extract_command = "surfaceFeatures"
    else:
        extract_command = "surfaceFeatureExtract"

    run = """#!/bin/bash
# OpenFOAM Run script generated by SnappyHexMesh GUI

function run_and_log(){
  # Run a command and redirect it's output to a log file.
  # First argument is the program name (log file name),
  # rest of the arguments contain the string to run the program.

  cmd=$1
  run_commands="${@:2}"
  echo "Running $cmd with command: $run_commands"
  $run_commands &> log."$cmd"
  if [ $? -ne 0 ]; then
    echo "Running $cmd failed, see log."$cmd". Exiting."
    exit 1
  fi
}

"""
    run += "run_and_log blockMesh blockMesh\n"
    run += "run_and_log %s %s\n" % (extract_command, extract_command)

    # Add surfaceFeatureConvert commands for all _eMesh objects
    i = 0
    for ob in bpy.data.objects:
        if not (ob.name + "_eMesh") in bpy.data.objects:
            continue
        i += 1
        run += "run_and_log surfaceFeatureConvert_" + str(i) + \
            " surfaceFeatureConvert constant/triSurface/" + ob.name + "_eMesh.obj" + \
            " constant/triSurface/" + ob.name + ".eMesh\n"

    if gui.number_of_cpus == 1:
        run += "run_and_log snappyHexMesh snappyHexMesh\n"
        run += "run_and_log checkMesh checkMesh -latestTime\n"
        run += "# run_and_log postProcess postProcess -time '1:'\n"
    else:
        run += "run_and_log decomposePar decomposePar\n" + \
            "run_and_log snappyHexMesh mpirun -np %s snappyHexMesh -parallel\n" % gui.number_of_cpus + \
            "run_and_log checkMesh mpirun -np %s checkMesh -latestTime -parallel\n" % gui.number_of_cpus + \
            "# run_and_log postProcess mpirun -np %s postProcess -time '1:' -parallel\n" % gui.number_of_cpus + \
            "run_and_log reconstructParMesh reconstructParMesh -latestTime\n" + \
            "run_and_log reconstructPar reconstructPar -latestTime\n" + \
            "# run_and_log checkMesh checkMesh -latestTime\n"

    run += "echo \"Run done!\"\n"

    filename = os.path.join(abspath, "run")
    outfile = open(filename, 'w')
    outfile.write(''.join(run))
    outfile.close()
    # Make sure the file has executable attribute
    st = os.stat(filename)
    os.chmod(filename, st.st_mode | stat.S_IEXEC)

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
        bpy.ops.object.transform_apply(location=True, scale=True, rotation=True, isolate_users=True)
        i.select_set(False)
        n += 1
    return n

class OBJECT_OT_snappyhexmeshgui_cleanup_meshes(bpy.types.Operator):
    """Clean Up Meshes (SnappyHexMeshGUI). Merges closeby vertices and recalculates outside normals for selected mesh objects"""
    bl_idname = "object.snappyhexmeshgui_cleanup_meshes"
    bl_label = "SnappyHexMeshGUI Clean Up Meshes"

    @classmethod
    def poll(cls, context):
        ob = context.active_object
        return (ob and ob.type == 'MESH' and context.mode == 'OBJECT')

    def execute(self, context):
        text = cleanup_meshes()
        if len(text) > 0:
            self.report({'INFO'}, " ".join(text))
        else:
            self.report({'INFO'}, "No objects selected, did nothing")
        return {'FINISHED'}

def cleanup_meshes():
    """Merges nearby vertices and recalculates face outside normals"""

    # Generate a list of objects to process
    obs = []
    for ob in bpy.data.objects:
        if ob.select_get() == False:
            continue
        ob.select_set(False)
        if ob.type != 'MESH':
            continue
        obs.append(ob)

    if not obs:
        return []
    text = []

    # Convert merge distance string to float
    gui = bpy.context.scene.snappyhexmeshgui
    try:
        gui.merge_distance = float(gui.merge_distance_string)
    except:
        text.append("ERROR: Merge Distance is not a number! Aborted operation!")
        return text

    # Process each selected object
    text.append("Merged vectices:")
    for ob in obs:
        bpy.ops.object.mode_set(mode='OBJECT')
        original_hide_mode = ob.hide_get()
        ob.hide_set(False)
        ob.select_set(True)
        bpy.ops.object.mode_set(mode='EDIT')
        bm = bmesh.from_edit_mesh(ob.data)
        nverts0 = len(bm.verts)
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=bpy.context.scene.snappyhexmeshgui.merge_distance)
        bm.verts.index_update()
        nverts1 = len(bm.verts)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        bmesh.update_edit_mesh(mesh=ob.data)
        bm.free()
        bpy.ops.object.mode_set(mode='OBJECT')
        ob.select_set(False)
        ob.hide_set(original_hide_mode)
        n_merged_vertices = nverts0 - nverts1
        text.append(ob.name + ":" + str(n_merged_vertices))

    for ob in obs:
        ob.select_set(True)

    return text


class OBJECT_OT_snappyhexmeshgui_clean_case_dir(bpy.types.Operator):
    """Clean Case Directory (Remove folders 1-9 constant system processor*) (SnappyHexMeshGUI)"""
    bl_idname = "object.snappyhexmeshgui_clean_case_dir"
    bl_label = "SnappyHexMeshGUI Clean Case Directory"

    @classmethod
    def poll(cls, context):
        ob = context.active_object
        return (ob and ob.type == 'MESH' and context.mode == 'OBJECT')

    def execute(self, context):
        deleted_names = clean_case_dir()
        self.report({'INFO'}, "Deleted: " + deleted_names)
        return {'FINISHED'}

def clean_case_dir():
    """Removes OpenFOAM directories (if they exist) from blend file save
    location to clean up case folder and make it ready for new export.
    """

    from shutil import rmtree
    names = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "system", "constant"]
    export_path = bpy.context.scene.snappyhexmeshgui.export_path
    abspath = bpy.path.abspath(export_path)
    l.debug ("Absolute path is %r" % abspath)
    deleted_names = ''

    from os import walk
    for dirpath, directorynames, filenames in walk(abspath):
        # Add processor directories for deletion, if any
        for dirname in directorynames:
            if dirname.startswith("processor"):
                names.append(dirname)
        # Delete old log files
        for filename in filenames:
            if filename.startswith("log."):
                names.append(filename)
            if filename == "run":
                names.append(filename)

    for i in names:
        filepath = os.path.join(abspath, i)
        if os.path.isdir(filepath):
            rmtree(filepath)
            deleted_names += i + " "
        elif os.path.isfile(filepath):
            os.remove(filepath)
            deleted_names += i + " "

    if not deleted_names:
        return "None"
    return deleted_names


class OBJECT_OT_snappyhexmeshgui_add_location_in_mesh_object(bpy.types.Operator):
    """Add Location in Mesh Object (SnappyHexMeshGUI)"""
    bl_idname = "object.snappyhexmeshgui_add_location_in_mesh_object"
    bl_label = "SnappyHexMeshGUI Add Location In Mesh Object"

    @classmethod
    def poll(cls, context):
        ob = context.active_object
        return (ob and ob.type == 'MESH' and context.mode == 'OBJECT')

    def execute(self, context):
        bpy.ops.object.empty_add(type='SPHERE', radius=0.2)
        bpy.context.active_object.name = "Location In Mesh region0"
        self.report({'INFO'}, "Added %r" % bpy.context.active_object.name)
        return {'FINISHED'}

def get_location_in_mesh():
    """Creates dictionary string for a user specified location in mesh.
    Coordinates of object "Location In Mesh" is used, or if it does not
    exist, zero coordinates.
    """

    # Find locations in mesh objects
    locs = []
    for i in bpy.data.objects:
        if i.type != "EMPTY":
            continue
        if i.name.startswith("Location In Mesh"):
            locs.append(i)

    # Export based on the number of objects
    if len(locs) == 0:
        return "locationInMesh (0 0 0);"

    elif len(locs) == 1:
        i = locs[0]
        return "locationInMesh (" + str(i.location.x) + " " + str(i.location.y) + " " + str(i.location.z) + ");"
    else:
        d = "locationsInMesh\n    (\n"
        for i in locs:
            d += "        ((" + str(i.location.x) + " " + str(i.location.y) + " " + str(i.location.z) + ") " + i.name.split("Location In Mesh")[1] + ")\n"
        d += "    );"
        return d

class OBJECT_OT_snappyhexmeshgui_copy_settings_to_objects(bpy.types.Operator):
    """Copy Settings to Objects (SnappyHexMeshGUI)"""
    bl_idname = "object.snappyhexmeshgui_copy_settings_to_objects"
    bl_description = "Copy Settings from Active Object to Selected Objects"
    bl_label = "SnappyHexMeshGUI Copy Settings to Objects"

    @classmethod
    def poll(cls, context):
        ob = context.active_object
        return (ob and ob.type == 'MESH' and context.mode == 'OBJECT')

    def execute(self, context):
        n = copy_settings_to_objects()
        self.report({'INFO'}, "Copied SnappyHexMesh Settings to %d Objects" % n)
        return {'FINISHED'}

def copy_settings_to_objects():
    """Copy Settings from Active to Selected Objects"""

    objects = [ob for ob in bpy.data.objects if ob.select_get() and ob.type=='MESH']
    a = bpy.context.active_object
    if not a:
        return 0
    n = 0
    for ob in objects:
        if ob == a:
            continue
        # Copy settings from active object
        ob.shmg_include_in_export = a.shmg_include_in_export
        ob.shmg_include_snapping = a.shmg_include_snapping
        ob.shmg_include_feature_extraction = a.shmg_include_feature_extraction
        ob.shmg_surface_min_level = a.shmg_surface_min_level
        ob.shmg_surface_max_level = a.shmg_surface_max_level
        ob.shmg_feature_edge_level = a.shmg_feature_edge_level
        ob.shmg_surface_layers = a.shmg_surface_layers
        ob.shmg_dict_number = a.shmg_dict_number
        ob.shmg_patch_info_type = a.shmg_patch_info_type
        ob.shmg_face_zone_type = a.shmg_face_zone_type
        ob.shmg_cell_zone_type = a.shmg_cell_zone_type
        ob.shmg_volume_level = a.shmg_volume_level
        ob.shmg_volume_type = a.shmg_volume_type
        ob.shmg_specify_object_layer_properties = a.shmg_specify_object_layer_properties
        ob.shmg_obj_surface_layer_expansion_ratio = a.shmg_obj_surface_layer_expansion_ratio
        ob.shmg_obj_surface_layer_final_thickness = a.shmg_obj_surface_layer_final_thickness
        ob.shmg_obj_surface_layer_minimum_thickness = a.shmg_obj_surface_layer_minimum_thickness
        n += 1
    return n
