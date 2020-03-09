# SnappyHexMesh GUI add-on for Blender

## Introduction

SnappyHexMesh is a volume mesh generation tool for OpenFOAM®, the open
source CFD (computational fluid dynamics) toolbox. SnappyHexMesh GUI
add-on for [Blender](https://www.blender.org/)
("the add-on" hereafter) is meant to aid OpenFOAM
users to use Blender as a CFD pre-processing tool. The aim is to

* Ease the workflow for updating, modifying and exporting 3D surface
  meshes to OpenFOAM.
* Allow definition of most common SnappyHexMesh settings via Blender
  GUI, to reduce need for manual writing of OpenFOAM dictionary
  definitions.
* Require minimal Blender skills. Geometry can be modelled in any 3D
  modelling / CAD program which exports a surface mesh format that can
  be imported to Blender, such as STL or Wavefront OBJ. Add-on is
  operated via panels in Blender's GUI.

The creation of OpenFOAM dictionary files is based on string
replacements using template files located in the
add-on's *skel* directory. The add-on is tested with
[Blender 2.82](https://www.blender.org) and
[OpenFOAM Foundation](https://openfoam.org/) version 7 of OpenFOAM.

## Documentation

Documentation (made using [Sphinx](https://www.sphinx-doc.org/en/master/))
is located in docs directory of the sources and is viewable online at
https://snappyhexmesh-gui.readthedocs.io. Please view the documentation for
installation and usage instructions.

### OpenFOAM Trade Mark Notice

This offering is not approved or endorsed by OpenCFD Limited, producer
and distributor of the OpenFOAM software via www.openfoam.com, and
owner of the OPENFOAM® and OpenCFD® trade marks.
