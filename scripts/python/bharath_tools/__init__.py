"""
Bharath Geometry Tools Python Package
Exposes HOM (Houdini Object Model) interfaces, automation scripts, and Qt GUI tools.
"""

from .hom_interface import (
    create_scale_points_node,
    apply_scale_preset,
    get_node_geometry_statistics,
    validate_node_parameters
)
from .ui import show_scale_points_dialog

__all__ = [
    "create_scale_points_node",
    "apply_scale_preset",
    "get_node_geometry_statistics",
    "validate_node_parameters",
    "show_scale_points_dialog",
]
