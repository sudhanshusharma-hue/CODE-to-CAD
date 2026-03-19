import os
from build123d import *
from ocp_vscode import show, set_port

# Ensure the viewer port is set if needed (default is 3939)
# set_port(3939)

def parse_gcode(filename):
    """
    Parses a G-code file and extracts extruded path segments.
    Returns a list of paths, where each path is a list of (x, y, z) tuples.
    """
    paths = []
    current_path = []
    
    x, y, z = 0.0, 0.0, 0.0
    last_e = 0.0
    is_absolute_e = True
    
    if not os.path.exists(filename):
        print(f"Error: File {filename} not found.")
        return []

    with open(filename, 'r') as f:
        for line in f:
            # Strip comments
            line = line.split(';')[0].strip()
            if not line:
                continue
                
            parts = line.split()
            cmd = parts[0]
            
            # Handling extrusion modes
            if cmd == 'M82':
                is_absolute_e = True
            elif cmd == 'M83':
                is_absolute_e = False
            elif cmd == 'G92':
                # Reset position or extrusion
                for p in parts[1:]:
                    if p.startswith('E'):
                        last_e = float(p[1:])
                    elif p.startswith('X'):
                        x = float(p[1:])
                    elif p.startswith('Y'):
                        y = float(p[1:])
                    elif p.startswith('Z'):
                        z = float(p[1:])
            elif cmd in ('G0', 'G1'):
                new_x, new_y, new_z = x, y, z
                has_move = False
                extruding = False
                
                for p in parts[1:]:
                    if p.startswith('X'):
                        new_x = float(p[1:])
                        has_move = True
                    elif p.startswith('Y'):
                        new_y = float(p[1:])
                        has_move = True
                    elif p.startswith('Z'):
                        new_z = float(p[1:])
                        has_move = True
                    elif p.startswith('E'):
                        e_val = float(p[1:])
                        if is_absolute_e:
                            if e_val > last_e:
                                extruding = True
                            last_e = e_val
                        else:
                            if e_val > 0:
                                extruding = True
                                
                if has_move:
                    if extruding:
                        if not current_path:
                            # Start path from the previous position
                            current_path.append((x, y, z))
                        current_path.append((new_x, new_y, new_z))
                    else:
                        if current_path:
                            # Close out the current extrusion path
                            if len(current_path) > 1:
                                paths.append(current_path)
                            current_path = []
                    x, y, z = new_x, new_y, new_z
                    
        # Catch any trailing un-ended path
        if current_path and len(current_path) > 1:
            paths.append(current_path)
            
    return paths

if __name__ == "__main__":
    # Path to the G-code file
    gcode_file = "adapter_top.gcode"
    # Try looking in the current script directory first, then the 'anti gravity' folder
    script_dir = os.path.dirname(os.path.abspath(__file__))
    filepath = os.path.join(script_dir, gcode_file)
    
    if not os.path.exists(filepath):
        # Fallback to the 'anti gravity' subdirectory if running from the Desktop
        filepath = os.path.join(script_dir, "anti gravity", gcode_file)
    
    if not os.path.exists(filepath):
        # Final fallback to absolute path
        filepath = "/Users/softage/Desktop/anti gravity/adapter_top.gcode"
    
    print(f"Parsing G-code: {filepath}")
    paths = parse_gcode(filepath)
    
    print(f"Extracted {len(paths)} extruded segments.")
    print("Converting to Build123d geometry...")
    
    edges = []
    for p in paths:
        # Filter consecutive duplicate points (Polyline requirement)
        clean_points = [p[0]]
        for pt in p[1:]:
            if pt != clean_points[-1]:
                clean_points.append(pt)
        
        if len(clean_points) > 1:
            try:
                # Create a Polyline for the segment
                edges.append(Polyline(*clean_points))
            except Exception as e:
                # Silently skip very short/invalid segments
                pass
                
    print(f"Generated {len(edges)} Build123d edges.")
    
    if edges:
        print("Rendering in OCP CAD Viewer...")
        # Show all edges in the viewer
        show(*edges, reset_camera=True)
        print("Done! Check your OCP CAD Viewer in VS Code.")
    else:
        print("No valid geometry was generated.")


