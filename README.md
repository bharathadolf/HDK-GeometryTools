# Bharath::GeometryTools — Houdini HDK Master Project

A production-grade Houdini Development Kit (HDK) C++ project demonstrating the complete engineering lifecycle from a simple Surface Operator (SOP) to multithreading, attributes, groups, Python/HOM integration, Qt GUI, automated testing, and CMake packaging.

---

## Architecture Overview

```
d:/Project HDK/
├── CMakeLists.txt              # Root modern CMake build configuration
├── package/
│   └── Bharath_GeometryTools.json.in # Houdini Package distribution template
├── src/
│   ├── SOP_ScalePoints.h       # C++ Node Declaration
│   └── SOP_ScalePoints.C       # C++ Cook Engine & Operator Registration
├── scripts/
│   └── python/
│       └── bharath_tools/
│           ├── __init__.py     # Python module initialization
│           ├── hom_interface.py# HOM / Python bindings & helpers (Version 6)
│           └── ui.py           # PySide2/PySide6 Qt Dialog (Version 8)
├── tests/
│   ├── test_scale_points.py    # Automated hython test suite (Version 7)
│   └── run_tests.bat           # Automated test launcher batch script
├── help/
│   └── nodes/sop/
│       └── Bharath--ScalePoints.txt # Houdini native Wiki documentation (Version 10)
└── README.md                   # This master documentation
```

---

## Progressive Evolution Roadmap

| Version | Milestone | Description |
| :--- | :--- | :--- |
| **V1** | **Base C++ SOP** | Minimal `OP_Operator` registered in `newSopOperator`, `duplicateSource(0, context)`, point loop. |
| **V2** | **Parameters** | Added `PRM_Template` parameters: `scale`, `center`, and `offset` with math: `center + (P - center) * scale + offset`. |
| **V3** | **Attributes** | Added `GA_RWHandle` support for creating and modifying `Cd` (color tint), `N` (normals), and `pscale`. |
| **V4** | **Point Groups** | Added `PRM_STRING` group picker and `parsePointGroups()` to filter transformations by group mask. |
| **V5** | **Multithreading** | Replaced serial loops with `UTparallelFor` and `GA_SplittableRange` for CPU parallel execution. |
| **V6** | **Python / HOM** | Created `bharath_tools.hom_interface` module with programmatic creation, presets, and query utilities. |
| **V7** | **Automated Tests** | Created `tests/test_scale_points.py` executed via `hython` covering math, attributes, and groups. |
| **V8** | **Qt UI** | Built `bharath_tools.ui` PySide dialog hooked to `hou.qt.mainWindow()` for real-time inspector control. |
| **V9** | **CMake Packaging** | Configured `CMakeLists.txt` with `find_package(Houdini)` and automated Houdini Package JSON creation. |
| **V10**| **Documentation** | Created native Houdini Wiki help documentation (`Bharath--ScalePoints.txt`). |

---

## How to Build (Visual Studio & CMake)

### Prerequisites
1. **SideFX Houdini** (Core or FX, version 19.5, 20.0, or 20.5).
2. **Visual Studio 2022** (with *Desktop development with C++* installed).
3. **CMake 3.22+**.

### Step 1: Open "Houdini Command Line Tools"
Search for **Houdini Command Line Tools** in the Windows Start menu and open it. This automatically sets `HFS`, `PATH`, and compiler environment variables.

### Step 2: Configure with CMake
Run the following in `d:\Project HDK`:
```powershell
mkdir build
cd build
cmake -G "Visual Studio 17 2022" -A x64 ..
```

### Step 3: Compile the Plugin
```powershell
cmake --build . --config Release
```
This produces:
- `build/install/Bharath_GeometryTools/dso/SOP_ScalePoints.dll`
- `build/Bharath_GeometryTools.json`

### Step 4: Install to Houdini
Copy the generated `build/Bharath_GeometryTools.json` into your user packages directory:
```powershell
copy Bharath_GeometryTools.json "%USERPROFILE%\Documents\houdini20.5\packages\"
```

Launch Houdini. In any geometry network (`/obj/geo1`), press **Tab** and search for **Bharath Scale Points**!
