"""
Version 6: Python / HOM Interface for Bharath::ScalePoints

Provides clean programmatic Python bindings and automation helpers around the C++ SOP.
"""

import hou
from typing import Dict, Any, Optional, Tuple

def create_scale_points_node(
    parent_node: hou.Node,
    node_name: str = "scale_points1",
    scale: Tuple[float, float, float] = (1.0, 1.0, 1.0),
    center: Tuple[float, float, float] = (0.0, 0.0, 0.0),
    offset: Tuple[float, float, float] = (0.0, 0.0, 0.0),
    group: str = ""
) -> hou.SopNode:
    """
    Creates and configures an instance of the C++ Bharath::ScalePoints node.
    """
    node = parent_node.createNode("Bharath::ScalePoints", node_name)
    node.parmTuple("scale").set(scale)
    node.parmTuple("center").set(center)
    node.parmTuple("offset").set(offset)
    if group:
        node.parm("group").set(group)
    return node

def apply_scale_preset(node: hou.SopNode, preset_name: str) -> None:
    """
    Applies common geometric presets to the Bharath::ScalePoints node.
    """
    if node.type().name() != "Bharath::ScalePoints":
        raise TypeError(f"Expected Bharath::ScalePoints node, got {node.type().name()}")

    presets = {
        "flatten_y": {"scale": (1.0, 0.0, 1.0), "offset": (0.0, 0.0, 0.0)},
        "double_size": {"scale": (2.0, 2.0, 2.0), "offset": (0.0, 0.0, 0.0)},
        "half_size": {"scale": (0.5, 0.5, 0.5), "offset": (0.0, 0.0, 0.0)},
        "mirror_x": {"scale": (-1.0, 1.0, 1.0), "offset": (0.0, 0.0, 0.0)},
        "push_up": {"scale": (1.0, 1.0, 1.0), "offset": (0.0, 2.0, 0.0)}
    }

    if preset_name not in presets:
        raise ValueError(f"Unknown preset '{preset_name}'. Options: {list(presets.keys())}")

    cfg = presets[preset_name]
    node.parmTuple("scale").set(cfg["scale"])
    node.parmTuple("offset").set(cfg["offset"])

def get_node_geometry_statistics(node: hou.SopNode) -> Dict[str, Any]:
    """
    Cooks the node and returns high-level geometry statistics via HOM.
    """
    geo = node.geometry()
    if geo is None:
        return {"point_count": 0, "bbox": None, "attributes": []}

    bbox = geo.boundingBox()
    return {
        "point_count": len(geo.points()),
        "primitive_count": len(geo.prims()),
        "bbox_min": (bbox.minvec().x(), bbox.minvec().y(), bbox.minvec().z()),
        "bbox_max": (bbox.maxvec().x(), bbox.maxvec().y(), bbox.maxvec().z()),
        "bbox_center": (bbox.center().x(), bbox.center().y(), bbox.center().z()),
        "attributes": [attrib.name() for attrib in geo.pointAttribs()]
    }

def validate_node_parameters(node: hou.SopNode) -> bool:
    """
    Checks if the node has all expected parameters exposed by the C++ PRM_Template list.
    """
    expected_parms = ["group", "scale", "center", "offset", "upd_normals", "upd_color", "upd_pscale", "pscale_val"]
    for parm_name in expected_parms:
        if node.parm(parm_name) is None and node.parmTuple(parm_name) is None:
            return False
    return True
