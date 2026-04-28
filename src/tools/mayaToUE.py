from PySide6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout
from PySide2.QtWidgets import QLineEdit, QPushButton
from core.MayaWidget import MayaWidget
import maya.cmds as mc

class MayaToUE:
    def __init__(self):
        self.meshes = []
        self.rootJnt = ""
        self.clips = []
        
    def SetSelectedAsMesh(self):
        selection = mc.ls(sl=True)
        if not selection:
            raise Exception("please select the mesh(es) of the rig")
        
        for obj in selection:
            shapes = mc.listRelatives(obj, s=True)
            if not shapes or mc.objectType(shapes[0]) != "mesh":
                raise Exception(f"{obj} is not a mesh, please select the mesh(es) of the rig")
            
        self.meshes = selection


class MayaToUEWidget(MayaWidget):
    def __init__(self):
        super().__init__()
        self.mayaToUE = MayaToUE()
        self.setWindowTitle("MayaToUE")

        self.masterLayout = QVBoxLayout()
        self.setlayout(self.masterLayout)

        meshSelectLayout = QHBoxLayout()
        self.masterLayout.addLayout(meshSelectLayout)
        meshSelectLayout.addWidget(QLabel("Mesh:"))
        self.meshSelectLineEdit = QLineEdit()
        self.meshSelectLineEdit.setEnabled(False)
        meshSelectBtn = QPushButton("<<<")
        meshSelectLayout.addWidget(meshSelectBtn)
        meshSelectBtn.clicked.connect(self.meshSelectBtnClicked)

    def MeshSelectNuttonClicked(self):
        self.mayaToUE.SetSelectedAsMesh()
        self.meshSelectLineEdit.setText(",".join(self.mayaToUE.meshes))

    def GetWidgetHAsh(self):
        return "38f2e9e93008b5efd85c5b1188f6595e61fba338533918751acf94f163935240"
    
def Run():
    mayaToUEWidget = MayaToUEWidget()
    mayaToUEWidget.show()

Run()