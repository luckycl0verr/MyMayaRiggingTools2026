from core.MayaWidget import MayaWidget
from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton, QLabel, QLineEdit, QColorDialog
import maya.cmds as mc
from maya.OpenMaya import MVector #This is the same as the Vector3 in Unity, transform.position.


import importlib
import core.MayaUtilities
importlib.reload(core.MayaUtilities)
from core.MayaUtilities import CreateCircleControllerForJnt, CreateBoxControllerForJnt, CreatePlusController, ConfigureCtrlForJnt, GetObjectPositionAsMVec

#The class to handle the rigging job.
class LimbRigger:
    #The constructor of the limb rigger class, to initialize the attributes.
    def __init__(self):
        self.nameBase = "" #Stores the base name used for naming all created rig elements.
        self.controllerSize = 10 #Default size for FK/IK controllers.
        self.blendControllerSize = 4 #Size for the IK/FK blend controller.
        self.controllerColorRGB = [1,1,1] #Default controller color (white in RGB).

    def SetNameBase(self, newNameBase):
        self.nameBase = newNameBase #Update the naming base.
        print(f"name base is set to: {self.nameBase}") #Print confirmation.

    def SetControllerSize(self, newControllerSize):
        self.controllerSize = newControllerSize #Update controller size.

    def SetBlendControllerSize(self, newBlendControllerSize):
        self.blendControllerSize = newBlendControllerSize #Update blend controller size.

    def RigLimb(self):
        print("Start Rigging!!") #Indicates that the rigging process has started.
        rootJnt, midJnt, endJnt = mc.ls(sl=True) #Get the selected joints (root, middle, end)
        print(f"found root {rootJnt}, mid: {midJnt}, and end {endJnt}") #Print the selected joints.

        rootCtrl, rootCtrlGrp = CreateCircleControllerForJnt(rootJnt, "fk_" + self.nameBase, self.controllerSize) #Creates the FK controller for the root joint.
        midCtrl, midCtrlGrp = CreateCircleControllerForJnt(midJnt, "fk_" + self.nameBase, self.controllerSize) #Creates the FK controller for the mid joint.
        endCtrl, endCtrlGrp = CreateCircleControllerForJnt(endJnt, "fk_" + self.nameBase, self.controllerSize) #Creates the FK controller for the end joint.

        print(f"parenting: {endCtrlGrp} to {midCtrl}") #Logs the parenting operation.
        mc.parent(endCtrlGrp, midCtrl) #Parents the end controller group under the mid controller.
        print(f"parenting: {midCtrlGrp} to {rootCtrl}") #Logs the parenting operation.
        mc.parent(midCtrlGrp, rootCtrl) #Parents the mid controller group under the root controller.

        endIKCtrl, endIKCtrlGrp = CreateBoxControllerForJnt(endJnt, "ik_" + self.nameBase, self.controllerSize) #Creates the IK controller for the end joint.

        ikFkBlendCtrlPrefix = self.nameBase+"_ikfkBlend" #The prefix for the blend controller naming.
        ikFkBlendController = CreatePlusController(ikFkBlendCtrlPrefix, self.blendControllerSize) #Creates IK/FK blend controller.
        ikFkBlendController, ikFkBlendCtrlControllerGrp = ConfigureCtrlForJnt(rootJnt, ikFkBlendController, False) #Positions the blend controller.

        ikFkBlendAttrName = "ikfkBlend" #Name of the blend attribute.
        mc.addAttr(ikFkBlendController, ln=ikFkBlendAttrName, min = 0, max = 1, k=True) #Add the blend attribute (0 = FK and 1 = IK).

        ikHandleName = "ikHandle_" + self.nameBase #Name for the IK handle.
        mc.ikHandle(n=ikHandleName, sj = rootJnt, ee=endJnt, sol="ikRPsolver") #Create the IK handle from the root joint to the end joint.

        rootJntLoc = GetObjectPositionAsMVec(rootJnt) #Get the root joint position as the vector.
        endJntLoc = GetObjectPositionAsMVec(endJnt) #Get the end joint position as the vector.

        poleVectorVals = mc.getAttr(f"{ikHandleName}.poleVector")[0] #Get the pole vector direction from the IK handle.
        poleVecDir = MVector(poleVectorVals[0], poleVectorVals[1], poleVectorVals[2]) #Coverts to a vector object.
        poleVecDir.normalize() #Make it a unit vector, a vector that has a length of 1.

        rootToEndVec = endJntLoc - rootJntLoc #Vector from the root joint to the end joint.
        rootToEndDist = rootToEndVec.length() #Distance between the root and the end joint.

        poleVectorCtrlLoc = rootJntLoc + rootToEndVec /2.0 + poleVecDir * rootToEndDist #Calculate the pole vector controller position.

        poleVectorCtrlName = "ac_ik_" + self.nameBase + "poleVector" #Name for the pole vector control.
        mc.spaceLocator(n=poleVectorCtrlName) #Create a locator for the pole vector.

        poleVectorCtrlGrpName = poleVectorCtrlName + "_grp" #Create a group name for the pole vector.
        mc.group(poleVectorCtrlName, n = poleVectorCtrlGrpName) #Group the locator.

        mc.setAttr(f"{poleVectorCtrlGrpName}.translate", poleVectorCtrlLoc.x, poleVectorCtrlLoc.y, poleVectorCtrlLoc.z, type="double3") #Sets the position of the pole vector control.
        mc.poleVectorConstraint(poleVectorCtrlName, ikHandleName) #Constrain the IK Handle to the pole vector.

        mc.parent(ikHandleName, endIKCtrl) #Parents the IK handle under the IK controller.
        mc.setAttr(f"{ikHandleName}.v", 0) #Hides the IK handle.

        mc.connectAttr(f"{ikFkBlendController}. {ikFkBlendAttrName}", f"{ikHandleName}.ikBlend") #Connects the blend attribute to the IK handle.
        mc.connectAttr(f"{ikFkBlendController}. {ikFkBlendAttrName}", f"{endIKCtrlGrp}.v") #Controls the IK controller's visibility.
        mc.connectAttr(f"{ikFkBlendController}. {ikFkBlendAttrName}", f"{poleVectorCtrlGrpName}.v") #Controls the pole vector's visibility.

        reverseNodeName = f"{self.nameBase}_reverse" #Name for the reverse node in the node editor.
        mc.createNode("reverse", n=reverseNodeName) #Creates the reverse node in the node editor.

        mc.connectAttr(f"{ikFkBlendController}. {ikFkBlendAttrName}", f"{reverseNodeName}.inputX") #Connects the blend attribute to the reverse node input.
        mc.connectAttr(f"{reverseNodeName}.outputX", f"{rootCtrlGrp}.v") #Uses the reverse output to control the FK visibility.

        orientConstraint = None #Initializes the orient constraint variable.
        wristConnections = mc.listConnections(endJnt) #Gets all the connections to the end joint.
        for connection in wristConnections: #Loops through the connections.
            if mc.objectType(connection) == "orientConstraint": #Checks if it's an orient constraint.
                orientConstraint = connection #Stores it
                break
        mc.connectAttr(f"{ikFkBlendController}.{ikFkBlendAttrName}", f"{orientConstraint}.{endIKCtrl}W1") #Connects the IK weight.
        mc.connectAttr(f"{reverseNodeName}.outputX", f"{orientConstraint}.{endCtrl}W0") #Connects the FK weight.

        topGrpName = f"{self.nameBase}_rig_grp" #Name for the top-level group.
        mc.group(n=topGrpName, empty=True) #Creates an empty group.

        mc.parent(rootCtrlGrp, topGrpName) #Parents the FK controls under the top group.
        mc.parent(ikFkBlendCtrlControllerGrp, topGrpName) #Parents the blend control group.
        mc.parent(endIKCtrlGrp, topGrpName) #Parents the IK Control group.
        mc.parent(poleVectorCtrlGrpName, topGrpName) #Parents the pole vector group.

        #HW: Add color override for the topGrpName to be self.controllerColorRGB.
        mc.setAttr(f"{topGrpName}.overrideEnabled", 1) #Enables color override.
        mc.setAttr(f"{topGrpName}.overrideRGBColors", 1) #Uses the RGB color mode.

        mc.setAttr(f"{topGrpName}.overrideColorR", self.controllerColorRGB[0]) #Sets the red channel.
        mc.setAttr(f"{topGrpName}.overrideColorG", self.controllerColorRGB[1]) #Sets the green channel.
        mc.setAttr(f"{topGrpName}.overrideColorB", self.controllerColorRGB[2]) #Sets the blue channel.

