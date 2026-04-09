import maya.cmds as mc

def CreateCircleControllerForJnt(jnt, namePrefix, radius=10):
    ctrlName = f"ac_{namePrefix}_{jnt}"  
    mc.circle(n=ctrlName, r = radius, nr=(1,0,0))

    ctrlGrpName = ctrlName + "_grp"
    mc.group(ctrlName, n=ctrlGrpName)

    mc.matchTransform(ctrlGrpName, jnt)
    mc.orientConstraint(ctrlName, jnt)    

    return ctrlName, ctrlGrpName