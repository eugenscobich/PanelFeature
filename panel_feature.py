# -*- coding: utf-8 -*-
import os
import FreeCAD as App
import Part

try:
    import FreeCADGui as Gui
    from pivy import coin
except Exception:
    Gui = None
    coin = None


def _clamp01(x: float) -> float:
    return 0.0 if x < 0.0 else (1.0 if x > 1.0 else x)


def _to_rgb3(color_prop):
    try:
        r, g, b = color_prop[0], color_prop[1], color_prop[2]
        return (_clamp01(float(r)), _clamp01(float(g)), _clamp01(float(b)))
    except Exception:
        return (0.8, 0.8, 0.8)


def _safe_path(p):
    if not p:
        return ""
    try:
        p = str(p)
    except Exception:
        return ""
    return p.strip()


def _file_exists(p):
    p = _safe_path(p)
    return bool(p) and os.path.isfile(p)


def _make_face_sep(face_coords, rgb, texture_path=""):
    sep = coin.SoSeparator()

    mat = coin.SoMaterial()
    mat.diffuseColor.setValue(rgb[0], rgb[1], rgb[2])
    sep.addChild(mat)

    if _file_exists(texture_path):
        tex = coin.SoTexture2()
        tex.filename = _safe_path(texture_path)
        sep.addChild(tex)

        tcoord = coin.SoTextureCoordinate2()
        tcoord.point.setValues(
            0, 4,
            [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]
        )
        sep.addChild(tcoord)

    coords = coin.SoCoordinate3()
    coords.point.setValues(0, 4, face_coords)
    sep.addChild(coords)

    fs = coin.SoFaceSet()
    fs.numVertices.setValue(4)
    sep.addChild(fs)

    return sep


class PanelFeatureProxy:
    def __init__(self, obj):
        obj.Proxy = self
        self._busy = False
        self._init_properties(obj)

    def _init_properties(self, obj):
        obj.addProperty("App::PropertyLength", "Length", "Dimensions", "Panel length (X).")
        obj.addProperty("App::PropertyLength", "Width", "Dimensions", "Panel width (Y).")
        obj.addProperty("App::PropertyLength", "Thickness", "Dimensions", "Panel thickness (Z).")
        obj.Length = App.Units.Quantity("200 mm")
        obj.Width = App.Units.Quantity("400 mm")
        obj.Thickness = App.Units.Quantity("18 mm")

        obj.addProperty("App::PropertyColor", "BaseColor", "Appearance", "Top face color (Length x Width).")
        obj.addProperty("App::PropertyBool", "ColorForBothSides", "Appearance", "If true, bottom face uses Color/Texture too.")
        obj.addProperty("App::PropertyColor", "Color", "Appearance", "Color used for 'colored' faces (or replaced by Texture).")
        obj.addProperty("App::PropertyPath", "Texture", "Appearance", "Optional texture for 'colored' faces (view only).")
        obj.BaseColor = (0.5, 0.5, 0.5)   # gray
        obj.ColorForBothSides = True
        obj.Color = (1.0, 1.0, 1.0)       # white
        obj.Texture = ""

        obj.addProperty("App::PropertyBool", "ABSL1", "ABS", "ABS on L1 (Length x Thickness).")
        obj.addProperty("App::PropertyBool", "ABSL2", "ABS", "ABS on L2 (Length x Thickness).")
        obj.addProperty("App::PropertyBool", "ABSW1", "ABS", "ABS on W1 (Width x Thickness).")
        obj.addProperty("App::PropertyBool", "ABSW2", "ABS", "ABS on W2 (Width x Thickness).")
        obj.addProperty("App::PropertyLength", "ABSThickness", "ABS", "ABS thickness (informational).")
        obj.addProperty("App::PropertyPath", "ABSTexture", "ABS", "Optional texture for ABS faces (view only).")
        obj.addProperty("App::PropertyColor", "MissingABSColor", "ABS", "Color for side faces without ABS.")
        obj.ABSL1 = True
        obj.ABSL2 = True
        obj.ABSW1 = True
        obj.ABSW2 = True
        obj.ABSThickness = App.Units.Quantity("0.5 mm")
        obj.ABSTexture = ""
        obj.MissingABSColor = (1.0, 0.0, 0.0)  # red

    def execute(self, obj):
        L = float(obj.Length)
        W = float(obj.Width)
        T = float(obj.Thickness)

        if L <= 0 or W <= 0 or T <= 0:
            obj.Shape = Part.Shape()
            return

        obj.Shape = Part.makeBox(L, W, T)

    def onChanged(self, obj, prop):
        if self._busy:
            return
        try:
            if hasattr(obj, "State") and ("Restore" in obj.State):
                return
        except Exception:
            pass

        dims = {"Length", "Width", "Thickness"}
        visuals = {
            "BaseColor", "ColorForBothSides", "Color", "Texture",
            "ABSL1", "ABSL2", "ABSW1", "ABSW2",
            "ABSThickness", "ABSTexture", "MissingABSColor",
        }

        if prop in dims:
            self._busy = True
            try:
                obj.touch()
                if obj.Document:
                    obj.Document.recompute()
            finally:
                self._busy = False
        elif prop in visuals:
            try:
                vp = obj.ViewObject.Proxy
                if vp and hasattr(vp, "updateVisual"):
                    vp.updateVisual(obj.ViewObject)
            except Exception:
                pass


