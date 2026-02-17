# -*- coding: utf-8 -*-
import FreeCADGui as Gui
import FreeCAD as App

from panel_feature import create_panel_feature


class CreatePanelFeatureCommand:
    """Toolbar/Menu command"""

    def GetResources(self):
        return {
            "Pixmap": App.getResourceDir() + "Mod/PanelFeature/Resources/icons/create_panel_feature.svg",
            "MenuText": "Create Panel Feature",
            "ToolTip": "Create a parametric panel feature with per-face colors/textures and ABS visualization.",
        }

    def IsActive(self):
        return App.ActiveDocument is not None

    def Activated(self):
        create_panel_feature(name="PanelFeature")


class PanelFeatureWorkbench(Gui.Workbench):
    MenuText = "Panel Feature"
    ToolTip = "Panel Feature"
    Icon = App.getResourceDir() + "Mod/PanelFeature/Resources/icons/panel_feature.svg"

    def Initialize(self):
        Gui.addCommand("Create_Panel_Feature", CreatePanelFeatureCommand())
        self.appendToolbar("Panel Feature", ["Create_Panel_Feature"])
        self.appendMenu("Panel Feature", ["Create_Panel_Feature"])
        Log ('Loading Panel_Feature module... done\n')

    def Activated(self):
        pass

    def Deactivated(self):
        pass


Gui.addWorkbench(PanelFeatureWorkbench())