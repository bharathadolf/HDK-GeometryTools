"""
Version 8: Qt UI for Bharath::ScalePoints

A modern PySide (PySide2/PySide6) Qt dialog that attaches to Houdini's main window,
allowing interactive control and live geometry inspection for the C++ SOP node.
"""

import hou

try:
    from PySide6 import QtWidgets, QtCore, QtGui
except ImportError:
    from PySide2 import QtWidgets, QtCore, QtGui

from .hom_interface import apply_scale_preset, get_node_geometry_statistics

class ScalePointsInspectorDialog(QtWidgets.QDialog):
    """
    Interactive Qt Dialog for inspecting and adjusting Bharath::ScalePoints nodes.
    """
    def __init__(self, node: hou.SopNode, parent=None):
        parent = parent or hou.qt.mainWindow()
        super().__init__(parent)
        self.node = node
        self.setWindowTitle(f"Bharath ScalePoints Inspector - {node.name()}")
        self.resize(440, 520)
        self.setProperty("houdiniStyle", True)
        self.setup_ui()
        self.sync_from_node()

    def setup_ui(self):
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(15, 15, 15, 15)

        # Title Banner
        title_box = QtWidgets.QGroupBox("Target Node Information")
        title_layout = QtWidgets.QVBoxLayout(title_box)
        self.lbl_node_path = QtWidgets.QLabel(f"Path: {self.node.path()}")
        self.lbl_node_path.setStyleSheet("font-weight: bold; color: #4FC3F7;")
        self.lbl_stats = QtWidgets.QLabel("Points: Loading...")
        title_layout.addWidget(self.lbl_node_path)
        title_layout.addWidget(self.lbl_stats)
        main_layout.addWidget(title_box)

        # Transform Controls
        xform_box = QtWidgets.QGroupBox("Point Transformation")
        xform_layout = QtWidgets.QGridLayout(xform_box)

        # Uniform Scale
        xform_layout.addWidget(QtWidgets.QLabel("Scale (XYZ):"), 0, 0)
        self.spn_scale_x = QtWidgets.QDoubleSpinBox()
        self.spn_scale_y = QtWidgets.QDoubleSpinBox()
        self.spn_scale_z = QtWidgets.QDoubleSpinBox()
        for i, spn in enumerate([self.spn_scale_x, self.spn_scale_y, self.spn_scale_z]):
            spn.setRange(-1000.0, 1000.0)
            spn.setSingleStep(0.1)
            spn.setValue(1.0)
            spn.valueChanged.connect(self.on_transform_changed)
            xform_layout.addWidget(spn, 0, i + 1)

        # Center / Pivot
        xform_layout.addWidget(QtWidgets.QLabel("Center (XYZ):"), 1, 0)
        self.spn_center_x = QtWidgets.QDoubleSpinBox()
        self.spn_center_y = QtWidgets.QDoubleSpinBox()
        self.spn_center_z = QtWidgets.QDoubleSpinBox()
        for i, spn in enumerate([self.spn_center_x, self.spn_center_y, self.spn_center_z]):
            spn.setRange(-10000.0, 10000.0)
            spn.setSingleStep(0.5)
            spn.valueChanged.connect(self.on_transform_changed)
            xform_layout.addWidget(spn, 1, i + 1)

        # Offset
        xform_layout.addWidget(QtWidgets.QLabel("Offset (XYZ):"), 2, 0)
        self.spn_offset_x = QtWidgets.QDoubleSpinBox()
        self.spn_offset_y = QtWidgets.QDoubleSpinBox()
        self.spn_offset_z = QtWidgets.QDoubleSpinBox()
        for i, spn in enumerate([self.spn_offset_x, self.spn_offset_y, self.spn_offset_z]):
            spn.setRange(-10000.0, 10000.0)
            spn.setSingleStep(0.5)
            spn.valueChanged.connect(self.on_transform_changed)
            xform_layout.addWidget(spn, 2, i + 1)

        main_layout.addWidget(xform_box)

        # Attributes Checkboxes
        attrib_box = QtWidgets.QGroupBox("Attribute Output Toggles")
        attrib_layout = QtWidgets.QVBoxLayout(attrib_box)
        self.chk_normals = QtWidgets.QCheckBox("Recalculate Normals (N)")
        self.chk_color = QtWidgets.QCheckBox("Compute Displacement Tint (Cd)")
        self.chk_pscale = QtWidgets.QCheckBox("Update pscale")
        
        self.chk_normals.stateChanged.connect(self.on_attrib_changed)
        self.chk_color.stateChanged.connect(self.on_attrib_changed)
        self.chk_pscale.stateChanged.connect(self.on_attrib_changed)

        attrib_layout.addWidget(self.chk_normals)
        attrib_layout.addWidget(self.chk_color)
        attrib_layout.addWidget(self.chk_pscale)
        main_layout.addWidget(attrib_box)

        # Presets Group
        preset_box = QtWidgets.QGroupBox("Quick Presets")
        preset_layout = QtWidgets.QHBoxLayout(preset_box)
        btn_double = QtWidgets.QPushButton("2x Size")
        btn_half = QtWidgets.QPushButton("0.5x Size")
        btn_flatten = QtWidgets.QPushButton("Flatten Y")
        btn_reset = QtWidgets.QPushButton("Reset")

        btn_double.clicked.connect(lambda: self.apply_preset("double_size"))
        btn_half.clicked.connect(lambda: self.apply_preset("half_size"))
        btn_flatten.clicked.connect(lambda: self.apply_preset("flatten_y"))
        btn_reset.clicked.connect(self.reset_parameters)

        preset_layout.addWidget(btn_double)
        preset_layout.addWidget(btn_half)
        preset_layout.addWidget(btn_flatten)
        preset_layout.addWidget(btn_reset)
        main_layout.addWidget(preset_box)

        # Refresh button
        btn_refresh = QtWidgets.QPushButton("Refresh Stats")
        btn_refresh.clicked.connect(self.update_statistics)
        main_layout.addWidget(btn_refresh)

    def sync_from_node(self):
        """Reads parameter values from the Houdini node into Qt widgets."""
        if not self.node or not self.node.isValid():
            return

        s = self.node.parmTuple("scale").eval()
        self.spn_scale_x.setValue(s[0])
        self.spn_scale_y.setValue(s[1])
        self.spn_scale_z.setValue(s[2])

        c = self.node.parmTuple("center").eval()
        self.spn_center_x.setValue(c[0])
        self.spn_center_y.setValue(c[1])
        self.spn_center_z.setValue(c[2])

        o = self.node.parmTuple("offset").eval()
        self.spn_offset_x.setValue(o[0])
        self.spn_offset_y.setValue(o[1])
        self.spn_offset_z.setValue(o[2])

        self.chk_normals.setChecked(bool(self.node.parm("upd_normals").eval()))
        self.chk_color.setChecked(bool(self.node.parm("upd_color").eval()))
        self.chk_pscale.setChecked(bool(self.node.parm("upd_pscale").eval()))

        self.update_statistics()

    def on_transform_changed(self):
        """Pushes values from Qt widgets to the Houdini node parameters."""
        with hou.undos.group("Update Bharath::ScalePoints from Qt"):
            self.node.parmTuple("scale").set((
                self.spn_scale_x.value(),
                self.spn_scale_y.value(),
                self.spn_scale_z.value()
            ))
            self.node.parmTuple("center").set((
                self.spn_center_x.value(),
                self.spn_center_y.value(),
                self.spn_center_z.value()
            ))
            self.node.parmTuple("offset").set((
                self.spn_offset_x.value(),
                self.spn_offset_y.value(),
                self.spn_offset_z.value()
            ))
        self.update_statistics()

    def on_attrib_changed(self):
        with hou.undos.group("Toggle Attributes from Qt"):
            self.node.parm("upd_normals").set(1 if self.chk_normals.isChecked() else 0)
            self.node.parm("upd_color").set(1 if self.chk_color.isChecked() else 0)
            self.node.parm("upd_pscale").set(1 if self.chk_pscale.isChecked() else 0)
        self.update_statistics()

    def apply_preset(self, preset_name: str):
        apply_scale_preset(self.node, preset_name)
        self.sync_from_node()

    def reset_parameters(self):
        with hou.undos.group("Reset ScalePoints"):
            self.node.parmTuple("scale").set((1.0, 1.0, 1.0))
            self.node.parmTuple("center").set((0.0, 0.0, 0.0))
            self.node.parmTuple("offset").set((0.0, 0.0, 0.0))
        self.sync_from_node()

    def update_statistics(self):
        stats = get_node_geometry_statistics(self.node)
        pt_count = stats.get("point_count", 0)
        attribs = ", ".join(stats.get("attributes", []))
        self.lbl_stats.setText(f"Points: {pt_count} | Attribs: [{attribs}]")

def show_scale_points_dialog():
    """Entry point to launch the Qt dialog for currently selected node."""
    selected = hou.selectedNodes()
    target_node = None
    for n in selected:
        if n.type().name() == "Bharath::ScalePoints":
            target_node = n
            break

    if not target_node:
        hou.ui.displayMessage("Please select a 'Bharath::ScalePoints' node first!", severity=hou.severityType.Warning)
        return None

    dialog = ScalePointsInspectorDialog(target_node)
    dialog.show()
    return dialog