class ViewProviderPanelFeature:
    def __init__(self, vobj):
        vobj.Proxy = self
        self.root = None

    def attach(self, vobj):
        if coin is None:
            return
        self.root = coin.SoSeparator()
        vobj.RootNode.addChild(self.root)
        self.updateVisual(vobj)

    def updateData(self, obj, prop):
        try:
            self.updateVisual(obj.ViewObject)
        except Exception:
            pass

    def onChanged(self, vobj, prop):
        if prop in ("Visibility",):
            return
        self.updateVisual(vobj)

    def _quads(self, L, W, T):
        top = [(0, 0, T), (L, 0, T), (L, W, T), (0, W, T)]
        bottom = [(0, 0, 0), (0, W, 0), (L, W, 0), (L, 0, 0)]
        l1 = [(0, 0, 0), (L, 0, 0), (L, 0, T), (0, 0, T)]      # Y=0
        l2 = [(0, W, 0), (0, W, T), (L, W, T), (L, W, 0)]      # Y=W
        w1 = [(0, 0, 0), (0, 0, T), (0, W, T), (0, W, 0)]      # X=0
        w2 = [(L, 0, 0), (L, W, 0), (L, W, T), (L, 0, T)]      # X=L
        return {"top": top, "bottom": bottom, "l1": l1, "l2": l2, "w1": w1, "w2": w2}

    def updateVisual(self, vobj):
        if coin is None or self.root is None:
            return
        obj = vobj.Object
        if obj is None:
            return

        self.root.removeAllChildren()

        L = float(obj.Length)
        W = float(obj.Width)
        T = float(obj.Thickness)
        if L <= 0 or W <= 0 or T <= 0:
            return

        quads = self._quads(L, W, T)

        base_rgb = _to_rgb3(obj.BaseColor)
        color_rgb = _to_rgb3(obj.Color)
        missing_rgb = _to_rgb3(obj.MissingABSColor)

        texture = _safe_path(obj.Texture)
        abs_texture = _safe_path(obj.ABSTexture)

        # Top (LxW): BaseColor
        self.root.addChild(_make_face_sep(quads["top"], base_rgb, texture_path=""))

        # Bottom (LxW): Color (or Texture) if ColorForBothSides
        if bool(obj.ColorForBothSides):
            self.root.addChild(_make_face_sep(quads["bottom"], color_rgb, texture_path=texture))
        else:
            self.root.addChild(_make_face_sep(quads["bottom"], missing_rgb, texture_path=""))

        def add_side(face_key, abs_enabled: bool):
            if abs_enabled:
                if _file_exists(abs_texture):
                    self.root.addChild(_make_face_sep(quads[face_key], color_rgb, texture_path=abs_texture))
                else:
                    self.root.addChild(_make_face_sep(quads[face_key], color_rgb, texture_path=""))
            else:
                self.root.addChild(_make_face_sep(quads[face_key], missing_rgb, texture_path=""))

        # Side faces:
        # L1/L2 are (Length x Thickness)
        add_side("l1", bool(obj.ABSL1))
        add_side("l2", bool(obj.ABSL2))
        # W1/W2 are (Width x Thickness)
        add_side("w1", bool(obj.ABSW1))
        add_side("w2", bool(obj.ABSW2))

    def __getstate__(self):
        return None

    def __setstate__(self, _state):
        return None


def create_panel_feature(name="PanelFeature"):
    doc = App.ActiveDocument
    if doc is None:
        doc = App.newDocument()

    obj = doc.addObject("Part::FeaturePython", name)
    PanelFeatureProxy(obj)

    if Gui is not None:
        ViewProviderPanelFeature(obj.ViewObject)

    doc.recompute()
    return obj