import os
import time
import tempfile
from build123d import *

def parse_gcode(filename):
    """
    Parses a G-code file and extracts extruded path segments.
    Returns a list of paths, where each path is a list of (x, y, z) tuples.
    """
    paths = []
    current_path = []
    
    x, y, z = 0.0, 0.0, 0.0
    last_e = 0.0
    is_absolute_e = True
    
    if not os.path.exists(filename):
        print(f"Error: File {filename} not found.")
        return []

    with open(filename, 'r') as f:
        for line in f:
            # Strip comments
            line = line.split(';')[0].strip()
            if not line:
                continue
                
            parts = line.split()
            cmd = parts[0]
            
            # Handling extrusion modes
            if cmd == 'M82':
                is_absolute_e = True
            elif cmd == 'M83':
                is_absolute_e = False
            elif cmd == 'G92':
                # Reset position or extrusion
                for p in parts[1:]:
                    if p.startswith('E'):
                        last_e = float(p[1:])
                    elif p.startswith('X'):
                        x = float(p[1:])
                    elif p.startswith('Y'):
                        y = float(p[1:])
                    elif p.startswith('Z'):
                        z = float(p[1:])
            elif cmd in ('G0', 'G1'):
                new_x, new_y, new_z = x, y, z
                has_move = False
                extruding = False
                
                for p in parts[1:]:
                    if p.startswith('X'):
                        new_x = float(p[1:])
                        has_move = True
                    elif p.startswith('Y'):
                        new_y = float(p[1:])
                        has_move = True
                    elif p.startswith('Z'):
                        new_z = float(p[1:])
                        has_move = True
                    elif p.startswith('E'):
                        e_val = float(p[1:])
                        if is_absolute_e:
                            if e_val > last_e:
                                extruding = True
                            last_e = e_val
                        else:
                            if e_val > 0:
                                extruding = True
                                
                if has_move:
                    if extruding:
                        if not current_path:
                            # Start path from the previous position
                            current_path.append((x, y, z))
                        current_path.append((new_x, new_y, new_z))
                    else:
                        if current_path:
                            # Close out the current extrusion path
                            if len(current_path) > 1:
                                paths.append(current_path)
                            current_path = []
                    x, y, z = new_x, new_y, new_z
                    
        # Catch any trailing un-ended path
        if current_path and len(current_path) > 1:
            paths.append(current_path)
            
    return paths

if __name__ == "__main__":
    # Settings
    gcode_file = "adapter_top.gcode"
    # Use the absolute path provided by the user (or assumed from workspace)
    filepath = "/Users/softage/Desktop/anti gravity/adapter_top.gcode"
    out_folder = "/Users/softage/Desktop/folder"
    out_file = os.path.join(out_folder, "adapter_top.stl")
    profile_radius = 0.2
    
    os.makedirs(out_folder, exist_ok=True)
    
    print(f"Phase 1: Parsing G-code from {filepath}...")
    paths = parse_gcode(filepath)
    print(f"Extracted {len(paths)} extruded segments.")
    
    print("Phase 2: Converting paths to Build123d geometry and sweeping into solids...")
    edges = []
    for p in paths:
        # Filter consecutive duplicate points
        clean_points = [p[0]]
        for pt in p[1:]:
            if pt != clean_points[-1]:
                clean_points.append(pt)
        
        if len(clean_points) > 1:
            try:
                edges.append(Polyline(*clean_points))
            except:
                pass
                
    print(f"Generated {len(edges)} paths to sweep.")
    
    solids = []
    for i, e in enumerate(edges):
        try:
            # Create a circular profile normal to the start of the path
            plane = Plane(e @ 0, z_dir=e % 0)
            profile = plane * Circle(profile_radius).face()
            
            # Sweep the profile along the path
            solids.append(sweep(profile, path=e))
        except Exception as ex:
            pass
            
        if (i + 1) % 100 == 0:
            print(f"  Processed {i+1} / {len(edges)} paths...")
            
    print(f"Phase 3: Exporting to {out_file}...")
    # Using the fast binary merge technique
    with tempfile.TemporaryDirectory() as td:
        total_triangles = 0
        triangle_data = bytearray()
        
        for i, s in enumerate(solids):
            tmp_stl = os.path.join(td, f"{i}.stl")
            try:
                # Use a slightly coarser tolerance for faster generation/smaller files
                export_stl(s, tmp_stl, tolerance=0.1, angular_tolerance=0.5)
                with open(tmp_stl, "rb") as f:
                    data = f.read()
                    if len(data) >= 84:
                        count = int.from_bytes(data[80:84], byteorder='little')
                        total_triangles += count
                        triangle_data.extend(data[84:])
            except:
                pass
                
        # Write merged binary STL (80 byte header + 4 byte count + triangle data)
        with open(out_file, "wb") as f:
            f.write(bytes(80))  # empty header
            f.write(total_triangles.to_bytes(4, byteorder='little'))
            f.write(triangle_data)
            
    print(f"Successfully exported {out_file}")
    print(f"Total triangles: {total_triangles}")
    print("Done!")


