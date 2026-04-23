import importlib
import core.MayaWidget
importlib.reload(core.MayaWidget)

from core.MayaWidget import MayaWidget
from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QLabel
import maya.cmds as mc
from maya.OpenMaya import MVector 

import importlib
import core.MayaUtilities
importlib.reload(core.MayaUtilities)
from core.MayaUtilities import (CreateCircleControllerForJnt, CreateBoxControllerForJnt,CreatePlusController,ConfigureCtrlForJnt, GetObjectPositionAsMVec)

class LimbRigger:
    def __init__(self):
        self.nameBase = ""
        self.controllerSize = 10
        self.blendControllerSize = 4
        self.controlColorRGB = [0,0,0]

    def SetNameBase(self, NewNameBase):
        self.nameBase = NewNameBase
        print(f"name base is set to: {self.nameBase}")

    def SetControllerSize(self, newControllerSize):
        self.controllerSize = newControllerSize

    def SetBlendControllersize(self, newBlendControllerSize):
        self.blendControllerSize = newBlendControllerSize

    def RigLimb(self):
        print("start Rigging!")
        rootJnt, midJnt, endJnt = mc.ls(sl=True)
        print(f"found root {rootJnt}, mid:{midJnt}, and end: {endJnt}")

        rootCtrl, rootCtrlGrp = CreateCircleControllerForJnt(rootJnt, "fk_" + self.nameBase, self.controllerSize)
        midCtrl, midCtrlGrp = CreateCircleControllerForJnt(midJnt, "fk_" + self.nameBase, self.controllerSize)
        endCtrl, endCtrlGrp = CreateCircleControllerForJnt(endJnt, "fk_" + self.nameBase, self.controllerSize)
        
        mc.parent(endCtrlGrp, midCtrl)
        mc.parent(midCtrlGrp, rootCtrl)

        endIkCtrl, endIkCtrlGrp = CreateBoxControllerForJnt(endJnt, "ik_" + self.nameBase, self.controllerSize)

        ikFkBlendCtrlPrefix = self.nameBase + "_ikfkBlend"
        ikFkBlendController = CreatePlusController(ikFkBlendCtrlPrefix, self.blendControllerSize)
        ikFkBlendController, ikFkBlendControllerGrp = ConfigureCtrlForJnt(rootJnt, ikFkBlendController, False)

        ikfkBlendAttrName = "ikfkBlend"
        mc.addAttr(ikFkBlendController,ln=ikfkBlendAttrName, min=0, max=1, k=True)

        ikHandleName = "ikHandle_" + self.nameBase
        mc.ikHandle(n=ikHandleName, sj=rootJnt, ee=endJnt, sol="ikRPsolver")

        rootJntLoc = GetObjectPositionAsMVec(rootJnt)
        endJntLoc = GetObjectPositionAsMVec(endJnt)
        
        poleVectorVals = mc.getAttr(f"{ikHandleName}.poleVector")[0]
        poleVecDir = MVector(poleVectorVals[0], poleVectorVals[1], poleVectorVals[2])
        poleVecDir.normalize()

        rootToEndVec = endJntLoc - rootJntLoc
        rootToEndDist = rootToEndVec.length()

        poleVectorCtrlLoc = rootJntLoc + rootToEndVec/2.0 + poleVecDir * rootToEndDist

        poleVectorCtrlName = "ac_ik_" + self.nameBase + "PoleVector"
        mc.spaceLocator(n=poleVectorCtrlName)

        poleVectorCtrlGrpName = poleVectorCtrlName + "_grp"
        mc.group(poleVectorCtrlName, n = poleVectorCtrlGrpName)

        mc.setAttr(f"{poleVectorCtrlGrpName}.translate", poleVectorCtrlLoc.x, poleVectorCtrlLoc.y, poleVectorCtrlLoc.z, type="double3")
        mc.poleVectorConstraint(poleVectorCtrlName, ikHandleName)

        mc.parent(ikHandleName, endIkCtrl)
        mc.setAttr(f"{ikHandleName}.v", 0)

        mc.connectAttr(f"{ikFkBlendController}.{ikfkBlendAttrName}", f"{ikHandleName}.ikBlend")
        mc.connectAttr(f"{ikFkBlendController}.{ikfkBlendAttrName}", f"{endIkCtrlGrp}.v")
        mc.connectAttr(f"{ikFkBlendController}.{ikfkBlendAttrName}", f"{poleVectorCtrlGrpName}.v")

        reverseNodeName = f"{self.nameBase}_reverse"
        mc.createNode("reverse", n=reverseNodeName)

        mc.connectAttr(f"{ikFkBlendController}.{ikfkBlendAttrName}", f"{reverseNodeName}.inputX")
        mc.connectAttr(f"{reverseNodeName}.outputX", f"{rootCtrlGrp}.v")

        orientConstraint = None
        wristConnections = mc.listConnections(endJnt)
        for connection in wristConnections:
            if mc.objectType(connection) == "orientConstraint":
                orientConstraint = connection
                break

        mc.connectAttr(f"{ikFkBlendController}.{ikfkBlendAttrName}", f"{orientConstraint}.{endIkCtrl}W1")
        mc.connectAttr(f"{reverseNodeName}.outputX", f"{orientConstraint}.{endCtrl}W0")

        topGrpName = f"{self.nameBase}_rig_grp"
        mc.group(n=topGrpName, empty=True)

        mc.parent(rootCtrlGrp, topGrpName)
        mc.parent(ikFkBlendControllerGrp, topGrpName)
        mc.parent(endIkCtrlGrp, topGrpName)
        mc.parent(poleVectorCtrlGrpName, topGrpName)

        mc.setAttr(f"{topGrpName}.overrideEnabled", 1)
        mc.setAttr(f"{topGrpName}.overrideRGBColors", 1)

        mc.setAttr(f"{topGrpName}.overrideColorR", self.controllerColorRGB[0])
        mc.setAttr(f"{topGrpName}.overrideColorG", self.controllerColorRGB[1])
        mc.setAttr(f"{topGrpName}.overrideColorB", self.controllerColorRGB[2])