class LimbRiggerWidget(MayaWidget):

    def __init__(self):
        super().__init__() #Initializes the parent widget.
        self.setWindowTitle("Limb Rigger") #Sets the window title.
        self.rigger = LimbRigger() #Creates the LimbRigger instance.
        self.masterLayout = QVBoxLayout() #This is the Main vertical layout.
        self.setLayout(self.masterLayout) #Assigns the layout to the widget.
        self.controlColorRGB = [0,0,0] #Stores the selected color.

        self.masterLayout.addWidget(QLabel("Select the 3 joints of the limb, from base to end, and then: ")) #This is the instruction label for the widget.

        self.infoLayout = QHBoxLayout() #Horizontal layout for the inputs.
        self.masterLayout.addLayout(self.infoLayout) #Adds to the main layout.
        self.infoLayout.addWidget(QLabel("Name Base:")) #The label for the name input.

        self.nameBaseLineEdit = QLineEdit() #This is a text input field.
        self.infoLayout.addWidget(self.nameBaseLineEdit) #Adds to the layout.

        self.setNameBaseBtn = QPushButton("Set Name Base") #This is the button to set the name(s).
        self.setNameBaseBtn.clicked.connect(self.SetNameBaseBtnClicked) #Connects the button to its function.
        self.infoLayout.addWidget(self.setNameBaseBtn) #Adds the button to the layout.

        #Add a color pick widget to the self.masterLayout 
        self.masterLayout.addWidget(QLabel("Base Color:")) #This is the label for color selection.

        self.controlColorBtn = QPushButton("Select Color") #This is the button to open the color picker.
        self.controlColorBtn.clicked.connect(self.controlColorBtnClicked) #Connects to the rigging function.
        self.masterLayout.addWidget (self.controlColorBtn) #Adds the button to the layout.

        self.rigLimbBtn = QPushButton("Rig Limb") #This is the button to trigger the rigging.
        self.rigLimbBtn.clicked.connect(self.RigLimbBtnClicked) #Connects to the rigging function.
        self.masterLayout.addWidget(self.rigLimbBtn) #Adds the button to the layout.


    #Listen for Color Change and connect to a function.
    def controlColorBtnClicked(self):
        pickedColor = QColorDialog().getColor() #Opens the color picker dialog.
        self.rigger.controllerColorRGB[0] = pickedColor.redF() #Stores the red value in RGB.
        self.rigger.controllerColorRGB[1] = pickedColor.greenF() #Stores the green value in RGB.
        self.rigger.controllerColorRGB[2] = pickedColor.blueF() #Stores the blue value in RGB.
        print(self.rigger.controllerColorRGB) #Prints the selected color.

        #The function needs to update the color of the limbRigger: self.rigger.controlColorRGB.


    def SetNameBaseBtnClicked(self):
        self.rigger.SetNameBase(self.nameBaseLineEdit.text()) #Passes the text input to the rigger.

    def RigLimbBtnClicked(self):
        self.rigger.RigLimb() #This triggers the rigging process.


    def GetWidgetHash(self):
        return "4067fcd8bf8e146af389a6de3aff0f88f88668684ed0aa0944d96e6b3b94b3e8" #Returns the unique identifier.

def Run():
    limbRiggerWidget = LimbRiggerWidget() #Creates the widget instance.
    limbRiggerWidget.show() #Displays the UI Window.

Run() #Executes the tool.