"""
Version 7: Automated Tests for Bharath::ScalePoints SOP

Run using hython:
    hython tests/test_scale_points.py
"""

import sys
import math

def run_tests():
    print("=" * 60)
    print("RUNNING AUTOMATED TESTS: Bharath::ScalePoints C++ SOP")
    print("=" * 60)

    try:
        import hou
    except ImportError:
        print("ERROR: This test script must be executed using 'hython' (Houdini's Python executable).")
        sys.exit(1)

    # 1. Test Node Creation and Operator Registration
    print("[TEST 1/5] Testing Operator Registration & Node Creation...")
    obj = hou.node("/obj")
    geo_node = obj.createNode("geo", "test_geo_container")
    
    scale_node = geo_node.createNode("Bharath::ScalePoints", "scale_test")
    if not scale_node:
        print("FAIL: Bharath::ScalePoints node type could not be instantiated.")
        sys.exit(1)
    print(" PASS: Operator registered and created successfully.")

    # 2. Test Input Geometry Connection
    print("[TEST 2/5] Testing Geometry Input Cooking...")
    box_node = geo_node.createNode("box", "input_box")
    scale_node.setInput(0, box_node)
    
    # Cook
    geo = scale_node.geometry()
    orig_points = box_node.geometry().points()
    assert len(geo.points()) == len(orig_points), "Point count mismatch between input and output!"
    print(f" PASS: Cooked geometry with {len(geo.points())} points.")

    # 3. Test Mathematical Transformation (Scale, Center, Offset)
    print("[TEST 3/5] Testing Math Transformation (Scale & Offset)...")
    scale_factor = (2.0, 3.0, 0.5)
    offset_vec = (10.0, -5.0, 2.0)
    center_vec = (0.0, 0.0, 0.0)

    scale_node.parmTuple("scale").set(scale_factor)
    scale_node.parmTuple("offset").set(offset_vec)
    scale_node.parmTuple("center").set(center_vec)

    # Force recook
    geo = scale_node.geometry()
    for orig_pt, out_pt in zip(orig_points, geo.points()):
        orig_p = orig_pt.position()
        out_p = out_pt.position()
        expected_x = center_vec[0] + (orig_p.x() - center_vec[0]) * scale_factor[0] + offset_vec[0]
        expected_y = center_vec[1] + (orig_p.y() - center_vec[1]) * scale_factor[1] + offset_vec[1]
        expected_z = center_vec[2] + (orig_p.z() - center_vec[2]) * scale_factor[2] + offset_vec[2]

        assert math.isclose(out_p.x(), expected_x, rel_tol=1e-4), f"X mismatch: {out_p.x()} vs {expected_x}"
        assert math.isclose(out_p.y(), expected_y, rel_tol=1e-4), f"Y mismatch: {out_p.y()} vs {expected_y}"
        assert math.isclose(out_p.z(), expected_z, rel_tol=1e-4), f"Z mismatch: {out_p.z()} vs {expected_z}"
    print(" PASS: Mathematical point positions match expected formulas perfectly.")

    # 4. Test Attributes Creation (Cd, N, pscale)
    print("[TEST 4/5] Testing Attribute Generation (Cd, N, pscale)...")
    scale_node.parm("upd_normals").set(1)
    scale_node.parm("upd_color").set(1)
    scale_node.parm("upd_pscale").set(1)
    scale_node.parm("pscale_val").set(1.5)

    geo = scale_node.geometry()
    attrib_names = [a.name() for a in geo.pointAttribs()]
    assert "Cd" in attrib_names, "Missing Cd attribute!"
    assert "N" in attrib_names, "Missing N attribute!"
    assert "pscale" in attrib_names, "Missing pscale attribute!"
    
    # Check that pscale has positive nonzero values
    for pt in geo.points():
        pscale_val = pt.attribValue("pscale")
        assert pscale_val > 0.0, f"Invalid pscale value: {pscale_val}"
    print(" PASS: Attributes Cd, N, and pscale generated and populated successfully.")

    # 5. Test Group Filtering
    print("[TEST 5/5] Testing Point Group Filtering...")
    group_node = geo_node.createNode("groupcreate", "create_group")
    group_node.setInput(0, box_node)
    group_node.parm("groupname").set("top_points")
    group_node.parm("grouptype").set(0) # Points
    group_node.parm("basegroup").set("0-3") # First 4 points only

    scale_node.setInput(0, group_node)
    scale_node.parm("group").set("top_points")
    
    geo = scale_node.geometry()
    input_geo = group_node.geometry()
    for i, (in_pt, out_pt) in enumerate(zip(input_geo.points(), geo.points())):
        if i in [0, 1, 2, 3]:
            # Should be transformed
            assert in_pt.position() != out_pt.position(), f"Point {i} in group was not transformed!"
        else:
            # Should NOT be transformed
            assert math.isclose(in_pt.position().x(), out_pt.position().x(), abs_tol=1e-5)
            assert math.isclose(in_pt.position().y(), out_pt.position().y(), abs_tol=1e-5)
            assert math.isclose(in_pt.position().z(), out_pt.position().z(), abs_tol=1e-5)
    print(" PASS: Group filtering correctly isolates operations to group members.")

    # Cleanup
    geo_node.destroy()
    print("=" * 60)
    print("ALL 5 AUTOMATED TESTS PASSED SUCCESSFULLY! (100% OK)")
    print("=" * 60)

if __name__ == "__main__":
    run_tests()
