#include "SOP_ScalePoints.h"

// HDK Core Headers
#include <OP/OP_Operator.h>
#include <OP/OP_OperatorTable.h>
#include <PRM/PRM_Include.h>
#include <PRM/PRM_Range.h>
#include <GU/GU_Detail.h>
#include <GA/GA_SplittableRange.h>
#include <GA/GA_Handle.h>
#include <UT/UT_DMatrix4.h>
#include <UT/UT_ParallelUtil.h>
#include <UT/UT_Interrupt.h>

using namespace Bharath;

// ==============================================================================
// 1. PARAMETER DEFINITIONS (Python: Type Properties -> Parameters)
// ==============================================================================

// Parameter names and UI labels
static PRM_Name prmGroupName("group", "Group");
static PRM_Name prmScaleName("scale", "Scale");
static PRM_Name prmCenterName("center", "Center");
static PRM_Name prmOffsetName("offset", "Offset");

static PRM_Name prmUpdNormalsName("upd_normals", "Recalculate Normals (N)");
static PRM_Name prmUpdColorName("upd_color", "Compute Velocity/Scale Tint (Cd)");
static PRM_Name prmUpdPscaleName("upd_pscale", "Multiply pscale");
static PRM_Name prmPscaleFactorName("pscale_val", "pscale Multiplier");

// Default values (Python: default_value in parm template)
static PRM_Default prmGroupDefault(0, "");
static PRM_Default prmScaleDefaults[] = { PRM_Default(1.0), PRM_Default(1.0), PRM_Default(1.0) };
static PRM_Default prmCenterDefaults[] = { PRM_Default(0.0), PRM_Default(0.0), PRM_Default(0.0) };
static PRM_Default prmOffsetDefaults[] = { PRM_Default(0.0), PRM_Default(0.0), PRM_Default(0.0) };
static PRM_Default prmToggleDefault(1);
static PRM_Default prmPscaleDefault(1.0);

// Parameter Template List (Houdini uses this array to build the UI)
PRM_Template SOP_ScalePoints::myTemplateList[] = {
    // String parameter for group selection with point group picker menu
    PRM_Template(PRM_STRING, 1, &prmGroupName, &prmGroupDefault, &SOP_Node::pointGroupMenu),
    
    // 3-float vector for 3D scale
    PRM_Template(PRM_XYZ, 3, &prmScaleName, prmScaleDefaults),
    
    // 3-float vector for pivot center
    PRM_Template(PRM_XYZ, 3, &prmCenterName, prmCenterDefaults),
    
    // 3-float vector for translation offset
    PRM_Template(PRM_XYZ, 3, &prmOffsetName, prmOffsetDefaults),
    
    // Attribute toggles
    PRM_Template(PRM_TOGGLE, 1, &prmUpdNormalsName, &prmToggleDefault),
    PRM_Template(PRM_TOGGLE, 1, &prmUpdColorName, &prmToggleDefault),
    PRM_Template(PRM_TOGGLE, 1, &prmUpdPscaleName, &prmToggleDefault),
    PRM_Template(PRM_FLT, 1, &prmPscaleFactorName, &prmPscaleDefault),
    
    PRM_Template() // Terminator (Null sentinel ending the list)
};

// ==============================================================================
// 2. OPERATOR REGISTRATION (The entry point Houdini calls on startup)
// ==============================================================================
// In Python plugins, you might do: hou.nodeTypeCategories()['Sop'].register(...)
// In C++, Houdini searches the DLL for this exact extern "C" C-linkage function:
void newSopOperator(OP_OperatorTable *table)
{
    table->addOperator(new OP_Operator(
        "Bharath::ScalePoints",             // Internal operator name
        "Bharath Scale Points",            // UI Label shown in the Tab menu
        SOP_ScalePoints::myConstructor,    // Pointer to constructor function
        SOP_ScalePoints::myTemplateList,   // UI Parameter definitions
        1,                                 // Min inputs (1 input geometry required)
        1,                                 // Max inputs
        nullptr,                           // Local variables (deprecated in modern HDK)
        OP_FLAG_GENERATOR                  // Flags (0 or generator)
    ));
}

// Factory function
OP_Node *SOP_ScalePoints::myConstructor(OP_Network *net, const char *name, OP_Operator *entry)
{
    return new SOP_ScalePoints(net, name, entry);
}

