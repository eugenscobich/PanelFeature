import os
import FreeCAD as App
import FreeCADGui as Gui
import Part

class PanelFeatureProxy:
    def __init__(self, obj):
        obj.Proxy = self
        self._init_properties(obj)

    def _init_properties(self, obj):
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

        obj.addProperty("App::PropertyLength", "Length", "Dimensions", "Panel length (X).")
        obj.addProperty("App::PropertyLength", "Width", "Dimensions", "Panel width (Y).")
        obj.addProperty("App::PropertyLength", "Thickness", "Dimensions", "Panel thickness (Z).")
        obj.Length = App.Units.Quantity("200 mm")
        obj.Width = App.Units.Quantity("400 mm")
        obj.Thickness = App.Units.Quantity("18 mm")

    def execute(self, obj):
        L = float(obj.Length)
        W = float(obj.Width)
        T = float(obj.Thickness)

        if L <= 0 or W <= 0 or T <= 0:
            obj.Shape = Part.Shape()
            return
        App.Console.PrintMessage(f"Making a box of dimension {L}x{W}x{T}\n")
        obj.Shape = Part.makeBox(L, W, T)

    def onChanged(self, obj, prop):
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
            try:
                obj.touch()
                if obj.Document:
                    obj.Document.recompute()
            except Exception:
                pass


def _rgb(c):
    """FreeCAD colors are often (r,g,b) or (r,g,b,a). Return (r,g,b)."""
    return (float(c[0]), float(c[1]), float(c[2]))

def apply_panel_face_colors(obj):
    """
    Colors faces based on obj.BaseColor / obj.Color / obj.MissingABSColor and ABS flags.
    Uses face center-of-mass to map faces to Top/Bottom/L1/L2/W1/W2.
    """
    if not hasattr(obj, "ViewObject") or obj.ViewObject is None:
        return
    sh = getattr(obj, "Shape", None)
    if sh is None or sh.isNull():
        return
    if len(sh.Faces) == 0:
        return

    # Pick your palette
    base = _rgb(obj.BaseColor)                 # top (and optionally bottom)
    generic = _rgb(obj.Color)                  # used for "ABS present" sides (example)
    missing = _rgb(obj.MissingABSColor)        # used for "ABS missing" sides

    # Build a per-face color list in Face order
    face_colors = [generic] * len(sh.Faces)

    # Collect face centers for classification
    centers = []
    for i, f in enumerate(sh.Faces):
        c = f.CenterOfMass
        centers.append((i, c.x, c.y, c.z))

    # Identify faces by extreme center coordinates
    top_i    = max(centers, key=lambda t: t[3])[0]
    bottom_i = min(centers, key=lambda t: t[3])[0]
    x_min_i  = min(centers, key=lambda t: t[1])[0]
    x_max_i  = max(centers, key=lambda t: t[1])[0]
    y_min_i  = min(centers, key=lambda t: t[2])[0]
    y_max_i  = max(centers, key=lambda t: t[2])[0]

    # Top / bottom
    face_colors[top_i] = base
    if bool(obj.ColorForBothSides):
        face_colors[bottom_i] = base

    # Side ABS logic (example mapping):
    # - X sides correspond to "Length x Thickness": ABSL1 / ABSL2
    # - Y sides correspond to "Width  x Thickness": ABSW1 / ABSW2
    face_colors[x_min_i] = generic if bool(obj.ABSL1) else missing
    face_colors[x_max_i] = generic if bool(obj.ABSL2) else missing
    face_colors[y_min_i] = generic if bool(obj.ABSW1) else missing
    face_colors[y_max_i] = generic if bool(obj.ABSW2) else missing

    # Apply to the view provider
    vobj = obj.ViewObject
    vobj.DiffuseColor = face_colors

    # Workaround: in some FreeCAD versions, FeaturePython may not refresh DiffuseColor
    # until it is re-assigned to itself. :contentReference[oaicite:1]{index=1}
    vobj.DiffuseColor = vobj.DiffuseColor

class ViewProviderPanelFeature:
    def __init__(self, vobj):
        vobj.Proxy = self

    def attach(self, vobj):
        pass

    def updateData(self, obj, prop):
        App.Console.PrintMessage("updateData\n")
        if prop in (
                "Shape",
                "BaseColor", "ColorForBothSides", "Color",
                "ABSL1", "ABSL2", "ABSW1", "ABSW2", "MissingABSColor",
        ):
            try:
                apply_panel_face_colors(obj)
            except Exception as e:
                App.Console.PrintWarning(f"apply_panel_face_colors failed: {e}\n")

    def onChanged(self, vobj, prop):
        pass

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