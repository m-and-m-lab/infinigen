#!/usr/bin/env python3
"""
This script:
  • Loads a USD file and finds the prim at a user‐specified path.
  • Exports that prim’s subtree (all child mesh prims) to a temporary USD file.
  • Converts the filtered USD file to an OBJ file using Aspose.3D.
  • Loads the OBJ using trimesh and sets up a pyrender scene.
  • Places a camera (via pyrender’s offscreen renderer) determined automatically from the mesh bounding box.
  • Renders the scene offscreen and saves the resulting image.

Dependencies: trimesh, pyrender, imageio, and Pixar's USD Python modules.
"""

import argparse
import sys

import imageio
import numpy as np
import pyrender
import trimesh
from pxr import Gf, Usd, UsdGeom


def look_at(eye, target, up=np.array([0, 0, 1])):
    """
    Computes a 4x4 camera-to-world transformation matrix.
    The camera is placed at 'eye', looks toward 'target', with 'up' defining the vertical direction.
    This formulation sets the camera's local -z axis as the view direction.
    """
    forward = target - eye
    forward /= np.linalg.norm(forward)

    right = np.cross(forward, up)
    right /= np.linalg.norm(right)

    true_up = np.cross(right, forward)

    # Build rotation matrix with columns: right, true_up, and -forward
    mat = np.eye(4)
    mat[0, :3] = right
    mat[1, :3] = true_up
    mat[2, :3] = -forward
    mat[:3, 3] = eye
    return mat


def compute_camera_transform(mesh, fov=np.radians(60)):
    """
    Computes a camera-to-world transformation matrix that frames the mesh.
    - Uses the mesh's oriented bounding box center.
    - Uses the maximum dimension of the bounding box as the size.
    - Computes a distance such that the object fits in the view,
      using d = (max_extent/2) / tan(FOV/2).
    - Positions the camera along the negative Y axis.
    """
    bbox = mesh.bounding_box_oriented
    center = bbox.centroid
    extents = bbox.extents
    max_extent = np.max(extents)

    # Compute the distance so that the full object fits in the field-of-view.
    distance = (max_extent / 2.0) / np.tan(fov / 2.0)

    # Position the camera.
    # Here we place the camera along the negative Y axis.
    eye = center + np.array([0, -distance, 0])

    # Choose an up vector; many USD assets use Z as up.
    up = np.array([0, 0, 1])

    return look_at(eye, center, up)


def export_prim_and_children(src_prim, dst_stage):
    """
    Recursively copy the source prim and all its children into the destination stage.

    Parameters:
      src_prim (Usd.Prim): The source prim to copy.
      dst_stage (Usd.Stage): The destination stage where the prim will be copied.

    Returns:
      dst_prim (Usd.Prim): The defined prim in dst_stage corresponding to src_prim.
    """
    # Define the prim in the destination stage at the same path and type name.
    dst_prim = dst_stage.DefinePrim(src_prim.GetPath(), src_prim.GetTypeName())

    # Copy all valid authored attributes.
    for attr in src_prim.GetAttributes():
        if attr.IsAuthored():
            dst_attr = dst_prim.CreateAttribute(attr.GetName(), attr.GetTypeName())
            dst_attr.Set(attr.Get())

    # Recursively process children.
    for child in src_prim.GetChildren():
        export_prim_and_children(child, dst_stage)

    return dst_prim


def export_subtree_to_usd(src_usd_file, prim_path, dst_usd_file):
    """
    Opens the source USD, retrieves the prim at prim_path,
    copies its subtree into a new USD stage, and exports the resulting layer.

    Parameters:
      src_usd_file (str): The file path to the source USD file.
      prim_path (str): The USD prim path of the subtree to export.
      dst_usd_file (str): The file path where the new USD file will be saved.
    """
    # Load the source USD stage.
    src_stage = Usd.Stage.Open(src_usd_file)
    if not src_stage:
        print(f"Failed to open USD file: {src_usd_file}")
        sys.exit(1)

    # Get the prim at the specified path.
    target_prim = src_stage.GetPrimAtPath(prim_path)
    if not target_prim or not target_prim.IsValid():
        print(f"Invalid prim or prim not found at: {prim_path}")
        sys.exit(1)

    # Create a new stage for exporting.
    dst_stage = Usd.Stage.CreateNew(dst_usd_file)

    # Recursively copy the target prim and its children.
    export_prim_and_children(target_prim, dst_stage)

    # Save the new stage by exporting its root layer.
    dst_stage.GetRootLayer().Export(dst_usd_file)
    print(f"Exported prim subtree from {prim_path} to {dst_usd_file}")