SOP_ScalePoints::SOP_ScalePoints(OP_Network *net, const char *name, OP_Operator *entry)
    : SOP_Node(net, name, entry)
{
    // Need this so Houdini knows this node modifies incoming geometry
    mySopFlags.setNeedConfigure(true);
}

SOP_ScalePoints::~SOP_ScalePoints()
{
}

// ==============================================================================
// 3. PARAMETER EVALUATION HELPERS
// ==============================================================================
void SOP_ScalePoints::getGroupString(UT_String &str, fpreal t)
{
    evalString(str, "group", 0, t);
}

UT_Vector3 SOP_ScalePoints::getScale(fpreal t)
{
    return UT_Vector3(
        evalFloat("scale", 0, t),
        evalFloat("scale", 1, t),
        evalFloat("scale", 2, t)
    );
}

UT_Vector3 SOP_ScalePoints::getCenter(fpreal t)
{
    return UT_Vector3(
        evalFloat("center", 0, t),
        evalFloat("center", 1, t),
        evalFloat("center", 2, t)
    );
}

UT_Vector3 SOP_ScalePoints::getOffset(fpreal t)
{
    return UT_Vector3(
        evalFloat("offset", 0, t),
        evalFloat("offset", 1, t),
        evalFloat("offset", 2, t)
    );
}

bool SOP_ScalePoints::getUpdateNormals(fpreal t)
{
    return evalInt("upd_normals", 0, t) != 0;
}

bool SOP_ScalePoints::getUpdateColor(fpreal t)
{
    return evalInt("upd_color", 0, t) != 0;
}

bool SOP_ScalePoints::getUpdatePscale(fpreal t)
{
    return evalInt("upd_pscale", 0, t) != 0;
}

fpreal SOP_ScalePoints::getPscaleFactor(fpreal t)
{
    return evalFloat("pscale_val", 0, t);
}

