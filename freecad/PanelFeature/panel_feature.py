import FreeCAD as App
import FreeCADGui as Gui
import Part
from pivy import coin

# -----------------------------
# Helpers
# -----------------------------
def _rgb(c):
    return (float(c[0]), float(c[1]), float(c[2]))

def remove_child_part(parentObject, name):
    for child in parentObject.Group:
        if getattr(child, "Name", "") == name:
            parentObject.removeObject(child)
            return

def get_or_create_child_part(doc, parentObject, name):
    for child in parentObject.Group:
        if getattr(child, "Name", "") == name:
            return child
    obj = doc.addObject("Part::Feature", name)
    parentObject.addObject(obj)
    return obj

def _clear_texture(obj):
    try:
        root = obj.ViewObject.RootNode
        i = 0
        while i < root.getNumChildren():
            node = root.getChild(i)
            if isinstance(node, coin.SoTexture2):
                root.removeChild(i)
                continue  # don't increment index after removal
            i += 1
    except Exception as e:
        App.Console.PrintError(f"clear texture failed: {e}\n")

def _set_texture(obj, texture_path):
    texture_path = (texture_path or "").strip()
    try:
        App.Console.PrintMessage(f"apply texture: {texture_path}\n")

        _set_color(obj, (1.0, 1.0, 1.0))

        rootnode = obj.ViewObject.RootNode
        tex =  coin.SoTexture2()
        tex.filename = texture_path
        rootnode.insertChild(tex, 1)
    except Exception as e:
        App.Console.PrintError(f"apply texture failed: {e}\n")
        pass

def _set_color(obj, rgb):
    # For a single-face thin solid, ShapeColor is enough
    try:
        _clear_texture(obj)
        obj.ViewObject.ShapeColor = rgb
    except Exception:
        pass

