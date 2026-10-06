# Houdini HDK Master Guide: From Python to C++ Operator Mastery

> **Audience:** Technical Artists, Python developers, and TDs with zero C++ experience seeking to build high-performance Houdini C++ plugins.  
> **Project:** `Bharath::GeometryTools` (Versions 1–10)

---

## Table of Contents
1. [The "Python to C++" Mental Bridge](#1-the-python-to-c-mental-bridge)
   - [A. Interpreted vs. Compiled](#a-interpreted-vs-compiled)
   - [B. Variables, Types, Pointers, and References](#b-variables-types-pointers-and-references)
   - [C. Classes, Inheritance, and the SOP Lifecycle](#c-classes-inheritance-and-the-sop-lifecycle)
2. [Steps to Write and Register a Basic Surface Operator (SOP)](#2-steps-to-write-and-register-a-basic-surface-operator-sop)
3. [Setting Up a Custom CMake Project for HDK](#3-setting-up-a-custom-cmake-project-for-hdk)
4. [Compiling & Troubleshooting in Visual Studio and Houdini](#4-compiling--troubleshooting-in-visual-studio-and-houdini)
   - [A. How to Compile on Windows](#a-how-to-compile-on-windows)
   - [B. Troubleshooting Compilation & Linker Errors](#b-troubleshooting-compilation--linker-errors)
   - [C. Troubleshooting Runtime Errors & Crashes](#c-troubleshooting-runtime-errors--crashes)
   - [D. Attaching Visual Studio Debugger](#d-attaching-visual-studio-debugger)
5. [The Progressive Master Project: Bharath::GeometryTools (V1–V10)](#5-the-progressive-master-project-bharathgeometrytools-v1v10)
6. [Quick Build & Test Runbook](#6-quick-build--test-runbook)

---

## 1. The "Python to C++" Mental Bridge

To master C++, you do not need to relearn computer science from scratch. You only need to map what you already know in Python to how C++ operates at the hardware level.

### A. Interpreted vs. Compiled

* **In Python:** You write `.py` scripts. Python reads text line-by-line, converts it into bytecode on the fly, and runs it inside the virtual machine. If you make a typo on line 90, lines 1–89 execute before the script crashes.
* **In C++:** The computer cannot run `.cpp` files directly. You run a **compiler** (e.g., Microsoft Visual Studio `MSVC`). It scans all files, verifies strict type rules, translates them into raw machine code, and links them into a binary library (`.dll` on Windows, `.so` on Linux). Once compiled, Houdini loads the binary directly into memory.

```
Python:  Code.py   ─────────────► Python VM Interpreter ─────────────► CPU Execution
C++:     Code.cpp  ──► Compiler ──► Linker ──► Plugin.dll ──► Houdini ──► Direct CPU Execution
```

---

### B. Variables, Types, Pointers (`*`), and References (`&`)

#### 1. Static Typing vs. Dynamic Typing

In Python, variables are dynamically typed labels pointing to objects:
```python
x = 10        # Integer
x = "Houdini" # Rebound to a String dynamically
```

In C++, every variable must declare a fixed memory type upfront:
```cpp
int x = 10;
// x = "Houdini"; // COMPILE ERROR: Cannot store string data in integer memory!
```

---

#### 2. Values vs. Pointers (`*`)

| Concept | Syntax | Meaning | Python Equivalent |
| :--- | :--- | :--- | :--- |
| **Value** | `int a = 5;` | You own the actual box in memory. | `a = 5` |
| **Pointer** | `int* p = &a;` | You hold the **memory address** (house address) of `a`. | Storing the `id(a)` / object reference |
| **Dereference** | `*p = 20;` | Follow the address and modify the box contents. | Modifying mutable object in-place |

> [!CAUTION]
> **Null Pointers Cause Immediate Crashes!**  
> In Python, accessing an attribute on `None` throws `AttributeError`.  
> In C++, dereferencing `nullptr` causes an OS-level **Access Violation (`0xC0000005`)** that instantly crashes Houdini to desktop without saving!
>
> ```cpp
> GU_Detail* gdp = nullptr;
> // gdp->getP(); // CRASH! Trying to access memory address 0x00000000
> ```

---

#### 3. References (`&`)

A reference is a permanent alias (nickname) for an existing object that can never be null:
```cpp
void processGeo(const GU_Detail &geo) {
    // 'geo' is an unchangeable alias to the real geometry. No slow memory copying!
}
```

---

### C. Classes, Inheritance, and the SOP Lifecycle

#### Python HOM (Houdini Object Model)
```python
class MySop(hou.Node):
    def cook(self):
        geo = self.geometry()
        # Modify geo in Python...
```

#### C++ HDK
```cpp
class SOP_ScalePoints : public SOP_Node {
protected:
    virtual OP_ERROR cookMySop(OP_Context &context) override {
        duplicateSource(0, context); // Copy input 0 into gdp (GU_Detail*)
        // 'gdp' is the member pointer to output geometry
        return error();
    }
};
```
* **`public SOP_Node`**: Inheritance (equivalent to `class MySop(hou.Node)`).
* **`virtual` & `override`**: Tells Houdini: *"When this node cooks, execute my custom C++ method instead of the base class default."*

---

## 2. Steps to Write and Register a Basic Surface Operator (SOP)

Every HDK SOP follows a strict 4-step architecture:

```
┌────────────────────────────────────────────────────────┐
│ 1. newSopOperator(OP_OperatorTable *table)             │ ◄── Houdini startup hook
│    Registers the operator type name and factory        │
└──────────────────────────┬─────────────────────────────┘
                           │
┌──────────────────────────▼─────────────────────────────┐
│ 2. PRM_Template myTemplateList[]                       │ ◄── Declares UI Parameters
│    Sliders, Vectors, Strings, Menus                    │
└──────────────────────────┬─────────────────────────────┘
                           │
┌──────────────────────────▼─────────────────────────────┐
│ 3. Factory Constructor (myConstructor)                 │ ◄── Instantiates the C++ class
│    Creates an instance when node is dropped in network │
└──────────────────────────┬─────────────────────────────┘
                           │
┌──────────────────────────▼─────────────────────────────┐
│ 4. cookMySop(OP_Context &context)                      │ ◄── Node execution loop
│    lockInputs() ──► duplicateSource() ──► process      │
└────────────────────────────────────────────────────────┘
```

1. **Registration Hook (`newSopOperator`)**: An `extern "C"` function Houdini scans when loading the `.dll`. You provide the internal name (e.g. `Bharath::ScalePoints`), the UI label (`Bharath Scale Points`), and the parameter template.
2. **Parameter List (`PRM_Template`)**: Defines the node UI controls (equivalent to the Parameters tab in an HDA).
3. **Factory Constructor**: Instantiates the C++ class when dropped into the network editor.
4. **The Cook Function (`cookMySop`)**:
   - `lockInputs(context)`: Freezes upstream nodes while calculating.
   - `duplicateSource(0, context)`: Copies input geometry into `gdp` (`GU_Detail*`).
   - Evaluates parameters at time `context.getTime()`.
   - Directly transforms points and attributes in memory.
   - `unlockInputs(context)`: Releases upstream locks.

---

## 3. Setting Up a Custom CMake Project for HDK

Modern HDK development relies on **CMake** instead of the legacy `hcustom` command-line utility.

### Advantages of CMake
* Generates native Visual Studio solution files (`.sln`) with full IntelliSense and syntax highlighting.
* Automatically links required Houdini libraries (`HoudiniGEO.lib`, `HoudiniPRM.lib`, `HoudiniUT.lib`).
* Manages multi-file architectures, automated tests, and packaging.

### CMake Integration
Houdini ships its official CMake configuration inside `$HFS/toolkit/cmake`.

```cmake
# Add Houdini CMake modules to prefix path
list(APPEND CMAKE_PREFIX_PATH "${HOUDINI_ROOT}/toolkit/cmake")
find_package(Houdini REQUIRED)

# Configure your shared library target
add_library(SOP_ScalePoints SHARED ${SOURCE_FILES})
houdini_configure_target(SOP_ScalePoints)
```

---

## 4. Compiling & Troubleshooting in Visual Studio and Houdini

### A. How to Compile on Windows

1. Install **Visual Studio 2022** with the **Desktop development with C++** workload.
2. Open **Houdini Command Line Tools** from the Windows Start Menu (this sets `$HFS` and environment paths).
3. Configure and build:
   ```powershell
   cd /d "d:\Project HDK"
   mkdir build
   cd build
   cmake -G "Visual Studio 17 2022" -A x64 ..
   cmake --build . --config Release
   ```

---

### B. Troubleshooting Compilation & Linker Errors

| Error Code / Message | Root Cause | Solution |
| :--- | :--- | :--- |
| `fatal error: SOP/SOP_Node.h: No such file or directory` | CMake could not locate the Houdini SDK headers. | Ensure `HFS` or `HOUDINI_ROOT` points to your Houdini install (e.g., `C:/Program Files/Side Effects Software/Houdini 20.5.x`). |
| `LNK2019 / LNK2001: unresolved external symbol` | Missing implementation or unlinked Houdini library. | Ensure [CMakeLists.txt](file:///d:/Project%20HDK/CMakeLists.txt) calls `houdini_configure_target(TargetName)`. |
| `error C2338: /permissive- or C++17 required` | MSVC C++ standard mismatch. | Houdini 19.5+ requires C++17. Add `set(CMAKE_CXX_STANDARD 17)` in CMake. |

---

### C. Troubleshooting Runtime Errors & Crashes

#### 1. The Dreaded `0xC0000005: Access Violation`
Occurs when reading or writing invalid memory addresses (dereferencing a null pointer).

```cpp
// BUG:
GA_Attribute *attr = gdp->findPointAttribute("pscale");
// If "pscale" attribute did not exist, attr is nullptr!
attr->bumpDataId(); // CRASH!

// FIX:
if (attr) {
    attr->bumpDataId();
}
```

#### 2. Attribute Handle Safety (`GA_RWHandle`)
Always check `.isValid()` before calling `.get()` or `.set()`:
```cpp
GA_RWHandleV3 h_cd(gdp->findPointAttribute("Cd"));
if (h_cd.isValid()) {
    h_cd.set(ptoff, color);
}
```

#### 3. Reading Houdini Crash Logs
When Houdini crashes, it saves a detailed call stack to:  
`C:\Users\<Username>\AppData\Local\Temp\houdini_crashes\crash.YOUR_PC_pid.txt`  
Open this file to view the exact line number in your C++ code that triggered the crash.

---

### D. Attaching Visual Studio Debugger

1. Build your project in **RelWithDebInfo** or **Debug**:
   ```powershell
   cmake --build . --config RelWithDebInfo
   ```
2. Open `d:\Project HDK\build\Bharath_GeometryTools.sln` in Visual Studio.
3. Launch Houdini.
4. In Visual Studio, select **Debug -> Attach to Process...** (`Ctrl + Alt + P`).
5. Select `houdini.exe` and click **Attach**.
6. Open [SOP_ScalePoints.C](file:///d:/Project%20HDK/src/SOP_ScalePoints.C) and place a breakpoint on line inside `cookMySop`.
7. Move a slider on the node in Houdini: execution will pause at your breakpoint, allowing line-by-line debugging (`F10`) and variable inspection.

---

## 5. The Progressive Master Project: Bharath::GeometryTools (V1–V10)

### Project Directory Structure
```
d:/Project HDK/
├── CMakeLists.txt                         # V9: Modern CMake Build Configuration
├── README.md                              # Master Reference Documentation
├── package/
│   └── Bharath_GeometryTools.json.in      # V9: Houdini Package Distribution Template
├── src/
│   ├── SOP_ScalePoints.h                  # Node Class Declaration & Parameter Interface
│   └── SOP_ScalePoints.C                  # V1-V5: Cook Engine, Parameters, Attribs, Threading
├── scripts/
│   └── python/
│       └── bharath_tools/
│           ├── __init__.py                # Package Exports
│           ├── hom_interface.py           # V6: HOM Python Helpers & Presets
│           └── ui.py                      # V8: Interactive PySide Qt UI Dialog
├── tests/
│   ├── INFO.md                            # Complete HDK Guide & Architecture Reference
│   ├── test_scale_points.py               # V7: Automated Test Suite (hython)
│   └── run_tests.bat                      # V7: Test Launcher Batch Script
└── help/
    └── nodes/
        └── sop/
            └── Bharath--ScalePoints.txt   # V10: Houdini Native Wiki Help File
```

---

### Progressive Evolution Milestones

#### Version 1: The Minimal Surface Operator
* **Concept:** Connect input geometry, duplicate to `gdp`, iterate over point offsets, and transform positions.
* **Code Reference:** [SOP_ScalePoints.C](file:///d:/Project%20HDK/src/SOP_ScalePoints.C#L170-L177)
```cpp
duplicateSource(0, context); // Duplicate input geometry
GA_Range point_range = gdp->getPointRange();
GA_RWHandleV3 h_p(gdp->getP()); // Point position handle
```

---

#### Version 2: Adding Parameters (`Scale`, `Center`, `Offset`)
* **Concept:** Declare parameters using `PRM_Template`, evaluate them at time `t`, and apply affine transformation.
* **Mathematical Formula:**
  $$\vec{P}_{new} = \vec{C} + (\vec{P}_{orig} - \vec{C}) \odot \vec{S} + \vec{O}$$
* **Code Reference:** [SOP_ScalePoints.C](file:///d:/Project%20HDK/src/SOP_ScalePoints.C#L27-L44)
```cpp
UT_Vector3 orig_pos = h_p.get(ptoff);
UT_Vector3 centered = orig_pos - center_val;
UT_Vector3 scaled_pos(centered.x() * scale_val.x(), centered.y() * scale_val.y(), centered.z() * scale_val.z());
UT_Vector3 final_pos = center_val + scaled_pos + offset_val;
h_p.set(ptoff, final_pos);
```

---

#### Version 3: Adding Attributes (`Cd`, `N`, `pscale`)
* **Concept:** Create or access point attributes using type-safe handles (`GA_RWHandleV3`, `GA_RWHandleF`).
  - **`N` (Normals):** Recalculated with inverse-transpose scaling and normalized.
  - **`Cd` (Color):** Computes tint gradient from displacement distance.
  - **`pscale`:** Multiplied by average scale factor.
* **Code Reference:** [SOP_ScalePoints.C](file:///d:/Project%20HDK/src/SOP_ScalePoints.C#L207-L244)
```cpp
GA_RWHandleV3 h_cd;
if (upd_color) {
    GA_Attribute *attrib = gdp->findPointAttribute("Cd");
    if (!attrib)
        attrib = gdp->addFloatTuple(GA_ATTRIB_POINT, "Cd", 3);
    h_cd.bind(attrib);
}
```

---

#### Version 4: Adding Point Groups
* **Concept:** Parse group string masks (`0-10`, `@P.y>0`) using `parsePointGroups()` to restrict operations.
* **Code Reference:** [SOP_ScalePoints.C](file:///d:/Project%20HDK/src/SOP_ScalePoints.C#L190-L204)
```cpp
const GA_PointGroup *group = nullptr;
if (group_str.isstring()) {
    group = parsePointGroups(group_str, GroupCreator(gdp));
}
GA_Range point_range = group ? gdp->getPointRange(group) : gdp->getPointRange();
```

---

#### Version 5: High-Performance Multithreading
* **Concept:** Parallelize across CPU cores using `GA_SplittableRange` and `UTparallelFor`.
* **Thread Safety Rule:** Never add/remove attributes inside the worker thread. Pre-allocate before parallel execution!
* **Code Reference:** [SOP_ScalePoints.C](file:///d:/Project%20HDK/src/SOP_ScalePoints.C#L250-L315)
```cpp
GA_SplittableRange splittable_range(point_range);
UTparallelFor(splittable_range, [&](const GA_SplittableRange &sub_range) {
    for (GA_Iterator it(sub_range); !it.atEnd(); ++it) {
        GA_Offset ptoff = *it;
        // High-speed thread-safe point update
    }
});
```

---

#### Version 6: Python / HOM Interface
* **File:** [scripts/python/bharath_tools/hom_interface.py](file:///d:/Project%20HDK/scripts/python/bharath_tools/hom_interface.py)
* **Features:**
  - `create_scale_points_node()`: Helper to create and configure the node in one call.
  - `apply_scale_preset()`: Applies presets (`flatten_y`, `double_size`, `mirror_x`).
  - `get_node_geometry_statistics()`: Returns bounding boxes and attribute lists.

---

#### Version 7: Automated Testing Suite
* **File:** [tests/test_scale_points.py](file:///d:/Project%20HDK/tests/test_scale_points.py)
* **Execution:** Run via `hython tests/test_scale_points.py` or execute [tests/run_tests.bat](file:///d:/Project%20HDK/tests/run_tests.bat).
* **Validation Checks:**
  1. Operator registration & node creation.
  2. Geometry cooking & point count parity.
  3. Mathematical precision of scale and offset formulas.
  4. Attribute generation (`Cd`, `N`, `pscale`).
  5. Group isolation.

---

#### Version 8: Interactive Qt UI
* **File:** [scripts/python/bharath_tools/ui.py](file:///d:/Project%20HDK/scripts/python/bharath_tools/ui.py)
* **Features:**
  - PySide2/PySide6 window attached to `hou.qt.mainWindow()`.
  - Real-time two-way synchronization within undo blocks (`hou.undos.group`).
  - Live geometry statistics readout.
  - Launch from Houdini Python Console:
    ```python
    import bharath_tools
    bharath_tools.show_scale_points_dialog()
    ```

---

#### Version 9: Modern CMake Packaging
* **Files:** [CMakeLists.txt](file:///d:/Project%20HDK/CMakeLists.txt) & [package/Bharath_GeometryTools.json.in](file:///d:/Project%20HDK/package/Bharath_GeometryTools.json.in)
* **Features:**
  - Automatically builds binary `.dll` into `build/install/Bharath_GeometryTools/dso/`.
  - Copies Python scripts and help documentation.
  - Generates package descriptor `Bharath_GeometryTools.json` for zero-install distribution.

---

#### Version 10: Native Help Documentation
* **File:** [help/nodes/sop/Bharath--ScalePoints.txt](file:///d:/Project%20HDK/help/nodes/sop/Bharath--ScalePoints.txt)
* **Features:**
  - Formatted in Houdini Wiki syntax.
  - Renders directly in Houdini's built-in help browser when clicking the **`?`** icon on the node.

---

## 6. Quick Build & Test Runbook

```cmd
:: 1. Open Houdini Command Line Tools and navigate to project root
cd /d "d:\Project HDK"

:: 2. Configure build system
mkdir build
cd build
cmake -G "Visual Studio 17 2022" -A x64 ..

:: 3. Compile plugin
cmake --build . --config Release

:: 4. Deploy package definition to Houdini
copy Bharath_GeometryTools.json "%USERPROFILE%\Documents\houdini20.5\packages\"

:: 5. Run automated test suite
cd ..\tests
run_tests.bat
```

> [!TIP]
> Once installed, launch Houdini, drop down a Geometry network (`/obj/geo1`), press **Tab**, and search for **Bharath Scale Points**.