class LimbRiggerWidget(MayaWidget):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Limb Rigger")
        self.rigger = LimbRigger()
        self.masterLayout = QVBoxLayout()
        self.setLayout(self.masterLayout)
        self.controlColorRGB = [0,0,0]

        self.masterLayout.addWidget(QLabel("Select the 3 joints of the limb, from base to end, and then: "))

        self.infoLayout = QHBoxLayout()
        self.masterLayout.addLayout(self.infoLayout)
        self.infoLayout.addWidget(QLabel("Name Base:"))

        self.nameBaseLineEdit = QLineEdit()
        self.infoLayout.addWidget(self.nameBaseLineEdit)

        self.setNameBaseBtn = QPushButton("Set Name Base")
        self.setNameBaseBtn.clicked.connect(self.SetNameBaseBtnClicked)
        self.infoLayout.addWidget(self.setNameBaseBtn)

        self.masterLayout.addWidget(QLabel("Base Color:"))

        self.controlColorBtn = QPushButton("Select Color")
        self.controlColorBtn.clicked.connect(self.controlColorBtnClicked)
        self.masterLayout.addWidget (self.controlColorBtn)

        self.rigLimbBtn = QPushButton("Rig Limb") 
        self.rigLimbBtn.clicked.connect(self.RigLimbBtnClicked) 
        self.masterLayout.addWidget(self.rigLimbBtn) 

    def controlColorBtnClicked(self):
        pickedColor = QColorDialog().getColor() 
        self.rigger.controllerColorRGB[0] = pickedColor.redF() 
        self.rigger.controllerColorRGB[1] = pickedColor.greenF() 
        self.rigger.controllerColorRGB[2] = pickedColor.blueF() 
        print(self.rigger.controllerColorRGB) 

    def SetNameBaseBtnClicked(self):
        self.rigger.SetNameBase(self.nameBaseLineEdit.text()) 

    def RigLimbBtnClicked(self):
        self.rigger.RigLimb() 

    def GetWidgetHash(self):
        return "4067fcd8bf8e146af389a6de3aff0f88f88668684ed0aa0944d96e6b3b94b3e8" 

def Run():
    limbRiggerWidget = LimbRiggerWidget() 
    limbRiggerWidget.show() 

Run()