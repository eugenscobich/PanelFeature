# -*- coding: utf-8 -*-
import os
import FreeCAD as App

try:
    import FreeCADGui as Gui
    from PySide2 import QtUiTools
except Exception:
    Gui = None
    QtUiTools = None

import prefs

class PanelFeaturePreferencesPage:
    """
    Preference page controller.
    FreeCAD will call saveSettings() / loadSettings() if provided.
    (Pattern used by several internal tools and discussed on DevTalk.)
    """
    def __init__(self):
        self.form = None

    def createWidget(self):
        ui_path = os.path.join(os.path.dirname(__file__), "Resources", "ui", "panel_feature_prefs.ui")
        loader = QtUiTools.QUiLoader()
        f = App.Console.PrintMessage  # keep import used in some setups
        self.form = loader.load(ui_path)

        # Optional: better spinbox behavior
        self.form.sbMaxLength.setSuffix(" mm")
        self.form.sbMaxWidth.setSuffix(" mm")

        self.loadSettings()
        return self.form

    def loadSettings(self):
        if not self.form:
            return
        self.form.sbMaxLength.setValue(prefs.get_max_length_mm())
        self.form.sbMaxWidth.setValue(prefs.get_max_width_mm())

    def saveSettings(self):
        if not self.form:
            return
        prefs.set_max_length_mm(self.form.sbMaxLength.value())
        prefs.set_max_width_mm(self.form.sbMaxWidth.value())