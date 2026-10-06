#ifndef __SOP_ScalePoints_h__
#define __SOP_ScalePoints_h__

#include <SOP/SOP_Node.h>
#include <UT/UT_StringHolder.h>
#include <UT/UT_Vector3.h>

namespace Bharath
{

/// \class SOP_ScalePoints
/// \brief Custom Houdini C++ Surface Operator (SOP) that scales, offsets,
///        recalculates attributes (N, Cd, pscale), and handles groups multithreaded.
///
/// PYTHON ANALOGY:
/// In Python, you might write:
/// class ScalePoints(hou.Node):
///     def cook(self): ...
///
/// In C++, we inherit from SOP_Node and override cookMySop().
class SOP_ScalePoints : public SOP_Node
{
public:
    /// Factory constructor required by Houdini's operator registration system.
    /// Equivalent to Python's __init__().
    static OP_Node *myConstructor(OP_Network *net, const char *name, OP_Operator *entry);

    /// Declares the parameters (sliders, inputs) for this node.
    /// In Python/HDA terms, this is your "Type Properties -> Parameters" tab.
    static PRM_Template myTemplateList[];

protected:
    SOP_ScalePoints(OP_Network *net, const char *name, OP_Operator *entry);
    virtual ~SOP_ScalePoints();

    /// cookMySop() is called whenever Houdini needs to evaluate this node!
    /// Equivalent to Python SOP's cook(self) or VEX execution.
    virtual OP_ERROR cookMySop(OP_Context &context) override;

private:
    // Helper methods to read parameter values at a specific time (context.getTime())
    // In Python: self.parm("group").evalAsString()
    void        getGroupString(UT_String &str, fpreal t);
    
    // In Python: self.parmTuple("scale").eval()
    UT_Vector3  getScale(fpreal t);
    
    // In Python: self.parmTuple("center").eval()
    UT_Vector3  getCenter(fpreal t);
    
    // In Python: self.parmTuple("offset").eval()
    UT_Vector3  getOffset(fpreal t);

    // Attribute toggle flags
    bool        getUpdateNormals(fpreal t);
    bool        getUpdateColor(fpreal t);
    bool        getUpdatePscale(fpreal t);
    fpreal      getPscaleFactor(fpreal t);
};

} // namespace Bharath

#endif // __SOP_ScalePoints_h__