// ==============================================================================
// 4. THE COOK ENGINE (Python: def cook(self))
// ==============================================================================
OP_ERROR SOP_ScalePoints::cookMySop(OP_Context &context)
{
    // STEP A: Lock Inputs (prevents upstream nodes from modifying geometry concurrently)
    if (lockInputs(context) >= UT_ERROR_ABORT)
        return error();

    // STEP B: Duplicate Geometry from Input 0 into gdp (GU_Detail*)
    // 'gdp' is the member variable holding our output geometry buffer!
    duplicateSource(0, context);

    // Current evaluation time
    fpreal t = context.getTime();

    // STEP C: Evaluate Parameters
    UT_String group_str;
    getGroupString(group_str, t);

    UT_Vector3 scale_val  = getScale(t);
    UT_Vector3 center_val = getCenter(t);
    UT_Vector3 offset_val = getOffset(t);

    bool upd_normals = getUpdateNormals(t);
    bool upd_color   = getUpdateColor(t);
    bool upd_pscale  = getUpdatePscale(t);
    fpreal pscale_mult = getPscaleFactor(t);

    // STEP D: Parse Group (Version 4)
    // If group string is provided, find or build the point group
    const GA_PointGroup *group = nullptr;
    if (group_str.isstring())
    {
        group = parsePointGroups(group_str, GroupCreator(gdp));
        if (!group)
        {
            addWarning(SOP_MESSAGE, "Specified group could not be found or parsed.");
        }
    }

    // Determine the range of points to process:
    // If a group was specified, only include points in that group; otherwise, all points.
    GA_Range point_range = group ? gdp->getPointRange(group) : gdp->getPointRange();

    if (point_range.isEmpty())
    {
        // Nothing to process, unlock and return cleanly
        unlockInputs(context);
        return error();
    }

    // STEP E: Prepare Attributes (Version 3)
    // In HDK, we use GA_RWHandle (Read/Write Handle) for high-performance direct memory access.
    // Equivalent in Python: geo.findPointAttrib("Cd") or geo.addAttrib(hou.attribType.Point, "Cd", (1.0, 1.0, 1.0))
    
    GA_RWHandleV3 h_cd;
    if (upd_color)
    {
        GA_Attribute *attrib = gdp->findPointAttribute("Cd");
        if (!attrib)
            attrib = gdp->addFloatTuple(GA_ATTRIB_POINT, "Cd", 3);
        h_cd.bind(attrib);
    }

    GA_RWHandleV3 h_n;
    if (upd_normals)
    {
        GA_Attribute *attrib = gdp->findPointAttribute("N");
        if (!attrib)
            attrib = gdp->addFloatTuple(GA_ATTRIB_POINT, "N", 3);
        h_n.bind(attrib);
    }

    GA_RWHandleF h_pscale;
    if (upd_pscale)
    {
        GA_Attribute *attrib = gdp->findPointAttribute("pscale");
        if (!attrib)
        {
            attrib = gdp->addFloatTuple(GA_ATTRIB_POINT, "pscale", 1);
            // Default new pscale to 1.0
            GA_RWHandleF tmp_handle(attrib);
            for (GA_Iterator it(point_range); !it.atEnd(); ++it)
                tmp_handle.set(*it, 1.0f);
        }
        h_pscale.bind(attrib);
    }

    // Read/write handle to the built-in position attribute "P"
    GA_RWHandleV3 h_p(gdp->getP());

    // STEP F: Multithreaded Processing (Version 5)
    // Convert point range to a SplittableRange so UTparallelFor can divide it among CPU cores.
    GA_SplittableRange splittable_range(point_range);

    // UTparallelFor distributes sub-ranges to Houdini's worker thread pool
    UTparallelFor(splittable_range, [&](const GA_SplittableRange &sub_range)
    {
        for (GA_Iterator it(sub_range); !it.atEnd(); ++it)
        {
            GA_Offset ptoff = *it;

            // 1. Point Position Transformation (Version 1 & 2 Math)
            // pos_new = center + (pos_orig - center) * scale + offset
            UT_Vector3 orig_pos = h_p.get(ptoff);
            UT_Vector3 centered = orig_pos - center_val;
            
            UT_Vector3 scaled_pos(
                centered.x() * scale_val.x(),
                centered.y() * scale_val.y(),
                centered.z() * scale_val.z()
            );
            
            UT_Vector3 final_pos = center_val + scaled_pos + offset_val;
            h_p.set(ptoff, final_pos);

            // 2. Normal recalculation (Version 3)
            if (h_n.isValid())
            {
                UT_Vector3 normal = h_n.get(ptoff);
                if (normal.length2() < 1e-6f)
                {
                    // Fallback: outward vector from center
                    normal = final_pos - center_val;
                }
                else
                {
                    // Scale inverse transpose for normal vectors
                    normal.x() /= (scale_val.x() != 0.0f ? scale_val.x() : 1.0f);
                    normal.y() /= (scale_val.y() != 0.0f ? scale_val.y() : 1.0f);
                    normal.z() /= (scale_val.z() != 0.0f ? scale_val.z() : 1.0f);
                }
                normal.normalize();
                h_n.set(ptoff, normal);
            }

            // 3. Color tint based on displacement / scale intensity (Version 3)
            if (h_cd.isValid())
            {
                UT_Vector3 displacement = final_pos - orig_pos;
                fpreal disp_len = displacement.length();
                // Map displacement length to a pleasing gradient (tint)
                UT_Vector3 tint(
                    SYSclamp(disp_len * 0.5f, 0.1f, 1.0f),
                    SYSclamp(1.0f - disp_len * 0.25f, 0.2f, 0.9f),
                    SYSclamp(scale_val.length() * 0.33f, 0.1f, 1.0f)
                );
                h_cd.set(ptoff, tint);
            }

            // 4. pscale update (Version 3)
            if (h_pscale.isValid())
            {
                fpreal current_pscale = h_pscale.get(ptoff);
                fpreal avg_scale = (scale_val.x() + scale_val.y() + scale_val.z()) / 3.0f;
                h_pscale.set(ptoff, current_pscale * static_cast<float>(pscale_mult * avg_scale));
            }
        }
    });

    // Notify Houdini that P and attributes changed so the viewport updates
    gdp->getP()->bumpDataId();
    if (h_cd.isValid())     h_cd.getAttribute()->bumpDataId();
    if (h_n.isValid())      h_n.getAttribute()->bumpDataId();
    if (h_pscale.isValid()) h_pscale.getAttribute()->bumpDataId();

    // STEP G: Unlock inputs
    unlockInputs(context);
    return error();
}
