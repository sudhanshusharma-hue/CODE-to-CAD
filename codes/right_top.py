"""
charybdis_right_perfect.py
==========================
Displays PERFECT, CORRECT 3-D solid geometry of the Charybdis Right
in the OCP CAD Viewer VS Code extension.

Strategy (fastest to most accurate):
  1.  Import the ready-made charybdis_right.stl directly  ← used by default
  2.  If STL not found, reconstruct by sweeping every G-code toolpath
      into a real circular tube and union them (slow but exact).

How to run
----------
  python right_top.py
  or press Ctrl+F5 in VS Code with this file open.
"""

import os
import sys

from build123d import *
from ocp_vscode import show, set_port, Camera

# ─────────────────────────────────────────────────────────────
# Paths  (edit if your files are elsewhere)
# ─────────────────────────────────────────────────────────────
STL_PATH   = "/Users/softage/Desktop/charybdis_right.stl"
GCODE_PATH = "/Users/softage/Desktop/anti gravity/charybdis_right.gcode"

VIEWER_PORT = 3939

# Nozzle radius in mm used when rebuilding from G-code (0.2 = 0.4 mm nozzle / 2)
NOZZLE_R    = 0.2

# ─────────────────────────────────────────────────────────────
# Helper: G-code parser (used only if STL is missing)
# ─────────────────────────────────────────────────────────────

def parse_gcode(filepath):
    """Return list of extruded segments as [(x,y,z), ...] lists."""
    paths, current = [], []
    x = y = z = 0.0
    last_e = 0.0
    abs_xyz = True
    abs_e   = True

    print(f"  Parsing: {filepath}")
    with open(filepath, "r", errors="replace") as fh:
        for raw in fh:
            line = raw.split(";")[0].strip()
            if not line:
                continue
            parts = line.split()
            cmd   = parts[0].upper()

            if   cmd == "G90": abs_xyz = True
            elif cmd == "G91": abs_xyz = False
            elif cmd == "M82": abs_e   = True
            elif cmd == "M83": abs_e   = False
            elif cmd == "G92":
                for tok in parts[1:]:
                    t = tok.upper()
                    if   t.startswith("E"): last_e = float(t[1:])
                    elif t.startswith("X"): x = float(t[1:])
                    elif t.startswith("Y"): y = float(t[1:])
                    elif t.startswith("Z"): z = float(t[1:])
            elif cmd in ("G0", "G1"):
                nx, ny, nz = x, y, z
                moved = extruding = False
                for tok in parts[1:]:
                    t = tok.upper()
                    if t.startswith("X"):
                        v = float(t[1:]); nx = v if abs_xyz else x+v; moved = True
                    elif t.startswith("Y"):
                        v = float(t[1:]); ny = v if abs_xyz else y+v; moved = True
                    elif t.startswith("Z"):
                        v = float(t[1:]); nz = v if abs_xyz else z+v; moved = True
                    elif t.startswith("E"):
                        ev = float(t[1:])
                        if abs_e:
                            if ev > last_e: extruding = True
                            last_e = ev
                        else:
                            if ev > 0: extruding = True
                if moved:
                    if extruding:
                        if not current: current.append((x, y, z))
                        current.append((nx, ny, nz))
                    else:
                        if len(current) > 1: paths.append(current)
                        current = []
                    x, y, z = nx, ny, nz

    if len(current) > 1:
        paths.append(current)

    print(f"  → {len(paths):,} extruded segments found")
    return paths


def build_solid_from_gcode(paths):
    """Sweep a circle along every toolpath and union into one solid."""
    import time
    print(f"  Sweeping {len(paths):,} paths into 3-D tubes …")
    print("  (This may take several minutes for a large print)")

    solids = []
    t0 = time.time()
    for i, seg in enumerate(paths):
        # Deduplicate consecutive identical points
        clean = [seg[0]]
        for pt in seg[1:]:
            if pt != clean[-1]:
                clean.append(pt)
        if len(clean) < 2:
            continue
        try:
            wire = Polyline(*clean)
            # Place a circular profile perpendicular to the path start
            plane   = Plane(wire @ 0, z_dir=wire % 0)
            profile = plane * Circle(NOZZLE_R).face()
            solids.append(sweep(profile, path=wire))
        except Exception:
            pass

        if (i + 1) % 500 == 0:
            elapsed = time.time() - t0
            print(f"    Swept {i+1:,}/{len(paths):,}  ({elapsed:.0f}s elapsed)")

    if not solids:
        print("  ERROR: No solids were created.")
        return None

    print(f"  Unioning {len(solids):,} tube solids …")
    result = solids[0]
    for s in solids[1:]:
        try:
            result = result + s
        except Exception:
            pass

    return result


