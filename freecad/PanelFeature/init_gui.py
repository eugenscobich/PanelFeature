import os
import FreeCADGui as Gui
import FreeCAD as App

from freecad.PanelFeature import comands

ICONPATH = os.path.join(os.path.dirname(__file__), "Resources", "Icons")

class PanelFeature(Gui.Workbench):
    """
    class which gets initiated at startup of the gui
    """
    MenuText = "PanelFeature Menu"
    ToolTip = "PanelFeature Tool Tip"
    Icon = os.path.join(ICONPATH, "PanelFeatureWorkbench.svg")
    toolbox = ["Create_Panel_Feature"]

    def Initialize(self):
        App.Console.PrintMessage("Initialize PanelFeature Workbench\n")
        Gui.addCommand("Create_Panel_Feature", comands.CreatePanelFeatureCommand())
        self.appendToolbar("PanelFeature Tools", self.toolbox)
        self.appendMenu("PanelFeature Menu Tools", self.toolbox)

    def Activated(self):
        App.Console.PrintMessage("PanelFeature Workbench activated\n")

    def Deactivated(self):
        App.Console.PrintMessage("PanelFeature Workbench deactivated\n")

    def GetClassName(self):
        return "Gui::PythonWorkbench"

Gui.addWorkbench(PanelFeature())