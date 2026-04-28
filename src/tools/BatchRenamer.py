from core.MayaWidget import MayaWidget
from PySide6.QtWidgets import (QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QSpinBox, QCheckBox)
import maya.cmds as mc

import importlib
import core.MayaUtilities
importlib.reload(core.MayaUtilities)

class BatchRenamer:
    def __init__(self):
        self.baseName = "object"
        self.startNumber = 1
        self.padding = 2
        self.useUnderscore = True

    def RenameSelected(self):
        selectedObjects = mc.ls(sl=True)

        if not selectedObjects:
            mc.warning("Nothing is selected. Please select one or more objects to rename.")
            return

        if self.baseName.strip() == "":
            mc.warning("Base name is empty. Please type a name before renaming.")
            return

        if self.baseName[0].isdigit():
            mc.warning("Object names should not start with a number. Please use a letter first.")
            return

        renamedObjects = []

        for index, obj in enumerate(selectedObjects):
            number = self.startNumber + index
            numberText = str(number).zfill(self.padding)

            if self.useUnderscore:
                newName = f"{self.baseName}_{numberText}"
            else:
                newName = f"{self.baseName}{numberText}"

            renamedObj = mc.rename(obj, newName)
            renamedObjects.append(renamedObj)

        mc.inViewMessage(
            amg=f"Renamed <hl>{len(renamedObjects)}</hl> object(s).",
            pos="midCenter",
            fade=True
        )

        print("Renamed objects:")
        for obj in renamedObjects:
            print(obj)


class BatchRenamerWidget(MayaWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Batch Renamer")

        self.renamer = BatchRenamer()

        self.masterLayout = QVBoxLayout()
        self.setLayout(self.masterLayout)

        self.infoLabel = QLabel(
            "Batch Renamer\n"
            "Select objects, choose a base name, then rename everything at once."
        )
        self.masterLayout.addWidget(self.infoLabel)

        self.nameLayout = QHBoxLayout()
        self.masterLayout.addLayout(self.nameLayout)

        self.nameLayout.addWidget(QLabel("Base Name:"))

        self.baseNameLineEdit = QLineEdit()
        self.baseNameLineEdit.setText("object")
        self.baseNameLineEdit.setPlaceholderText("Example: rock, joint, prop")
        self.nameLayout.addWidget(self.baseNameLineEdit)

        self.numberLayout = QHBoxLayout()
        self.masterLayout.addLayout(self.numberLayout)

        self.numberLayout.addWidget(QLabel("Start Number:"))

        self.startNumberSpinBox = QSpinBox()
        self.startNumberSpinBox.setMinimum(0)
        self.startNumberSpinBox.setMaximum(9999)
        self.startNumberSpinBox.setValue(1)
        self.numberLayout.addWidget(self.startNumberSpinBox)

        self.numberLayout.addWidget(QLabel("Padding:"))

        self.paddingSpinBox = QSpinBox()
        self.paddingSpinBox.setMinimum(1)
        self.paddingSpinBox.setMaximum(6)
        self.paddingSpinBox.setValue(2)
        self.numberLayout.addWidget(self.paddingSpinBox)

        self.useUnderscoreCheckBox = QCheckBox("Use underscore before number")
        self.useUnderscoreCheckBox.setChecked(True)
        self.masterLayout.addWidget(self.useUnderscoreCheckBox)

        self.hintLabel = QLabel("Example result: object_01, object_02, object_03")
        self.masterLayout.addWidget(self.hintLabel)

        self.renameBtn = QPushButton("Rename Selected Objects")
        self.renameBtn.clicked.connect(self.RenameBtnClicked)
        self.masterLayout.addWidget(self.renameBtn)

    def RenameBtnClicked(self):
        self.renamer.baseName = self.baseNameLineEdit.text().strip()
        self.renamer.startNumber = self.startNumberSpinBox.value()
        self.renamer.padding = self.paddingSpinBox.value()
        self.renamer.useUnderscore = self.useUnderscoreCheckBox.isChecked()

        self.renamer.RenameSelected()

    def GetWidgetHash(self):
        return "564dbd37fa903560581445a41f8ea63dbb2b2ae9caade994f4d0212a470a8652"


def Run():
    batchRenamerWidget = BatchRenamerWidget()
    batchRenamerWidget.show()


Run()