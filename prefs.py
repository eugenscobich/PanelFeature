# -*- coding: utf-8 -*-
import FreeCAD as App

PARAM_PATH = "User parameter:BaseApp/Preferences/Mod/PanelFeatureAddon"

def param():
    return App.ParamGet(PARAM_PATH)

def get_max_length_mm(default=3000.0) -> float:
    return float(param().GetFloat("MaxLengthMM", float(default)))

def set_max_length_mm(val: float):
    param().SetFloat("MaxLengthMM", float(val))

def get_max_width_mm(default=3000.0) -> float:
    return float(param().GetFloat("MaxWidthMM", float(default)))

def set_max_width_mm(val: float):
    param().SetFloat("MaxWidthMM", float(val))