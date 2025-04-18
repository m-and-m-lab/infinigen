#!/usr/bin/env python3
"""
This script:
  • Loads the OBJ using trimesh and sets up a pyrender scene.

Dependencies: trimesh, pyrender
"""

import pyrender
import trimesh

# Load OBJ file
obj_trimesh = trimesh.load("output.obj")
# Generate mes and displayin pyrender scene
mesh = pyrender.Mesh.from_trimesh(obj_trimesh)
scene = pyrender.Scene()
scene.add(mesh)
pyrender.Viewer(scene, use_raymond_lighting=True)
