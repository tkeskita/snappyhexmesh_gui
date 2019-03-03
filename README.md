# SnappyHexMesh GUI add-on for Blender

## Introduction

SnappyHexMesh is a volume mesh generation tool for OpenFOAM, the open
source CFD (computational fluid dynamics) toolbox. SnappyHexMesh GUI
add-on for Blender ("the add-on" hereafter) is meant to aid OpenFOAM
users to use Blender as a CFD pre-processing tool. The aim is to ease
the export of 3D surface meshes into a SnappyHexMesh case folder, and
to allow definition of most common SnappyHexMesh settings in Blender,
to reduce need for manual writing of OpenFOAM dictionary definitions
for SnappyHexMesh.
The add-on is developed for Blender 2.8 (master branch).

## Current Status

The add-on is currently in development phase.
Currently implemented features include:
* Creation of basic OpenFOAM case structure, including meshes as STL files and
  dictionary files (most importantly snappyHexMeshDict)
* Creation of definition file for hexahedral base mesh with a defined cell size
  (blockMeshDict)
* Calculation of cell count for base mesh
* Definition of surface refinement levels for meshes

## Links

* [blender.org](https://www.blender.org/)
* [openfoam.org](https://openfoam.org/)
* [openfoam.com](https://www.openfoam.com/)