# -----------------------------
# Master FeaturePython
# -----------------------------
class PanelFeatureProxy:
    def __init__(self, obj, name):
        obj.Proxy = self
        self.name = name
        self._init_properties(obj)

    def _init_properties(self, obj):
        App.Console.PrintMessage(f"Init: {self.name}\n")
        # Appearance
        obj.addProperty("App::PropertyColor", "BaseColor", "Appearance", "Color of base material.")
        obj.addProperty("App::PropertyColor", "FrontColor", "Appearance", "Color of front face.")
        obj.addProperty("App::PropertyFile", "FrontTexture", "Appearance", "Optional texture for Front face (view only).")
        obj.addProperty("App::PropertyBool", "BackAppearanceAsFront", "Appearance", "If true, Back face uses Front Appearance.")

        obj.BaseColor = (0.588, 0.435, 0.2)
        obj.FrontColor = (0.5, 0.5, 0.5)
        obj.FrontTexture = ""
        obj.BackAppearanceAsFront = True

        # ABS
        obj.addProperty("App::PropertyLength", "ABSThickness", "ABS", "ABS thickness.")
        obj.addProperty("App::PropertyBool", "ABSL1Top", "ABS", "ABS on L1Top (Front Length x Thickness).")
        obj.addProperty("App::PropertyBool", "ABSL2Bottom", "ABS", "ABS on L2Bottom (Back Length x Thickness).")
        obj.addProperty("App::PropertyBool", "ABSW1Left", "ABS", "ABS on W1Left (Left Width x Thickness).")
        obj.addProperty("App::PropertyBool", "ABSW2Right", "ABS", "ABS on W2Right (Right Width x Thickness).")
        obj.addProperty("App::PropertyColor", "ABSColor", "ABS", "ABS Color.")
        obj.addProperty("App::PropertyFile", "ABSTexture", "ABS", "Optional texture for ABS faces (view only).")

        obj.ABSThickness = App.Units.Quantity("0.4 mm")
        obj.ABSL1Top = True
        obj.ABSL2Bottom = True
        obj.ABSW1Left = True
        obj.ABSW2Right = True
        obj.ABSColor = obj.FrontColor
        obj.ABSTexture = ""

        # Dimensions
        obj.addProperty("App::PropertyLength", "Length", "Dimensions", "Panel length (X).")
        obj.addProperty("App::PropertyLength", "Width", "Dimensions", "Panel width (Y).")
        obj.addProperty("App::PropertyLength", "Thickness", "Dimensions", "Panel thickness (Z).")
        obj.Length = App.Units.Quantity("200 mm")
        obj.Width = App.Units.Quantity("400 mm")
        obj.Thickness = App.Units.Quantity("18 mm")


    def execute(self, obj):
        global l1_top, l2_bottom, w1_left, w2_right, back

        App.Console.PrintMessage(f"Execute: {self.name}\n")
        l = float(obj.Length)
        w = float(obj.Width)
        t = float(obj.Thickness)

        abs_t = float(obj.ABSThickness)
        abs_l1_top = bool(obj.ABSL1Top)
        abs_l2_bottom = bool(obj.ABSL2Bottom)
        abs_w1_left = bool(obj.ABSW1Left)
        abs_w2_right = bool(obj.ABSW2Right)

        App.Console.PrintMessage(f"ABS configuration: {abs_t}x{abs_l1_top}x{abs_l2_bottom}x{abs_w1_left}x{abs_w2_right}\n")

        back_appearance_as_front = bool(obj.BackAppearanceAsFront)

        if l <= 0 or w <= 0 or t <= 0 or abs_t <= 0:
            App.Console.PrintMessage(f"Could not apply dimensions: {l}x{w}x{t}x{abs_t}\n")
            obj.Shape = Part.Shape()
            return

        doc = obj.Document

        skin = 0.01 #mm

        front = get_or_create_child_part(doc, obj.getParent(), f"{self.name}_Front")
        back = get_or_create_child_part(doc, obj.getParent(), f"{self.name}_Back")
        l1_top = get_or_create_child_part(doc, obj.getParent(), f"{self.name}_ABS_L1_Top")
        l2_bottom = get_or_create_child_part(doc, obj.getParent(), f"{self.name}_ABS_L2_Bottom")
        w1_left = get_or_create_child_part(doc, obj.getParent(), f"{self.name}_ABS_W1_Left")
        w2_right = get_or_create_child_part(doc, obj.getParent(), f"{self.name}_ABS_W2_Right")

        base_l = l
        base_w = w
        base_t = t - skin
        base_x = 0
        base_y = 0
        base_z = 0
        if abs_l1_top:
            base_w -= abs_t
        if abs_l2_bottom:
            base_w -= abs_t
            base_y += abs_t
        if abs_w1_left:
            base_l -= abs_t
            base_x += abs_t
        if abs_w2_right:
            base_l -= abs_t
        if back_appearance_as_front:
            base_z += skin
            base_t -= skin
        App.Console.PrintMessage(f"Create base shape: {base_l}x{base_w}x{base_t}x{base_x}x{base_y}x{base_z}\n")
        obj.Shape = Part.makeBox(base_l, base_w, base_t, App.Vector(base_x, base_y, base_z))

        front_l = base_l
        front_w = base_w
        front_t = skin
        front_x = base_x
        front_y = base_y
        front_z = base_z + base_t
        front.Shape = Part.makeBox(front_l, front_w, front_t, App.Vector(front_x, front_y, front_z))
        
        if back_appearance_as_front:
            back_l = base_l
            back_w = base_w
            back_t = skin
            back_x = base_x
            back_y = base_y
            back_z = 0
            back.Shape = Part.makeBox(back_l, back_w, back_t, App.Vector(back_x, back_y, back_z))
            back.ViewObject.Visibility = True
        else:
            back.ViewObject.Visibility = False
            back.Shape = Part.Shape()

        if abs_l1_top:
            l1_top_l = base_l
            l1_top_w = abs_t
            l1_top_t = base_z + base_t + skin
            l1_top_x = base_x
            l1_top_y = base_y + base_w
            l1_top_z = 0
            l1_top.Shape = Part.makeBox(l1_top_l, l1_top_w, l1_top_t, App.Vector(l1_top_x, l1_top_y, l1_top_z))
            l1_top.ViewObject.Visibility = True
        else:
            l1_top.ViewObject.Visibility = False
            l1_top.Shape = Part.Shape()

        if abs_l2_bottom:
            l2_bottom_l = base_l
            l2_bottom_w = abs_t
            l2_bottom_t = base_z + base_t + skin
            l2_bottom_x = base_x
            l2_bottom_y = 0
            l2_bottom_z = 0
            l2_bottom.Shape = Part.makeBox(l2_bottom_l, l2_bottom_w, l2_bottom_t, App.Vector(l2_bottom_x, l2_bottom_y, l2_bottom_z))
            l2_bottom.ViewObject.Visibility = True
        else:
            l2_bottom.ViewObject.Visibility = False
            l2_bottom.Shape = Part.Shape()

        if abs_w1_left:
            w1_left_l = abs_t
            w1_left_w = base_y + base_w + (abs_t if abs_l1_top else 0)
            w1_left_t = base_z + base_t + skin
            w1_left_x = 0
            w1_left_y = 0
            w1_left_z = 0
            w1_left.Shape = Part.makeBox(w1_left_l, w1_left_w, w1_left_t, App.Vector(w1_left_x, w1_left_y, w1_left_z))
            w1_left.ViewObject.Visibility = True
        else:
            w1_left.ViewObject.Visibility = False
            w1_left.Shape = Part.Shape()

        if abs_w2_right:
            w2_right_l = abs_t
            w2_right_w = base_y + base_w + (abs_t if abs_l1_top else 0)
            w2_right_t = base_z + base_t + skin
            w2_right_x = base_x + base_l
            w2_right_y = 0
            w2_right_z = 0
            w2_right.Shape = Part.makeBox(w2_right_l, w2_right_w, w2_right_t, App.Vector(w2_right_x, w2_right_y, w2_right_z))
            w2_right.ViewObject.Visibility = True
        else:
            w2_right.ViewObject.Visibility = False
            w2_right.Shape = Part.Shape()



        # Appearance rules
        base_rgb = _rgb(obj.BaseColor)
        front_rgb = _rgb(obj.FrontColor)
        abs_rgb = _rgb(obj.ABSColor)
        App.Console.PrintMessage(f"Base Color: {base_rgb}\n")
        _set_color(obj, base_rgb)

        # Front: texture if provided, else base color
        tex_front = (obj.FrontTexture or "").strip()
        if tex_front:
            _set_texture(front, tex_front)
            if back_appearance_as_front:
                _set_texture(back, tex_front)
        else:
            _set_color(front, front_rgb)
            if back_appearance_as_front:
                _set_color(back, front_rgb)

        # Sides: ABS texture if provided AND that side has ABS; otherwise color
        tex_abs = (obj.ABSTexture or "").strip()
        App.Console.PrintMessage(f"ABS Texture: {tex_abs}\n")
        if tex_abs:
            if abs_l1_top:
                _set_texture(l1_top, tex_abs)
            if abs_l2_bottom:
                _set_texture(l2_bottom, tex_abs)
            if abs_w1_left:
                _set_texture(w1_left, tex_abs)
            if abs_w2_right:
                _set_texture(w2_right, tex_abs)
        else:
            if abs_l1_top:
                _set_color(l1_top, abs_rgb)
            if abs_l2_bottom:
                _set_color(l2_bottom, abs_rgb)
            if abs_w1_left:
                _set_color(w1_left, abs_rgb)
            if abs_w2_right:
                _set_color(w2_right, abs_rgb)

    def onChanged(self, obj, prop):
        App.Console.PrintMessage(f"OnChange: {self.name}\n")
        obj.Document.recompute()

class ViewProviderPanelFeature:
    def __init__(self, vobj):
        vobj.Proxy = self

    def attach(self, vobj):
        pass

    def updateData(self, obj, prop):
        # Most updates handled in Proxy; keep minimal
        pass

    def onChanged(self, vobj, prop):
        pass


def create_panel_feature(name="Panel"):
    doc = App.ActiveDocument
    if doc is None:
        doc = App.newDocument()

    container = doc.addObject("App::Part", name)
    basePart = doc.addObject("Part::FeaturePython", f"{container.Name}_Base")
    container.addObject(basePart)

    PanelFeatureProxy(basePart, container.Name)

    if Gui is not None:
        ViewProviderPanelFeature(basePart.ViewObject)

    doc.recompute()
    return basePart