def convert_usd_to_obj(usd_file, prim_path, output_obj):
    # Open the USDA file
    stage = Usd.Stage.Open(usd_file)
    if not stage:
        print(f"Error: Could not open USD file '{usd_file}'")
        sys.exit(1)

    # Retrieve the target prim by its path
    target_prim = stage.GetPrimAtPath(prim_path)
    if not target_prim or not target_prim.IsValid():
        print(f"Error: No valid prim found at '{prim_path}'")
        sys.exit(1)

    # Collect all mesh prims under the target prim
    mesh_prims = [prim for prim in Usd.PrimRange(target_prim) if prim.IsA(UsdGeom.Mesh)]
    if not mesh_prims:
        print("No mesh prims found under the given prim path.")
        sys.exit(1)

    # Create a transform cache to obtain world-space transforms for each mesh
    xformCache = UsdGeom.XformCache(0)

    vertex_offset = 0  # Keeps track of the vertex index offset for OBJ indexing
    with open(output_obj, "w") as out:
        out.write("# OBJ file generated from USD file: {}\n".format(usd_file))
        for mesh in mesh_prims:
            mesh_schema = UsdGeom.Mesh(mesh)
            mesh_name = mesh.GetName()
            out.write("o {}\n".format(mesh_name))

            # Get the world transform for the mesh, so the vertices are in global space.
            transform = xformCache.GetLocalToWorldTransform(mesh)

            # Extract the mesh points and apply the transform.
            points = mesh_schema.GetPointsAttr().Get()
            transformed_points = [transform.Transform(Gf.Vec3f(*p)) for p in points]
            for pt in transformed_points:
                out.write("v {} {} {}\n".format(pt[0], pt[1], pt[2]))

            # Extract face vertex indices and the counts (number of vertices per face)
            face_indices = mesh_schema.GetFaceVertexIndicesAttr().Get()
            face_counts = mesh_schema.GetFaceVertexCountsAttr().Get()

            index = 0
            for count in face_counts:
                face = face_indices[index : index + count]
                # Convert indices for OBJ (1-indexed and adjusted by vertex_offset)
                face_adjusted = [str(i + 1 + vertex_offset) for i in face]
                out.write("f " + " ".join(face_adjusted) + "\n")
                index += count

            vertex_offset += len(points)

    print("Successfully wrote OBJ file to '{}'".format(output_obj))


def load_obj_into_trimesh(obj_file):
    """
    Load the OBJ file using trimesh. If the OBJ file contains multiple objects,
    they are concatenated into a single mesh.
    """
    mesh_data = trimesh.load(obj_file, force="scene")
    if isinstance(mesh_data, trimesh.Scene):
        # Concatenate all geometries from the scene into one mesh.
        meshes = [geom for geom in mesh_data.geometry.values()]
        if not meshes:
            print("No meshes found in the OBJ file.")
            sys.exit(1)
        mesh = trimesh.util.concatenate(meshes)
    else:
        mesh = mesh_data
    return mesh


def render_mesh_offscreen(
    mesh, output_image, width=640, height=480, fov=np.radians(60)
):
    """
    Renders the provided mesh offscreen using pyrender.

    The camera pose is computed programmatically to ensure the mesh fits the frame.
    """
    # Create a pyrender mesh from the trimesh object.
    p_mesh = pyrender.Mesh.from_trimesh(mesh)
    scene = pyrender.Scene()
    scene.add(p_mesh)

    # Compute a camera pose that frames the mesh.
    camera_pose = compute_camera_transform(mesh, fov)

    # Create a perspective camera using the specified field-of-view.
    camera = pyrender.PerspectiveCamera(yfov=fov, znear=0.05, zfar=1000.0)
    scene.add(camera, pose=camera_pose)

    # Add a directional light at the same location as the camera for basic illumination.
    light = pyrender.DirectionalLight(color=np.ones(3), intensity=3.0)
    scene.add(light, pose=camera_pose)

    # Render the scene offscreen.
    renderer = pyrender.OffscreenRenderer(viewport_width=width, viewport_height=height)
    color, _ = renderer.render(scene)
    renderer.delete()

    # Save the rendered image.
    imageio.imwrite(output_image, color)
    print("Saved render image to:", output_image)


def main():
    parser = argparse.ArgumentParser(
        description="Convert a specified object from a USD file to OBJ and render an image without using IsaacSim"
    )
    parser.add_argument(
        "--usd_file", required=True, help="Path to the USD file to load."
    )
    parser.add_argument(
        "--object_path",
        required=True,
        help="Prim path for the target object (e.g., /World/SingleCabinetFactory_2243540__spawn_asset_3512580_).",
    )
    parser.add_argument(
        "--temp_usd",
        default="temp_filtered.usda",
        help="Path to the temporary exported USD file.",
    )
    parser.add_argument(
        "--output_obj",
        default="output.obj",
        help="Path where the OBJ file will be saved.",
    )
    parser.add_argument(
        "--output_image",
        default="capture.png",
        help="Path for the final rendered image.",
    )
    args = parser.parse_args()

    # Step 1: Filter the USD file to only include the subtree below the specified object prim.
    export_subtree_to_usd(args.usd_file, args.object_path, args.temp_usd)

    # Step 2: Convert the filtered USD to OBJ using Aspose.3D.
    convert_usd_to_obj(args.temp_usd, args.object_path, args.output_obj)

    # Step 3: Load the OBJ into a trimesh object.
    mesh = load_obj_into_trimesh(args.output_obj)

    # Step 4: Render the mesh offscreen and save the resulting image.
    render_mesh_offscreen(mesh, args.output_image)


if __name__ == "__main__":
    main()