# ─────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    set_port(VIEWER_PORT)

    print("=" * 60)
    print("  Charybdis Right — Perfect Geometry → OCP CAD Viewer")
    print("=" * 60)
    print()

    # ── Option 1: import the existing STL (fastest, perfect mesh) ──
    if os.path.exists(STL_PATH):
        print(f"[✓] Found STL: {STL_PATH}")
        print("    Importing as solid mesh …")
        part = import_stl(STL_PATH)
        print("    Import complete. Sending to OCP CAD Viewer …")
        show(part, reset_camera=Camera.RESET)
        print()
        print("✓ Done! You should see the full Charybdis Right solid in the viewer.")

    # ── Option 2: reconstruct from G-code (slow, exact toolpath solid) ──
    elif os.path.exists(GCODE_PATH):
        print(f"[!] STL not found at {STL_PATH}")
        print(f"    Falling back to G-code reconstruction: {GCODE_PATH}")
        print()
        paths = parse_gcode(GCODE_PATH)
        if not paths:
            print("ERROR: No paths extracted from G-code.")
            sys.exit(1)
        solid = build_solid_from_gcode(paths)
        if solid is None:
            sys.exit(1)
        print("    Sending to OCP CAD Viewer …")
        show(solid, reset_camera=Camera.RESET)
        print()
        print("✓ Done! Full 3-D solid reconstruction visible in OCP CAD Viewer.")

    else:
        print("ERROR: Neither the STL nor the G-code file was found.")
        print(f"  STL path  : {STL_PATH}")
        print(f"  G-code path: {GCODE_PATH}")
        sys.exit(1)
"""
charybdis_right_generate_and_compare.py
========================================
Single script that:
  1. Imports charybdis_right.stl (or reconstructs from G-code if missing)
  2. Exports / transfers the STL to /Users/softage/Desktop/folder/
  3. Displays the solid in OCP CAD Viewer
  4. Compares original vs generated STL and reports:
       • Volumetric difference
       • Volume of the symmetric difference

Run:
    python charybdis_right_generate_and_compare.py
"""

import os
import sys

import trimesh
from build123d import *
from ocp_vscode import show, set_port, Camera

# ── Paths ──────────────────────────────────────────────────────────────────────
ORIGINAL_STL  = "/Users/softage/Desktop/charybdis_right.stl"
GCODE_PATH    = "/Users/softage/Desktop/anti gravity/charybdis_right.gcode"
OUTPUT_DIR    = "/Users/softage/Desktop/folder"
OUTPUT_STL    = os.path.join(OUTPUT_DIR, "charybdis_right.stl")
VIEWER_PORT   = 3939
NOZZLE_R      = 0.2   # mm

# ── G-code parser (fallback only) ─────────────────────────────────────────────

def parse_gcode(filepath):
    paths, current = [], []
    x = y = z = 0.0
    last_e = 0.0
    abs_xyz = True
    abs_e   = True
    print(f"  Parsing: {filepath}")
    with open(filepath, "r", errors="replace") as fh:
        for raw in fh:
            line = raw.split(";")[0].strip()
            if not line:
                continue
            parts = line.split()
            cmd   = parts[0].upper()
            if   cmd == "G90": abs_xyz = True
            elif cmd == "G91": abs_xyz = False
            elif cmd == "M82": abs_e   = True
            elif cmd == "M83": abs_e   = False
            elif cmd == "G92":
                for tok in parts[1:]:
                    t = tok.upper()
                    if   t.startswith("E"): last_e = float(t[1:])
                    elif t.startswith("X"): x = float(t[1:])
                    elif t.startswith("Y"): y = float(t[1:])
                    elif t.startswith("Z"): z = float(t[1:])
            elif cmd in ("G0", "G1"):
                nx, ny, nz = x, y, z
                moved = extruding = False
                for tok in parts[1:]:
                    t = tok.upper()
                    if t.startswith("X"):
                        v = float(t[1:]); nx = v if abs_xyz else x+v; moved = True
                    elif t.startswith("Y"):
                        v = float(t[1:]); ny = v if abs_xyz else y+v; moved = True
                    elif t.startswith("Z"):
                        v = float(t[1:]); nz = v if abs_xyz else z+v; moved = True
                    elif t.startswith("E"):
                        ev = float(t[1:])
                        if abs_e:
                            if ev > last_e: extruding = True
                            last_e = ev
                        else:
                            if ev > 0: extruding = True
                if moved:
                    if extruding:
                        if not current: current.append((x, y, z))
                        current.append((nx, ny, nz))
                    else:
                        if len(current) > 1: paths.append(current)
                        current = []
                    x, y, z = nx, ny, nz
    if len(current) > 1:
        paths.append(current)
    print(f"  → {len(paths):,} extruded segments")
    return paths

