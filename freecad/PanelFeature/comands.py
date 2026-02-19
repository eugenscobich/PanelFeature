import os
import FreeCADGui as Gui
import FreeCAD as App

from freecad.PanelFeature import panel_feature


ICONPATH = os.path.join(os.path.dirname(__file__), "Resources", "Icons")

class CreatePanelFeatureCommand:
    def GetResources(self):
        return {
            "Pixmap": os.path.join(ICONPATH, "CreatePanelFeature.svg"),
            "MenuText": "Create Panel Feature",
            "ToolTip": "Create a parametric panel feature with per-face colors/textures and ABS visualization.",
        }

    def IsActive(self):
        return App.ActiveDocument is not None

    def Activated(self):
        panel_feature.create_panel_feature(name="Panel")