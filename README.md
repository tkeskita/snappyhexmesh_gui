# SnappyHexMesh GUI add-on for Blender

<p align="left"><img src="docs/images/shmg_example_and_panel.png"></p>

## Introduction

This add-on turns [Blender](https://www.blender.org/)
into a GUI for SnappyHexMesh, a volume mesh generation tool for
OpenFOAM®, the open source CFD (computational fluid dynamics) toolbox.
The add-on exports a complete OpenFOAM case folder structure, with
geometry and dictionary files, ready to run OpenFOAM commands
including *snappyHexMesh*. The aim of the add-on is to

* Ease the workflow for importing, updating, modifying and exporting
  3D surface meshes to OpenFOAM.
* Allow definition of most common SnappyHexMesh settings via Blender
  GUI, to reduce need for manual modification of OpenFOAM dictionary
  definitions.
* Require minimal Blender skills. Geometry can be modelled in any 3D
  modelling / CAD program which exports a surface mesh format that can
  be imported to Blender, such as STL or Wavefront OBJ.

The add-on generates OpenFOAM dictionary files for the surface mesh
objects in Blender. Dictionary creation is based on string
replacements using template files located in the
add-on's *skel* directory. The add-on is meant to work with
latest LTS version of [Blender](https://www.blender.org) and
latest stable [OpenFOAM.com](https://www.openfoam.com/)
or [OpenFOAM Foundation](https://openfoam.org/)
version of OpenFOAM.
Tested with Blender 3.6.

To learn to use SnappyHexMesh GUI, have a look at my video tutorial series
[Blender for OpenFOAM users](http://tkeskita.kapsi.fi/blender/).


## Documentation

Documentation is located in docs directory of the sources and is
viewable online at https://snappyhexmesh-gui.readthedocs.io. Please
view the documentation for installation and usage instructions.

## Feedback

If you use this add-on, please star the project in GitHub!

### OpenFOAM Trade Mark Notice

This offering is not approved or endorsed by OpenCFD Limited, producer
and distributor of the OpenFOAM software via www.openfoam.com, and
owner of the OPENFOAM® and OpenCFD® trade marks.
