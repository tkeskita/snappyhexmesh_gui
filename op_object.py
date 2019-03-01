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
# Object related functionality
from .op_gen import *

# ----------------------------------------------------------------------------

def get_object_bbox_coords(obj):
    """Returns two vectors which contain the minimum and maximum coordinates
    for bounding box for object obj
    """

    # Acknowledgement: Here is nice explanation of obj.bound_box and example
    # for using Blender's bounding box data in python by zeffii:
    # https://blender.stackexchange.com/questions/32283/what-are-all-values-in-bound-box

    worldify = lambda p: obj.matrix_world @ mathutils.Vector(p[:])
    coords = [worldify(p).to_tuple() for p in obj.bound_box[:]]
    rotated = list(zip(*coords[::]))
    min_bbox = [min(c) for c in rotated]
    max_bbox = [max(c) for c in rotated]

    return min_bbox, max_bbox