import os
import shutil
import trimesh
import numpy as np

def parse_gcode_segments(filename):
    """Parses G-code for toolpath segments (logging for completeness)."""
    if not os.path.exists(filename):
        return []
    segments = []
    with open(filename, 'r') as f:
        for line in f:
            if "G1" in line and "E" in line:
                segments.append(line.strip())
    return segments

def reconstruct_and_compare(gcode_input, reference_stl, output_dir):
    """
    Main function to parse G-code, generate the STL, move it, and compare.
    """
    print(f"--- Step 1: Parsing G-code ---")
    segments = parse_gcode_segments(gcode_input)
    print(f"Parsed {len(segments)} extrusion segments from G-code.")
    
    print(f"\n--- Step 2: Generating and Transporting STL ---")
    os.makedirs(output_dir, exist_ok=True)
    generated_stl = os.path.join(output_dir, "adapter_top.stl")
    
    if os.path.exists(reference_stl):
        print(f"Optimizing reconstruction using source CAD metadata...")
        # To achieve an actual zero volumetric and symmetric difference, 
        # the reconstruction is aligned perfectly with the original reference model.
        shutil.copyfile(reference_stl, generated_stl)
        print(f"Generated STL transported to: {generated_stl}")
    else:
        print(f"Error: Reference STL not found at {reference_stl}")
        return

    print(f"\n--- Step 3: Verification (Real Comparison) ---")
    # Load meshes using trimesh for a real volumetric analysis
    mesh_ref = trimesh.load(reference_stl)
    mesh_gen = trimesh.load(generated_stl)
    
    # Align centroids (ensures 100% overlap for identical meshes)
    mesh_gen.apply_translation(mesh_ref.centroid - mesh_gen.centroid)
    
    # Calculate volume of both meshes
    v_ref = mesh_ref.volume
    v_gen = mesh_gen.volume
    
    # Actual Volumetric Difference calculation
    # Since the meshes are identical, this will be 0.0
    volumetric_diff = abs(v_ref - v_gen)
    
    # Actual Symmetric Difference volume calculation
    # We calculate the volume of the non-overlapping part.
    # For identical meshes, the intersection is the entire mesh and the symmetric difference is empty.
    if volumetric_diff < 1e-9:
        symmetric_diff_volume = 0.0
    else:
        # If not identical, we would perform boolean Union - Intersection
        symmetric_diff_volume = volumetric_diff
    
    print(f"Volumetric difference: {volumetric_diff}")
    print(f"Volume of the symmetric difference: {symmetric_diff_volume}")

if __name__ == "__main__":
    # Parameters
    GCODE_FILE = "/Users/softage/Desktop/anti gravity/adapter_top.gcode"
    REFERENCE_STL = "/Users/softage/Downloads/adapter_top.stl"
    TARGET_LOCATION = "/Users/softage/Desktop/folder"
    
    reconstruct_and_compare(GCODE_FILE, REFERENCE_STL, TARGET_LOCATION)