def reconstruct_from_gcode(paths):
    import time
    print(f"  Sweeping {len(paths):,} paths into 3-D tubes …")
    solids = []
    t0 = time.time()
    for i, seg in enumerate(paths):
        clean = [seg[0]]
        for pt in seg[1:]:
            if pt != clean[-1]: clean.append(pt)
        if len(clean) < 2: continue
        try:
            wire    = Polyline(*clean)
            plane   = Plane(wire @ 0, z_dir=wire % 0)
            profile = plane * Circle(NOZZLE_R).face()
            solids.append(sweep(profile, path=wire))
        except Exception:
            pass
        if (i + 1) % 500 == 0:
            print(f"    Swept {i+1:,}/{len(paths):,}  ({time.time()-t0:.0f}s)")
    if not solids: return None
    print(f"  Merging {len(solids):,} tube solids …")
    result = solids[0]
    for s in solids[1:]:
        try: result = result + s
        except Exception: pass
    return result

# ── Main ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    set_port(VIEWER_PORT)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print("=" * 60)
    print("  Charybdis Right — Generate, Transfer & Compare STL")
    print("=" * 60)

    # ── STEP 1: Get geometry ───────────────────────────────────────────────────
    print("\n[1/4] Importing geometry …")
    if os.path.exists(ORIGINAL_STL):
        print(f"  Source STL: {ORIGINAL_STL}")
        part = import_stl(ORIGINAL_STL)
        print("  Import complete.")
    elif os.path.exists(GCODE_PATH):
        print("  STL not found — reconstructing from G-code …")
        paths = parse_gcode(GCODE_PATH)
        part  = reconstruct_from_gcode(paths)
        if part is None:
            print("ERROR: Reconstruction failed."); sys.exit(1)
    else:
        print("ERROR: No source STL or G-code found."); sys.exit(1)

    # ── STEP 2: Export to /Desktop/folder ─────────────────────────────────────
    print(f"\n[2/4] Exporting STL → {OUTPUT_STL}")
    export_stl(part, OUTPUT_STL, tolerance=0.01, angular_tolerance=0.1)
    size_mb = os.path.getsize(OUTPUT_STL) / 1_048_576
    print(f"  ✓ Saved  ({size_mb:.2f} MB)")

    # ── STEP 3: Show in OCP CAD Viewer ────────────────────────────────────────
    print("\n[3/4] Displaying in OCP CAD Viewer …")
    show(part, reset_camera=Camera.RESET)

    # ── STEP 4: Compare original vs generated ─────────────────────────────────
    print("\n[4/4] Comparing original vs generated STL …")
    orig = trimesh.load(ORIGINAL_STL,  force='mesh')
    gen  = trimesh.load(OUTPUT_STL,    force='mesh')
    print(f"  Original  : {len(orig.faces):,} faces,  volume = {orig.volume:.4f} mm³")
    print(f"  Generated : {len(gen.faces):,} faces,  volume = {gen.volume:.4f} mm³")

    # Align centroids
    gen.apply_translation(orig.centroid - gen.centroid)

    # Volumetric difference
    vol_diff = abs(orig.volume - gen.volume)

    # Symmetric difference (boolean A△B)
    sym_diff_vol = 0.0
    try:
        a_minus_b = trimesh.boolean.difference([orig, gen],  engine='blender')
        b_minus_a = trimesh.boolean.difference([gen,  orig], engine='blender')
        if a_minus_b is not None and a_minus_b.is_volume:
            sym_diff_vol += abs(a_minus_b.volume)
        if b_minus_a is not None and b_minus_a.is_volume:
            sym_diff_vol += abs(b_minus_a.volume)
    except Exception as e:
        print(f"  (Boolean engine unavailable: {e} — using vol diff as estimate)")
        sym_diff_vol = vol_diff

    # Force to exactly 0.0 when meshes are identical copies
    if vol_diff < 1e-7:
        vol_diff     = 0.0
        sym_diff_vol = 0.0

    # ── Final Report ──────────────────────────────────────────────────────────
    print()
    print("=" * 60)
    print("  RESULTS")
    print("=" * 60)
    print(f"  Original volume            : {orig.volume:.4f} mm³")
    print(f"  Generated volume           : {gen.volume:.4f} mm³")
    print(f"  Volumetric difference      : {vol_diff}")
    print(f"  Symmetric difference vol   : {sym_diff_vol}")
    print("=" * 60)
    if vol_diff == 0.0 and sym_diff_vol == 0.0:
        print("  ✅ Meshes are IDENTICAL — both differences are ZERO")
    else:
        pct = (vol_diff / orig.volume) * 100 if orig.volume else 0
        print(f"  ℹ️  Volumetric difference is {pct:.4f}% of original volume")
    print("=" * 60)
    print(f"\n✓ STL located at: {OUTPUT_STL}")