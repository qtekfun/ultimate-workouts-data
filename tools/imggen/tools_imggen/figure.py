"""Procedural exercise figure engine (side-view filled figure + front-view figure).

WORLD COORDINATES: x grows to the right (the figure faces +x), y grows DOWN, the floor surface is y = FLOOR.
A standing figure has its ankle at (0, 0).  Units are "figure units" (a standing figure is ~290 units tall).

POSE DICT (angles in degrees)
  upward chain  shin, thigh, torso, head : angle from "up", positive towards +x (the facing side)
  arm chain     uarm, farm               : angle from "down", positive towards +x
  far leg       b_thigh, b_shin          : angle from "down", positive towards +x
  optional      ox, oy (ankle position in the world), foot / b_foot (toe direction, degrees, 0 = +x, +down)
Use body(...) to build poses from CONTACT TARGETS (ankle, hip, hand, back ankle) solved with two-bone IK, so feet
sit on the floor and hands sit on the grip.  Poses made by body() remember their targets and are interpolated in
target space (then re-solved), so in-between frames keep the contacts.

SPEC (what a pattern returns, see patterns/__init__.py):
  dict(poses=[A, B, ...], equipment=Gear|None, scene=Gear|None, hilite="quads", cycle=False, hold=(600, 500))

GEAR: Gear(back=, mid=, front=, bounds=) objects; every callable is fn(d, T, P, s) with d = ImageDraw (RGBA),
T = world -> pixel, P = dict of figure points in the world, s = pixels per unit.  Layers, back to front:
scene.back, equipment.back, far leg, near leg + torso + head, torso/leg highlight, equipment.mid, arms + hands,
arm highlight, equipment.front, scene.front.
"""
import math
from PIL import Image, ImageDraw, ImageChops

W = 360
SS = 3
BG = (240, 243, 248)
SKIN = (233, 186, 150)
SKIN_FAR = (212, 166, 132)
SHIRT = (47, 98, 214)
SHIRT_FAR = (38, 80, 182)
SHORTS = (52, 60, 84)
SHORTS_FAR = (42, 49, 70)
SHOE = (222, 229, 244)
HAIR = (60, 44, 38)
HILITE = (255, 120, 20, 175)
FLOORC = (196, 203, 217)
EQUIP = (92, 100, 122)
BENCHC = (120, 128, 150)
METAL = (150, 158, 178)
METAL_D = (118, 126, 146)
PAD = (74, 82, 104)
PAD_L = (96, 106, 130)
RUBBER = (70, 76, 94)
ACCENT = (222, 96, 60)
BANDC = (232, 120, 60)
CABLEC = (60, 66, 84)
MATC = (98, 168, 150)
BALLC = (120, 186, 220)
KBC = (58, 64, 84)
WOODC = (206, 170, 120)
WOODD = (178, 142, 96)

L = dict(shin=70, thigh=76, torso=92, neck=12, head=16, uarm=54, farm=52, foot=24)
FLOOR = 6.0
E = (7.0, 3.2)  # oblique "towards the viewer" vector used for equipment depth


# ----------------------------------------------------------------------------------------------- vectors / IK
def vup(a, n=1.0):
    r = math.radians(a)
    return (math.sin(r) * n, -math.cos(r) * n)


def vdown(a, n=1.0):
    r = math.radians(a)
    return (math.sin(r) * n, math.cos(r) * n)


def add(p, d):
    return (p[0] + d[0], p[1] + d[1])


def sub(p, q):
    return (p[0] - q[0], p[1] - q[1])


def mul(p, k):
    return (p[0] * k, p[1] * k)


def dist(p, q):
    return math.hypot(p[0] - q[0], p[1] - q[1])


def ang_up(p, q):
    """angle (from up, + towards +x) of the vector p -> q"""
    return math.degrees(math.atan2(q[0] - p[0], -(q[1] - p[1])))


def ang_down(p, q):
    return math.degrees(math.atan2(q[0] - p[0], q[1] - p[1]))


def ik2(base, tip, l1, l2, side=1):
    """Two-bone IK. Returns (joint, reachable tip).  side=+1: joint on the left-hand normal of base->tip
    (for a leg standing on the floor and facing +x that is the knee-forward solution)."""
    dx, dy = tip[0] - base[0], tip[1] - base[1]
    d0 = math.hypot(dx, dy) or 1e-6
    d = min(max(d0, abs(l1 - l2) + 0.5), l1 + l2 - 0.01)
    ux, uy = dx / d0, dy / d0
    a = (l1 * l1 - l2 * l2 + d * d) / (2 * d)
    h = math.sqrt(max(l1 * l1 - a * a, 0.0))
    nx, ny = -uy, ux
    joint = (base[0] + ux * a + nx * h * side, base[1] + uy * a + ny * h * side)
    return joint, (base[0] + ux * d, base[1] + uy * d)


def _lerp_val(a, b, t):
    if isinstance(a, (tuple, list)) and isinstance(b, (tuple, list)):
        return tuple(x + (y - x) * t for x, y in zip(a, b))
    if isinstance(a, (int, float)) and isinstance(b, (int, float)) and not isinstance(a, bool):
        return a + (b - a) * t
    return a


def body(ankle=(0.0, 0.0), hip=None, shin=None, thigh=None, torso=0.0, head=None, hand=None, uarm=0.0, farm=0.0,
         back=None, b_thigh=None, b_shin=None, foot=0.0, b_foot=0.0, knee_side=1, elbow_side=1, back_side=1,
         hand_fixed=False, **extra):
    """Build a pose from targets (all in world coordinates).

    legs : hip + ankle -> IK ;  or explicit shin+thigh (FK from the ankle) ;  or hip + explicit shin+thigh
           (the ankle then follows: the hip stays where it is).
    arm  : hand target (IK from the shoulder) or explicit uarm/farm.
    back : far-leg ankle target (IK from the hip), or explicit b_thigh/b_shin.
    """
    spec = dict(ankle=ankle, hip=hip, shin=shin, thigh=thigh, torso=torso, head=head, hand=hand, uarm=uarm,
                farm=farm, back=back, b_thigh=b_thigh, b_shin=b_shin, foot=foot, b_foot=b_foot,
                knee_side=knee_side, elbow_side=elbow_side, back_side=back_side)
    spec.update(extra)
    spec = {k: v for k, v in spec.items() if v is not None}
    pose = _solve(spec)
    pose["_spec"] = spec
    return pose


def _solve(sp):
    ank = sp.get("ankle", (0.0, 0.0))
    hip = sp.get("hip")
    if "shin" in sp and "thigh" in sp:
        kn = add((0, 0), vup(sp["shin"], L["shin"]))
        hl = add(kn, vup(sp["thigh"], L["thigh"]))
        if hip is not None:
            ank = (hip[0] - hl[0], hip[1] - hl[1])
        else:
            hip = (ank[0] + hl[0], ank[1] + hl[1])
        shin, thigh = sp["shin"], sp["thigh"]
    else:
        knee, hip_eff = ik2(ank, hip, L["shin"], L["thigh"], sp.get("knee_side", 1))
        shin, thigh = ang_up(ank, knee), ang_up(knee, hip_eff)
        miss_leg = dist(hip_eff, hip)
        hip = hip_eff
    torso = sp.get("torso", 0.0)
    shoulder = add(hip, vup(torso, L["torso"]))
    pose = dict(shin=shin, thigh=thigh, torso=torso, head=sp.get("head", torso), ox=ank[0], oy=ank[1],
                foot=sp.get("foot", 0.0))
    if "elbow_rel" in sp:
        # arm given by projected elbow / hand offsets (allows foreshortening of arms that swing towards the viewer)
        er = sp["elbow_rel"]
        he = sp.get("hand_e", (0.0, L["farm"]))
        pose["uarm"] = math.degrees(math.atan2(er[0], er[1]))
        pose["uscale"] = max(0.02, math.hypot(*er) / L["uarm"])
        pose["farm"] = math.degrees(math.atan2(he[0], he[1]))
        pose["fscale"] = max(0.02, math.hypot(*he) / L["farm"])
        sp = dict(sp)
        sp.pop("hand", None)
        sp.pop("hand_rel", None)
        sp.pop("hand_t", None)
        sp["_arm_done"] = True
    tgt = None
    if sp.get("_arm_done"):
        pass
    elif "hand_rel" in sp:
        tgt = add(shoulder, sp["hand_rel"])
    elif "hand_t" in sp:
        tgt = torso_pt(hip, torso, sp["hand_t"][0], sp["hand_t"][1])
    elif "hand" in sp:
        tgt = sp["hand"]
    if sp.get("_arm_done"):
        pass
    elif tgt is not None:
        el, wr = ik2(shoulder, tgt, L["uarm"], L["farm"], sp.get("elbow_side", 1))
        pose["uarm"], pose["farm"] = ang_down(shoulder, el), ang_down(el, wr)
        pose["_miss"] = dist(wr, tgt)
    else:
        pose["uarm"], pose["farm"] = sp.get("uarm", 0.0), sp.get("farm", 0.0)
    if "uscale_" in sp:
        pass
    if "back" in sp:
        kn2, an2 = ik2(hip, sp["back"], L["thigh"], L["shin"], sp.get("back_side", 1))
        pose["_miss"] = max(pose.get("_miss", 0.0), dist(an2, sp["back"]))
        pose["b_thigh"], pose["b_shin"] = ang_down(hip, kn2), ang_down(kn2, an2)
        pose["b_foot"] = sp.get("b_foot", 0.0)
    elif "b_thigh" in sp:
        pose["b_thigh"], pose["b_shin"] = sp["b_thigh"], sp.get("b_shin", sp["b_thigh"])
        pose["b_foot"] = sp.get("b_foot", 0.0)
    if "hand" not in sp and "back" not in sp:
        pass
    if 'miss_leg' in locals():
        pose["_miss"] = max(pose.get("_miss", 0.0), miss_leg)
    for k in ("front", "hide_arm", "far_arm"):
        if k in sp:
            pose[k] = sp[k]
    return pose


def torso_pt(hip, torso, along, out):
    """Point on the torso frame: `along` = distance from the shoulder down towards the hip, `out` = distance in
    front of the torso (+) or behind (-)."""
    sh = add(hip, vup(torso, L["torso"]))
    t = vup(torso)
    n = (math.cos(math.radians(torso)), math.sin(math.radians(torso)))
    return (sh[0] - t[0] * along + n[0] * out, sh[1] - t[1] * along + n[1] * out)


def lerp_pose(a, b, t):
    if "_spec" in a and "_spec" in b:
        sp = {}
        for k, va in a["_spec"].items():
            vb = b["_spec"].get(k, va)
            sp[k] = _lerp_val(va, vb, t)
        pose = _solve(sp)
        pose["_spec"] = sp
        return pose
    out = {}
    for k in set(a) | set(b):
        if k.startswith("_"):
            continue
        va, vb = a.get(k, b.get(k)), b.get(k, a.get(k))
        out[k] = _lerp_val(va, vb, t)
    return out


def ease(t):
    return t * t * (3 - 2 * t)


# ----------------------------------------------------------------------------------------------- FK
def build(pose, rotation=0.0):
    ox, oy = pose.get("ox", 0.0), pose.get("oy", 0.0)
    P = {}
    P["ankle"] = (ox, oy)
    f = math.radians(pose.get("foot", 0.0))
    P["toe"] = add(P["ankle"], (math.cos(f) * L["foot"], math.sin(f) * L["foot"]))
    P["heel"] = add(P["ankle"], (-math.cos(f) * 5.0, -math.sin(f) * 5.0))
    P["knee"] = add(P["ankle"], vup(pose["shin"], L["shin"]))
    P["hip"] = add(P["knee"], vup(pose["thigh"], L["thigh"]))
    P["shoulder"] = add(P["hip"], vup(pose["torso"], L["torso"]))
    th = pose.get("head", pose["torso"])
    P["head"] = add(P["shoulder"], vup(th, L["neck"] + L["head"]))
    P["elbow"] = add(P["shoulder"], vdown(pose["uarm"], L["uarm"] * pose.get("uscale", 1.0)))
    P["wrist"] = add(P["elbow"], vdown(pose["farm"], L["farm"] * pose.get("fscale", 1.0)))
    if "b_thigh" in pose:
        P["knee2"] = add(P["hip"], vdown(pose["b_thigh"], L["thigh"]))
        P["ankle2"] = add(P["knee2"], vdown(pose["b_shin"], L["shin"]))
        f2 = math.radians(pose.get("b_foot", 0.0))
        P["toe2"] = add(P["ankle2"], (math.cos(f2) * L["foot"] * 0.85, math.sin(f2) * L["foot"] * 0.85))
        P["heel2"] = add(P["ankle2"], (-math.cos(f2) * 5.0, -math.sin(f2) * 5.0))
    rad = lambda a: math.radians(a)
    N = {
        "shin": (math.cos(rad(pose["shin"])), math.sin(rad(pose["shin"]))),
        "thigh": (math.cos(rad(pose["thigh"])), math.sin(rad(pose["thigh"]))),
        "torso": (math.cos(rad(pose["torso"])), math.sin(rad(pose["torso"]))),
        "head": (math.cos(rad(th)), math.sin(rad(th))),
        "uarm": (math.cos(rad(pose["uarm"])), -math.sin(rad(pose["uarm"]))),
        "farm": (math.cos(rad(pose["farm"])), -math.sin(rad(pose["farm"]))),
    }
    if rotation:
        P = {k: rot(v, rotation) for k, v in P.items()}
        N = {k: rot(v, rotation) for k, v in N.items()}
    return P, N


def rot(p, deg):
    r = math.radians(deg)
    c, s = math.cos(r), math.sin(r)
    return (p[0] * c - p[1] * s, p[0] * s + p[1] * c)


def render(pose, pose_name_unused=None, rotation=0.0, hilite=None, equipment=None, hands_floor=False, scene=None,
           view=None):
    """Legacy entry point: returns (points, normals) of a pose."""
    return build(pose, rotation)


# ----------------------------------------------------------------------------------------------- drawing primitives
def capsule(d, a, b, ra, rb, col):
    dx, dy = b[0] - a[0], b[1] - a[1]
    n = math.hypot(dx, dy) or 1
    nx, ny = -dy / n, dx / n
    d.polygon([(a[0] + nx * ra, a[1] + ny * ra), (b[0] + nx * rb, b[1] + ny * rb),
               (b[0] - nx * rb, b[1] - ny * rb), (a[0] - nx * ra, a[1] - ny * ra)], fill=col)
    d.ellipse([a[0] - ra, a[1] - ra, a[0] + ra, a[1] + ra], fill=col)
    d.ellipse([b[0] - rb, b[1] - rb, b[0] + rb, b[1] + rb], fill=col)


def wcap(d, T, s, a, b, ra, rb, col):
    capsule(d, T(a), T(b), ra * s * SS, rb * s * SS, col)


def wcirc(d, T, s, c, r, col, outline=None, width=0):
    x, y = T(c)
    r = r * s * SS
    d.ellipse([x - r, y - r, x + r, y + r], fill=col, outline=outline, width=int(width * s * SS) if width else 0)


def wrect(d, T, s, x0, y0, x1, y1, r, col):
    a, b = T((min(x0, x1), min(y0, y1))), T((max(x0, x1), max(y0, y1)))
    d.rounded_rectangle([a[0], a[1], b[0], b[1]], radius=min(r * s * SS, (b[0] - a[0]) / 2, (b[1] - a[1]) / 2), fill=col)


def wpoly(d, T, pts, col):
    d.polygon([T(p) for p in pts], fill=col)


def wline(d, T, s, a, b, w, col):
    wcap(d, T, s, a, b, w / 2, w / 2, col)


def wring(d, T, s, c, r, w, col):
    x, y = T(c)
    r = r * s * SS
    d.ellipse([x - r, y - r, x + r, y + r], outline=col, width=max(1, int(w * s * SS)))


# ----------------------------------------------------------------------------------------------- gear
class Gear:
    """Equipment/scene piece with layers; fn(d, T, P, s).  bounds = (x0,y0,x1,y1) static world extent (optional),
    pts(P) -> extra world points to keep inside the camera (optional)."""

    def __init__(self, back=None, mid=None, front=None, bounds=None, pts=None):
        self.layers = {"back": [], "mid": [], "front": []}
        if back:
            self.layers["back"].append(back)
        if mid:
            self.layers["mid"].append(mid)
        if front:
            self.layers["front"].append(front)
        self.bounds = [bounds] if bounds else []
        self.ptsfn = [pts] if pts else []

    def __add__(self, o):
        return gear(self, o)

    def draw(self, layer, d, T, P, s):
        for fn in self.layers[layer]:
            fn(d, T, P, s)


def gear(*items):
    g = Gear()
    for it in items:
        if it is None:
            continue
        if callable(it) and not isinstance(it, Gear):
            it = Gear(mid=it)
        if isinstance(it, (list, tuple)):
            it = gear(*it)
        for k in g.layers:
            g.layers[k].extend(it.layers[k])
        g.bounds.extend(it.bounds)
        g.ptsfn.extend(it.ptsfn)
    return g


def _at(at, off=(0, 0)):
    def f(P):
        base = P[at] if isinstance(at, str) else (at(P) if callable(at) else at)
        return (base[0] + off[0], base[1] + off[1])
    return f


def barbell(at="wrist", plate=22, off=(0, 0), sz=False):
    """Barbell seen end-on: far plate behind the body, the bar crossing the grip, collar towards the viewer."""
    pt = _at(at, off)
    far = (-1.9 * E[0], -1.9 * E[1])
    pc = RUBBER if not sz else METAL_D

    def back(d, T, P, s):
        c = pt(P)
        fc = (c[0] + far[0], c[1] + far[1])
        wline(d, T, s, fc, c, 4.2, METAL)
        wcirc(d, T, s, fc, plate, pc)
        wcirc(d, T, s, fc, plate * 0.62, (84, 92, 114))
        wcirc(d, T, s, fc, 3.4, METAL)

    def front(d, T, P, s):
        c = pt(P)
        a = (c[0] + 0.55 * E[0], c[1] + 0.55 * E[1])
        n = (c[0] + 1.5 * E[0], c[1] + 1.5 * E[1])
        wline(d, T, s, a, n, 4.2, METAL)
        wcirc(d, T, s, n, 4.2, METAL_D)
        wcirc(d, T, s, n, 1.8, METAL)
        wring(d, T, s, c, 6.3, 1.1, (196, 150, 118))

    return Gear(back=back, front=front, pts=lambda P: [add(pt(P), (-plate, -plate)), add(pt(P), (plate, plate))])


def dumbbell(at="wrist", size=1.0, off=(0, 0)):
    pt = _at(at, off)
    e2 = (E[0] * 0.8, E[1] * 0.8)
    R = 10.5 * size

    def hexa(d, T, s, c, r, col):
        pts = [(c[0] + r * math.cos(math.radians(60 * i + 30)), c[1] + r * math.sin(math.radians(60 * i + 30)))
               for i in range(6)]
        wpoly(d, T, pts, col)

    def back(d, T, P, s):
        c = pt(P)
        fc = (c[0] - 1.3 * e2[0], c[1] - 1.3 * e2[1])
        wline(d, T, s, fc, c, 3.4, METAL)
        hexa(d, T, s, fc, R, RUBBER)
        wcirc(d, T, s, fc, R * 0.4, (84, 92, 114))

    def mid(d, T, P, s):
        c = pt(P)
        n = (c[0] + 1.25 * e2[0], c[1] + 1.25 * e2[1])
        wline(d, T, s, c, n, 3.4, METAL)
        hexa(d, T, s, n, R, EQUIP)
        wcirc(d, T, s, n, R * 0.4, (130, 138, 160))

    def front(d, T, P, s):
        c = pt(P)
        wline(d, T, s, add(c, (-1.5, -0.7)), add(c, (1.5, 0.7)), 3.0, METAL)

    return Gear(back=back, mid=mid, front=front, pts=lambda P: [add(pt(P), (-R - 8, -R - 8)), add(pt(P), (R + 8, R + 8))])


def kettlebell(at="wrist", size=1.0, off=(0, 0), drop=(0, 1)):
    """Kettlebell whose handle is held at `at`; the bell hangs along `drop`."""
    pt = _at(at, off)
    R = 15 * size

    def mid(d, T, P, s):
        c = pt(P)
        ctr = (c[0] + drop[0] * (R + 6), c[1] + drop[1] * (R + 6))
        wring(d, T, s, (c[0] + drop[0] * 5, c[1] + drop[1] * 5), 9 * size, 3.2, KBC)
        wcirc(d, T, s, ctr, R, KBC)
        wcirc(d, T, s, (ctr[0] - R * 0.35, ctr[1] - R * 0.35), R * 0.28, (96, 104, 128))

    def front(d, T, P, s):
        c = pt(P)
        wline(d, T, s, add(c, (-2.2, -0.6)), add(c, (2.2, 0.6)), 3.4, KBC)
        wring(d, T, s, c, 6.3, 1.1, (196, 150, 118))

    return Gear(mid=mid, front=front, pts=lambda P: [add(pt(P), (-R - 4, -R)), add(pt(P), (R + 4, 2 * R + 10))])


def band(anchor, at="wrist", post=None):
    """Resistance band from a fixed world anchor to the hand (or any point).  If the anchor is above the floor a
    post (door frame / rack upright) is drawn so that it never floats."""
    pt = _at(at)
    high = (FLOOR - anchor[1]) > 24 if post is None else post

    def back(d, T, P, s):
        if high:
            wrect(d, T, s, anchor[0] - 3.5, anchor[1], anchor[0] + 3.5, FLOOR - 4, 1, METAL_D)
            wrect(d, T, s, anchor[0] - 18, FLOOR - 5, anchor[0] + 18, FLOOR, 2, METAL_D)

    def mid(d, T, P, s):
        c = pt(P)
        wline(d, T, s, anchor, c, 2.8, BANDC)
        wcirc(d, T, s, anchor, 4.2, METAL)

    def front(d, T, P, s):
        c = pt(P)
        wcirc(d, T, s, c, 4.4, BANDC)
        wcirc(d, T, s, c, 1.8, SKIN)

    return Gear(back=back, mid=mid, front=front, bounds=(anchor[0] - 18, anchor[1] - 6, anchor[0] + 18, FLOOR if high else anchor[1] + 6))


def cable_station(pulley, at="wrist", handle="d", stack=True, tower=True, face=1):
    """Pulley tower grounded on the floor, cable to the hand, handle at the hand.
    handle: d | rope | bar | strap | none.  face=+1 tower stands to the right of the figure, -1 to the left."""
    pt = _at(at)
    px, py = pulley

    def back(d, T, P, s):
        if stack:
            sx = px + 24 * face
            wrect(d, T, s, sx - 11, py - 40, sx + 11, FLOOR, 2, (150, 158, 178))
            for i in range(9):
                yy = py - 36 + i * (FLOOR - py + 36) / 9
                wrect(d, T, s, sx - 11, yy, sx + 11, yy + 1.4, 0, (118, 126, 146))
            wrect(d, T, s, sx - 11, py - 12, sx + 11, py - 6, 1, ACCENT)
        if tower:
            wrect(d, T, s, px - 4, py - 34, px + 4, FLOOR, 2, METAL_D)
            wrect(d, T, s, px - 16, FLOOR - 5, px + 16, FLOOR, 2, METAL_D)
            if stack:
                wrect(d, T, s, min(px, px + 24 * face), py - 40, max(px, px + 24 * face), py - 34, 2, METAL_D)

    def mid(d, T, P, s):
        c = pt(P)
        wcirc(d, T, s, (px, py), 8, METAL_D)
        wcirc(d, T, s, (px, py), 4.5, (200, 205, 218))
        wline(d, T, s, (px, py), c, 1.8, CABLEC)

    def front(d, T, P, s):
        c = pt(P)
        if handle == "bar":
            wline(d, T, s, add(c, (-1.8, -0.8)), add(c, (2.2, 1.0)), 4.0, METAL)
            wcirc(d, T, s, add(c, (2.4, 1.1)), 4.4, METAL_D)
            wcirc(d, T, s, add(c, (-9, -4)), 3.6, METAL_D) if False else None
        elif handle == "rope":
            wcap(d, T, s, c, add(c, (4, 5)), 2.4, 2.8, RUBBER)
            wcap(d, T, s, add(c, (-2, -1)), add(c, (-5, 3)), 2.2, 2.6, RUBBER)
        elif handle == "strap":
            wring(d, T, s, add(c, (0, 1)), 6.5, 2.2, RUBBER)
        elif handle == "d":
            wline(d, T, s, add(c, (-1.8, -0.8)), add(c, (1.8, 0.8)), 3.6, METAL)
            wcirc(d, T, s, add(c, (2.2, 1.0)), 3.4, METAL_D)

    ext = (px - 22, py - 44, px + 30, FLOOR)
    return Gear(back=back, mid=mid, front=front, bounds=ext if stack or tower else None)


def box(x0, x1, h, col=WOODC):
    def back(d, T, P, s):
        wrect(d, T, s, x0, FLOOR - h, x1, FLOOR, 3, col)
        wrect(d, T, s, x0, FLOOR - h, x1, FLOOR - h + 5, 3, WOODD)
    return Gear(back=back, bounds=(x0, FLOOR - h, x1, FLOOR))


def mat(x0, x1, h=4.0):
    def back(d, T, P, s):
        wrect(d, T, s, x0, FLOOR - h, x1, FLOOR + 1, 2, MATC)
    return Gear(back=back, bounds=(x0, FLOOR - h, x1, FLOOR))


def swiss_ball(cx, r=34):
    def back(d, T, P, s):
        wcirc(d, T, s, (cx, FLOOR - r), r, BALLC)
        wcirc(d, T, s, (cx - r * 0.35, FLOOR - r * 1.35), r * 0.25, (160, 210, 236))
    return Gear(back=back, bounds=(cx - r, FLOOR - 2 * r, cx + r, FLOOR))


def flat_bench(x0, x1, top, thick=12, depth=True):
    """Flat pad, legs reach the floor.  top = world y of the pad surface."""
    def back(d, T, P, s):
        for x in (x0 + 16, x1 - 16):
            wrect(d, T, s, x - 3, top + thick - 2, x + 3, FLOOR, 1, METAL_D)
            wrect(d, T, s, x - 11, FLOOR - 4, x + 11, FLOOR, 2, METAL_D)
        wrect(d, T, s, x0, top, x1, top + thick, 5, BENCHC)
        wrect(d, T, s, x0 + 2, top + thick - 3, x1 - 2, top + thick, 2, METAL_D)
    return Gear(back=back, bounds=(x0, top, x1, FLOOR))


def seat_pad(x0, x1, top, thick=11):
    return flat_bench(x0, x1, top, thick)


def pad_line(p0, p1, th=12, col=BENCHC):
    """A padded board along p0 -> p1 (back pad of a bench or machine)."""
    def back(d, T, P, s):
        wcap(d, T, s, p0, p1, th / 2, th / 2, col)
    return Gear(back=back, bounds=(min(p0[0], p1[0]) - th, min(p0[1], p1[1]) - th, max(p0[0], p1[0]) + th, max(p0[1], p1[1]) + th))


def adj_bench(back_from, back_to, seat_x0, seat_x1, seat_top, th=12, thick=11):
    """Adjustable bench: seat pad, angled back pad (centerline back_from -> back_to), frame to the floor."""
    def back(d, T, P, s):
        rx = back_from[0]
        # rear leg + strut + front leg
        wrect(d, T, s, seat_x1 - 8 - 3, seat_top + thick - 2, seat_x1 - 8 + 3, FLOOR, 1, METAL_D)
        wrect(d, T, s, seat_x1 - 8 - 12, FLOOR - 4, seat_x1 - 8 + 10, FLOOR, 2, METAL_D)
        wrect(d, T, s, seat_x0 + 6 - 3, seat_top + thick - 2, seat_x0 + 6 + 3, FLOOR, 1, METAL_D)
        wrect(d, T, s, seat_x0 + 6 - 12, FLOOR - 4, seat_x0 + 6 + 12, FLOOR, 2, METAL_D)
        mid_ = ((back_from[0] + back_to[0]) / 2, (back_from[1] + back_to[1]) / 2)
        wline(d, T, s, (seat_x0 + 6, FLOOR - 6), mid_, 5, METAL_D)
        wrect(d, T, s, seat_x0 + 4, seat_top + thick, seat_x1 - 4, seat_top + thick + 3, 1, METAL_D)
        wrect(d, T, s, seat_x0, seat_top, seat_x1, seat_top + thick, 5, BENCHC)
        wcap(d, T, s, back_from, back_to, th / 2, th / 2, BENCHC)
    xs = [back_from[0], back_to[0], seat_x0, seat_x1]
    ys = [back_from[1], back_to[1], seat_top]
    return Gear(back=back, bounds=(min(xs) - 8, min(ys) - 8, max(xs) + 8, FLOOR))


def pullup_bar(x, y, depth=True, base=-60):
    """Pull-up bar at world height y with a post on each side (post at x+base on the floor, drawn as upright)."""
    def back(d, T, P, s):
        px = x + base
        wrect(d, T, s, px - 4, y, px + 4, FLOOR, 2, METAL_D)
        wrect(d, T, s, px - 20, FLOOR - 5, px + 20, FLOOR, 2, METAL_D)
        wline(d, T, s, (px, y), (x, y), 4.5, METAL_D)
    def front(d, T, P, s):
        wline(d, T, s, (x - 1.5, y - 0.6), (x + 2 * E[0], y + 2 * E[1]), 4.6, METAL)
        wcirc(d, T, s, (x + 2 * E[0], y + 2 * E[1]), 3.4, METAL_D)
    return Gear(back=back, front=front, bounds=(x + base - 22, y - 8, x + 20, FLOOR))


def dip_bars(mid, post_h=None):
    """Parallel bars seen from the side: the bar runs towards the viewer.  mid = world point at the middle of the
    grip (hands go there); two posts (near / far) down to the floor."""
    bx, by = mid

    def back(d, T, P, s):
        far = (bx - 1.7 * E[0], by - 1.7 * E[1])
        wrect(d, T, s, far[0] - 3.2, far[1], far[0] + 3.2, FLOOR - 4, 1, METAL_D)
        wrect(d, T, s, far[0] - 16, FLOOR - 5, far[0] + 16, FLOOR, 2, METAL_D)
        wline(d, T, s, far, (bx, by), 4.4, METAL_D)

    def front(d, T, P, s):
        near = (bx + 1.7 * E[0], by + 1.7 * E[1])
        wline(d, T, s, (bx + 0.5 * E[0], by + 0.5 * E[1]), near, 4.4, METAL)
        wrect(d, T, s, near[0] - 3.2, near[1], near[0] + 3.2, FLOOR - 4, 1, METAL_D)
        wrect(d, T, s, near[0] - 16, FLOOR - 5, near[0] + 16, FLOOR, 2, METAL_D)
        wring(d, T, s, (bx, by), 6.3, 1.1, (196, 150, 118))
    return Gear(back=back, front=front, bounds=(bx - 40, by - 14, bx + 34, FLOOR))


def lever(p0, p1, w=5.0, col=METAL_D, pivot=True):
    def back(d, T, P, s):
        wline(d, T, s, p0, p1, w, col)
        if pivot:
            wcirc(d, T, s, p0, w * 0.85, METAL)
    return Gear(back=back, bounds=(min(p0[0], p1[0]) - 6, min(p0[1], p1[1]) - 6, max(p0[0], p1[0]) + 6, max(p0[1], p1[1]) + 6))


def post(x, y0, y1, w=7, col=METAL_D, base=True):
    def back(d, T, P, s):
        wrect(d, T, s, x - w / 2, y0, x + w / 2, y1, 2, col)
        if base and abs(y1 - FLOOR) < 2:
            wrect(d, T, s, x - 22, FLOOR - 5, x + 22, FLOOR, 2, col)
    return Gear(back=back, bounds=(x - 22, y0, x + 22, y1))


def plates_at(p, r=22):
    def back(d, T, P, s):
        wcirc(d, T, s, p, r, RUBBER)
        wcirc(d, T, s, p, r * 0.6, (84, 92, 114))
    return Gear(back=back)


def smith_rail(x, top, below=FLOOR):
    """Smith machine: vertical rail at x (a thin tower) plus base."""
    def back(d, T, P, s):
        wrect(d, T, s, x - 3, top, x + 3, below, 2, (176, 182, 198))
        wrect(d, T, s, x - 26, FLOOR - 5, x + 26, FLOOR, 2, METAL_D)
        wrect(d, T, s, x - 6, top - 6, x + 6, top, 2, METAL_D)
    return Gear(back=back, bounds=(x - 26, top - 6, x + 26, FLOOR))


# legacy helpers (prototype API)
def bench_scene(rotation_hint=None):
    def f(d, T, P, s):
        k = s * SS
        hx, hy = T(P["hip"])
        sx, sy = T(P["shoulder"])
        x0 = min(hx, sx) - 40 * k
        x1 = max(hx, sx) + 26 * k
        y = max(hy, sy) + 14 * k
        fy = T((0, FLOOR))[1]
        d.rounded_rectangle([x0, y, x1, y + 12 * k], radius=5 * k, fill=BENCHC)
        for x in (x0 + 14 * k, x1 - 14 * k):
            d.rectangle([x - 3 * k, y + 12 * k, x + 3 * k, fy], fill=BENCHC)
    return f


# ----------------------------------------------------------------------------------------------- muscles
# muscle -> (segment, side, (t0, t1)); sides are relative to the segment's front normal
MUSCLES = {
    "quads": ("thigh", +1, (0.08, 0.92)), "hamstrings": ("thigh", -1, (0.08, 0.92)),
    "glutes": ("hipblob", -1, (0, 1)), "calves": ("shin", -1, (0.12, 0.88)),
    "biceps": ("uarm", +1, (0.1, 0.9)), "triceps": ("uarm", -1, (0.1, 0.9)),
    "forearms": ("farm", 0, (0.1, 0.9)), "chest": ("torso", +1, (0.55, 0.97)),
    "abs": ("torso", +1, (0.04, 0.5)), "back": ("torso", -1, (0.3, 0.97)),
    "lats": ("torso", -1, (0.22, 0.75)), "shoulders": ("shoulderblob", 0, (0, 1)),
    "obliques": ("torso", 0, (0.05, 0.45)), "traps": ("trapblob", 0, (0, 1)),
    "serratus": ("torso", +1, (0.4, 0.68)),
}
_SEGENDS = {"thigh": ("knee", "hip"), "shin": ("ankle", "knee"), "torso": ("hip", "shoulder"),
            "uarm": ("shoulder", "elbow"), "farm": ("elbow", "wrist")}
_SEGW = {"thigh": 9.6, "shin": 7.2, "torso": 14, "uarm": 7.4, "farm": 5.8}
_ARMSEG = ("uarm", "farm", "shoulderblob")


def unit(v):
    n = math.hypot(v[0], v[1]) or 1.0
    return (v[0] / n, v[1] / n)


def _hilite_layer(img_size, P, N, T, k, hilite, want_arm):
    seg = MUSCLES.get(hilite)
    if not seg:
        return None
    segn, side, (t0, t1) = seg
    is_arm = segn in _ARMSEG
    if is_arm != want_arm:
        return None
    ov = Image.new("RGBA", img_size, (0, 0, 0, 0))
    od = ImageDraw.Draw(ov, "RGBA")
    mask = Image.new("L", img_size, 0)
    md = ImageDraw.Draw(mask)
    if segn in _SEGENDS:
        a, b = P[_SEGENDS[segn][0]], P[_SEGENDS[segn][1]]
        n = N[segn]
        w = _SEGW[segn]
        wid = w * 1.05
        pa = (a[0] + (b[0] - a[0]) * t0 + n[0] * side * w * 0.55, a[1] + (b[1] - a[1]) * t0 + n[1] * side * w * 0.55)
        pb = (a[0] + (b[0] - a[0]) * t1 + n[0] * side * w * 0.55, a[1] + (b[1] - a[1]) * t1 + n[1] * side * w * 0.55)
        thick = w * (0.62 if side else 0.9)
        capsule(od, T(pa), T(pb), thick * k, thick * k, HILITE)
        capsule(md, T(a), T(b), w * k * 1.0, w * k * 1.0, 255)
        if segn == "thigh":
            md.ellipse([T(P["knee"])[0] - 9.6 * k, T(P["knee"])[1] - 9.6 * k, T(P["knee"])[0] + 9.6 * k, T(P["knee"])[1] + 9.6 * k], fill=255)
    elif segn == "hipblob":
        hp, sh_, kn = P["hip"], P["shoulder"], P["knee"]
        nt, nh = N["torso"], N["thigh"]
        tu = unit(sub(sh_, hp))
        hu = unit(sub(kn, hp))
        p1 = (hp[0] - nt[0] * 8.5 + tu[0] * 3, hp[1] - nt[1] * 8.5 + tu[1] * 3)
        p2 = (hp[0] - nh[0] * 8.0 + hu[0] * 15, hp[1] - nh[1] * 8.0 + hu[1] * 15)
        capsule(od, T(p1), T(p2), 8.6 * k, 8.0 * k, HILITE)
        capsule(md, T(P["hip"]), T(P["shoulder"]), 14 * k, 14 * k, 255)
        capsule(md, T(P["knee"]), T(P["hip"]), 12.5 * k, 12.5 * k, 255)
    elif segn == "shoulderblob":
        p = T(P["shoulder"])
        e = P["elbow"]
        sh_ = P["shoulder"]
        au = unit(sub(e, sh_))
        q2 = (sh_[0] + au[0] * 13, sh_[1] + au[1] * 13)
        capsule(od, T((sh_[0] + au[0] * 1, sh_[1] + au[1] * 1)), T(q2), 8.2 * k, 7.6 * k, HILITE)
        capsule(md, T(P["shoulder"]), T(P["elbow"]), 8.5 * k, 6.6 * k, 255)
        md.ellipse([p[0] - 9.5 * k, p[1] - 9.5 * k, p[0] + 9.5 * k, p[1] + 9.5 * k], fill=255)
    elif segn == "trapblob":
        a, b = P["shoulder"], P["head"]
        pm = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
        p = T(a)
        n = N["torso"]
        od.ellipse([p[0] - 12 * k - n[0] * 6 * k, p[1] - 12 * k - n[1] * 6 * k, p[0] + 12 * k - n[0] * 6 * k, p[1] + 12 * k - n[1] * 6 * k], fill=HILITE)
        capsule(md, T(P["hip"]), T(P["shoulder"]), 14.5 * k, 14.5 * k, 255)
    ov.putalpha(ImageChops.multiply(ov.getchannel("A"), mask))
    return ov


# ----------------------------------------------------------------------------------------------- drawing a frame
def _eye_hair(d, T, k, P, N):
    hx, hy = T(P["head"])
    r = L["head"] * k
    sx_, sy_ = T(P["shoulder"])
    ux, uy = hx - sx_, hy - sy_
    un = math.hypot(ux, uy) or 1
    ux, uy = ux / un, uy / un
    nx, ny = N["head"]
    cx_, cy_ = ux * 0.75 - nx * 0.65, uy * 0.75 - ny * 0.65
    c = math.degrees(math.atan2(cy_, cx_))
    d.pieslice([hx - r, hy - r, hx + r, hy + r], c - 105, c + 105, fill=HAIR)
    # nose
    nr = 2.6 * k
    npx, npy = hx + nx * r * 0.98, hy + ny * r * 0.98
    d.ellipse([npx - nr, npy - nr, npx + nr, npy + nr], fill=(222, 172, 136))
    ex_, ey_ = hx + nx * r * 0.52 + ux * r * 0.08, hy + ny * r * 0.52 + uy * r * 0.08
    er = 2.2 * k
    d.ellipse([ex_ - er, ey_ - er, ex_ + er, ey_ + er], fill=(30, 30, 40))


def _gear_list(g):
    if g is None:
        return None
    if isinstance(g, Gear):
        return g
    return gear(g)


def draw(P, N, hilite, equipment, scene, view, hands_floor=False, back_leg=False, lying=False, pose=None, size=W):
    """Draw one frame (points P/N from build()).  view = (minx, miny, maxx, maxy) in world coordinates."""
    minx, miny, maxx, maxy = view
    pad = 22
    s = min((size - 2 * pad) / (maxx - minx), (size - 2 * pad) / (maxy - miny), 1.7)
    cx, cy = (minx + maxx) / 2, (miny + maxy) / 2

    def T(p):
        return ((p[0] - cx) * s + size / 2) * SS, ((p[1] - cy) * s + size / 2) * SS

    equipment, scene = _gear_list(equipment), _gear_list(scene)
    img = Image.new("RGBA", (size * SS, size * SS), BG + (255,))
    d = ImageDraw.Draw(img, "RGBA")
    k = s * SS
    fy = T((0, FLOOR))[1]
    d.rounded_rectangle([14 * SS, fy - 1 * SS, (size - 14) * SS, fy + 6 * SS], radius=3 * SS, fill=FLOORC)
    if scene:
        scene.draw("back", d, T, P, s)
    if equipment:
        equipment.draw("back", d, T, P, s)

    def cap(a, b, ra, rb, col):
        capsule(d, T(P[a]), T(P[b]), ra * k, rb * k, col)

    def shoe(a, h, t, col):
        capsule(d, T(P[h]), T(P[t]), 6.9 * k, 6.5 * k, (92, 102, 130))
        wcirc(d, T, s, P[a], 7.2, (92, 102, 130))
        capsule(d, T(P[h]), T(P[t]), 5.6 * k, 5.2 * k, col)
        wcirc(d, T, s, P[a], 6.0, col)

    if back_leg:
        cap("hip", "knee2", 11.0, 8.2, SHORTS_FAR)
        cap("knee2", "ankle2", 8.2, 6.0, SKIN_FAR)
        shoe("ankle2", "heel2", "toe2", (196, 204, 222))
    shoe("ankle", "heel", "toe", SHOE)
    cap("ankle", "knee", 6.4, 8.8, SKIN)
    cap("knee", "hip", 9.6, 12.5, SHORTS)
    cap("hip", "shoulder", 14, 15, SHIRT)
    hx, hy = T(P["head"])
    r = L["head"] * k
    capsule(d, T(P["shoulder"]), T(P["head"]), 5 * k, 5 * k, SKIN)
    d.ellipse([hx - r, hy - r, hx + r, hy + r], fill=SKIN)
    _eye_hair(d, T, k, P, N)
    ov = _hilite_layer(img.size, P, N, T, k, hilite, False)
    if ov is not None:
        img = Image.alpha_composite(img, ov)
        d = ImageDraw.Draw(img, "RGBA")
    if equipment:
        equipment.draw("mid", d, T, P, s)
    if not (pose and pose.get("hide_arm")):
        capsule(d, T(P["shoulder"]), T(P["elbow"]), 8.5 * k, 6.6 * k, SHIRT)
        capsule(d, T(P["elbow"]), T(P["wrist"]), 6.2 * k, 5.0 * k, SKIN)
        wx, wy = T(P["wrist"])
        d.ellipse([wx - 6.2 * k, wy - 6.2 * k, wx + 6.2 * k, wy + 6.2 * k], fill=SKIN)
    ov = _hilite_layer(img.size, P, N, T, k, hilite, True)
    if ov is not None:
        img = Image.alpha_composite(img, ov)
        d = ImageDraw.Draw(img, "RGBA")
    if equipment:
        equipment.draw("front", d, T, P, s)
    if scene:
        scene.draw("front", d, T, P, s)
    return img.convert("RGB").resize((size, size), Image.LANCZOS)


# ----------------------------------------------------------------------------------------------- front view figure
FRONT = dict(sh=21.0, hipw=11.0, torso=92.0, neck=12.0)


def fpose(rot=0.0, pelvis=(0.0, -146.0), arm_l=(0, 0), arm_r=(0, 0), leg_l=(0, 0), leg_r=(0, 0), sc_arm=(1.0, 1.0),
          sc_leg=(1.0, 1.0), head=0.0, lean=1.0, foot_out=12.0, **extra):
    """Front-view pose.  Arms/legs: (upper, lower) abduction angles from "down" (0 = hanging, 90 = out to the side,
    180 = up); the image-left limbs mirror the image-right ones.  rot rotates the whole figure (negative = lying with
    the head to the left); pelvis = world position of the pelvis centre; sc_* foreshorten limbs (towards the viewer);
    lean < 1 shortens the torso (bent over)."""
    d = dict(rot=rot, pelvis=pelvis, arm_l=arm_l, arm_r=arm_r, leg_l=leg_l, leg_r=leg_r, sc_arm=sc_arm, sc_leg=sc_leg,
             head=head, lean=lean, foot_out=foot_out)
    d.update(extra)
    d["_front"] = True
    return d


def _lerp_front(a, b, t):
    out = {}
    for k, va in a.items():
        vb = b.get(k, va)
        if isinstance(va, (tuple, list)) and isinstance(va[0], (tuple, list)):
            out[k] = va
        else:
            out[k] = _lerp_val(va, vb, t)
    return out


def fbuild(p):
    r = math.radians(p["rot"])
    c, s_ = math.cos(r), math.sin(r)
    ox, oy = p["pelvis"]
    lean = p.get("lean", 1.0)

    def W(x, y):  # local (pelvis at 0,0, y down) -> world
        return (ox + x * c - y * s_, oy + x * s_ + y * c)

    P = {}
    P["pelvis"] = W(0, 0)
    P["neck"] = W(0, -FRONT["torso"] * lean)
    hd = p.get("head", 0.0)
    hr = math.radians(hd)
    P["head"] = W(math.sin(hr) * (FRONT["neck"] + L["head"]), -FRONT["torso"] * lean - math.cos(hr) * (FRONT["neck"] + L["head"]))
    shy = -FRONT["torso"] * lean + 6
    for side, sg in (("l", -1), ("r", 1)):
        a1, a2 = p["arm_" + side]
        sca = p["sc_arm"][0 if side == "l" else 1]
        sh = (sg * FRONT["sh"], shy)
        e = (sh[0] + sg * math.sin(math.radians(a1)) * L["uarm"] * sca, sh[1] + math.cos(math.radians(a1)) * L["uarm"] * sca)
        w = (e[0] + sg * math.sin(math.radians(a2)) * L["farm"] * sca, e[1] + math.cos(math.radians(a2)) * L["farm"] * sca)
        P["sh_" + side], P["el_" + side], P["wr_" + side] = W(*sh), W(*e), W(*w)
        b1, b2 = p["leg_" + side]
        scl = p["sc_leg"][0 if side == "l" else 1]
        sct = p.get("sc_thigh", (1.0, 1.0))[0 if side == "l" else 1]
        hp = (sg * FRONT["hipw"], 0)
        k = (hp[0] + sg * math.sin(math.radians(b1)) * L["thigh"] * scl * sct, hp[1] + math.cos(math.radians(b1)) * L["thigh"] * scl * sct)
        an = (k[0] + sg * math.sin(math.radians(b2)) * L["shin"] * scl, k[1] + math.cos(math.radians(b2)) * L["shin"] * scl)
        fo = p.get("foot_out", 12.0)
        # toe: out to the side and slightly down, rotated with the figure
        toe = (an[0] + sg * fo, an[1] + 3)
        P["hp_" + side], P["kn_" + side], P["an_" + side], P["toe_" + side] = W(*hp), W(*k), W(*an), W(*toe)
    P["_rot"] = (c, s_)
    return P


def fdraw(P, p, hilite, equipment, scene, view, size=W, floor=True):
    minx, miny, maxx, maxy = view
    pad = 22
    sc = min((size - 2 * pad) / (maxx - minx), (size - 2 * pad) / (maxy - miny), 1.7)
    cx, cy = (minx + maxx) / 2, (miny + maxy) / 2

    def T(q):
        return ((q[0] - cx) * sc + size / 2) * SS, ((q[1] - cy) * sc + size / 2) * SS

    equipment, scene = _gear_list(equipment), _gear_list(scene)
    img = Image.new("RGBA", (size * SS, size * SS), BG + (255,))
    d = ImageDraw.Draw(img, "RGBA")
    k = sc * SS
    if floor:
        fy = T((0, FLOOR))[1]
        d.rounded_rectangle([14 * SS, fy - 1 * SS, (size - 14) * SS, fy + 6 * SS], radius=3 * SS, fill=FLOORC)
    if scene:
        scene.draw("back", d, T, P, sc)
    if equipment:
        equipment.draw("back", d, T, P, sc)
    c, s_ = P["_rot"]

    def cap(a, b, ra, rb, col):
        capsule(d, T(P[a]), T(P[b]), ra * k, rb * k, col)

    def loc(vx, vy):  # rotate a local vector
        return (vx * c - vy * s_, vx * s_ + vy * c)

    # legs
    for side in ("l", "r"):
        capsule(d, T(P["toe_" + side]), T(P["an_" + side]), 5.2 * k, 6.0 * k, (92, 102, 130))
        capsule(d, T(P["toe_" + side]), T(P["an_" + side]), 3.9 * k, 4.8 * k, SHOE)
        cap("an_" + side, "kn_" + side, 6.2, 8.4, SKIN)
        cap("kn_" + side, "hp_" + side, 8.8, 11.5, SHORTS)
    # torso: trapezoid-ish capsule, wider at the shoulders
    a, b = P["pelvis"], P["neck"]
    capsule(d, T(a), T(b), 17 * k, 22 * k, SHIRT)
    up = loc(0, -1)
    nk = (P["neck"][0] + up[0] * 12, P["neck"][1] + up[1] * 12)
    capsule(d, T(nk), T(P["head"]), 5 * k, 5 * k, SKIN)
    hx, hy = T(P["head"])
    r_ = L["head"] * k
    d.ellipse([hx - r_, hy - r_, hx + r_, hy + r_], fill=SKIN)
    hr = math.radians(p.get("head", 0.0))
    upv = (up[0] * math.cos(hr) - up[1] * math.sin(hr), up[0] * math.sin(hr) + up[1] * math.cos(hr))
    ang = math.degrees(math.atan2(upv[1], upv[0]))
    d.pieslice([hx - r_, hy - r_, hx + r_, hy + r_], ang - 80, ang + 80, fill=HAIR)
    rt = loc(1, 0)
    for sg in (-1, 1):
        ex = hx + (rt[0] * sg * 5.8 - upv[0] * 3.5) * k
        ey = hy + (rt[1] * sg * 5.8 - upv[1] * 3.5) * k
        er = 1.9 * k
        d.ellipse([ex - er, ey - er, ex + er, ey + er], fill=(30, 30, 40))
    # highlight
    if hilite:
        ov = Image.new("RGBA", img.size, (0, 0, 0, 0))
        od = ImageDraw.Draw(ov, "RGBA")
        mask = Image.new("L", img.size, 0)
        md = ImageDraw.Draw(mask)
        capsule(md, T(a), T(b), 17 * k, 22 * k, 255)

        def blob(local, rx, ry, col=HILITE):
            q = T(P["pelvis"])
            w = loc(*local)
            cxp, cyp = q[0] + w[0] * k, q[1] + w[1] * k
            n = 28
            pts = []
            for i in range(n):
                th = 2 * math.pi * i / n
                lx, ly = math.cos(th) * rx, math.sin(th) * ry
                wv = loc(lx, ly)
                pts.append((cxp + wv[0] * k, cyp + wv[1] * k))
            od.polygon(pts, fill=col)
        lean = p.get("lean", 1.0)
        tl = FRONT["torso"] * lean
        if hilite == "chest":
            blob((-10, -tl * 0.72), 10.5, 9.5)
            blob((10, -tl * 0.72), 10.5, 9.5)
        elif hilite == "abs":
            blob((0, -tl * 0.35), 9, 20)
        elif hilite in ("lats", "back", "obliques", "serratus"):
            blob((-15, -tl * 0.5), 6.5, 20)
            blob((15, -tl * 0.5), 6.5, 20)
        elif hilite == "traps":
            blob((-9, -tl - 3), 10, 7)
            blob((9, -tl - 3), 10, 7)
        elif hilite == "glutes":
            blob((-15, -7), 6.8, 11)
            blob((15, -7), 6.8, 11)
        ov.putalpha(ImageChops.multiply(ov.getchannel("A"), mask))
        img = Image.alpha_composite(img, ov)
        d = ImageDraw.Draw(img, "RGBA")
        if hilite in ("quads", "hamstrings", "calves"):
            ov = Image.new("RGBA", img.size, (0, 0, 0, 0))
            od = ImageDraw.Draw(ov, "RGBA")
            for side in ("l", "r"):
                if hilite in ("quads", "hamstrings"):
                    capsule(od, T(P["hp_" + side]), T(P["kn_" + side]), 8.4 * k, 7.4 * k, HILITE)
                else:
                    capsule(od, T(P["kn_" + side]), T(P["an_" + side]), 7 * k, 5.6 * k, HILITE)
            img = Image.alpha_composite(img, ov)
            d = ImageDraw.Draw(img, "RGBA")
    if equipment:
        equipment.draw("mid", d, T, P, sc)
    for side in ("l", "r"):
        capsule(d, T(P["sh_" + side]), T(P["el_" + side]), 8.2 * k, 6.4 * k, SHIRT)
        capsule(d, T(P["el_" + side]), T(P["wr_" + side]), 6.2 * k, 5.0 * k, SKIN)
        wx, wy = T(P["wr_" + side])
        d.ellipse([wx - 6.0 * k, wy - 6.0 * k, wx + 6.0 * k, wy + 6.0 * k], fill=SKIN)
    if hilite in ("shoulders", "biceps", "triceps", "forearms"):
        ov = Image.new("RGBA", img.size, (0, 0, 0, 0))
        od = ImageDraw.Draw(ov, "RGBA")
        mk = Image.new("L", img.size, 0)
        md2 = ImageDraw.Draw(mk)
        for side in ("l", "r"):
            capsule(md2, T(P["sh_" + side]), T(P["el_" + side]), 8.2 * k, 6.4 * k, 255)
            capsule(md2, T(P["el_" + side]), T(P["wr_" + side]), 6.2 * k, 5.0 * k, 255)
            if hilite == "shoulders":
                q = T(P["sh_" + side])
                e = T(P["el_" + side])
                vx, vy = e[0] - q[0], e[1] - q[1]
                n_ = math.hypot(vx, vy) or 1
                od.ellipse([q[0] + vx / n_ * 5 * k - 10 * k, q[1] + vy / n_ * 5 * k - 10 * k, q[0] + vx / n_ * 5 * k + 10 * k, q[1] + vy / n_ * 5 * k + 10 * k], fill=HILITE)
                md2.ellipse([q[0] - 11 * k, q[1] - 11 * k, q[0] + 11 * k, q[1] + 11 * k], fill=255)
            elif hilite in ("biceps", "triceps"):
                capsule(od, T(P["sh_" + side]), T(P["el_" + side]), 6.4 * k, 5.4 * k, HILITE)
            else:
                capsule(od, T(P["el_" + side]), T(P["wr_" + side]), 5 * k, 4.2 * k, HILITE)
        ov.putalpha(ImageChops.multiply(ov.getchannel("A"), mk))
        img = Image.alpha_composite(img, ov)
        d = ImageDraw.Draw(img, "RGBA")
    if equipment:
        equipment.draw("front", d, T, P, sc)
    if scene:
        scene.draw("front", d, T, P, sc)
    return img.convert("RGB").resize((size, size), Image.LANCZOS)


def front_dumbbells(size=1.0, which=("l", "r"), axis="x"):
    """Dumbbells held in the front-view hands (handle across, heads on both sides)."""
    R = 9.5 * size

    def front(d, T, P, s):
        c, s_ = P["_rot"]
        for side in which:
            q = P["wr_" + side]
            ax = (c, s_) if axis == "x" else (-s_, c)  # local x (or y) axis in the world
            a = (q[0] - ax[0] * 8 * size, q[1] - ax[1] * 8 * size)
            b = (q[0] + ax[0] * 8 * size, q[1] + ax[1] * 8 * size)
            wline(d, T, s, a, b, 3.0, METAL)
            for e in (a, b):
                wcap(d, T, s, (e[0] - ax[0] * 1.0, e[1] - ax[1] * 1.0), (e[0] + ax[0] * 1.0, e[1] + ax[1] * 1.0), R * 0.62, R * 0.62, RUBBER)
        # fist over the handle
        for side in which:
            q = P["wr_" + side]
            wcirc(d, T, s, q, 5.2, SKIN)
    return Gear(front=front)


# ----------------------------------------------------------------------------------------------- animation
def pose_at(poses, u):
    """u in [0, len-1]: piecewise interpolation between consecutive key poses."""
    n = len(poses)
    if u <= 0:
        return poses[0]
    if u >= n - 1:
        return poses[-1]
    i = int(u)
    return lerp_pose(poses[i], poses[i + 1], u - i)


def animate_spec(spec, steps=9, size=W):
    """Render a spec (see module docstring) -> (frames, durations_ms): loop A -> B (-> C ...) -> A, eased."""
    poses = spec["poses"]
    if poses and poses[0].get("_front"):
        return _animate_front(spec, steps, size)
    n = len(poses)
    cycle = spec.get("cycle", False)
    keyposes = list(poses) + ([poses[0]] if cycle else [])
    m = len(keyposes)
    last = m - 1
    hold = spec.get("hold", (600, 500))
    frame_ms = spec.get("frame_ms", 70)
    # key-frame times
    if m == 2:
        us = [ease(i / steps) for i in range(steps + 1)]
        us = us + us[-2::-1]
        us = [u * last for u in us]
    else:
        seg = max(2, round(steps * 2 / last))
        grid = [i / (last * seg) for i in range(last * seg + 1)]
        up = [ease(u) * last for u in grid]
        if cycle:
            us = up[:-1]
        else:
            us = up + up[-2::-1]
    frames_pose = [pose_at(keyposes, u) for u in us]
    P0 = []
    pts = []
    for ps in frames_pose:
        Pp, Np = build(ps, spec.get("rotation", 0.0))
        P0.append((Pp, Np, ps))
        pts += list(Pp.values())
    eq, sc = _gear_list(spec.get("equipment")), _gear_list(spec.get("scene"))
    for g in (eq, sc):
        if g:
            for b in g.bounds:
                pts += [(b[0], b[1]), (b[2], b[3])]
            for fn in g.ptsfn:
                for Pp, _, _ in (P0[0], P0[len(P0) // 2]):
                    pts += fn(Pp)
    pts.append((0, FLOOR + 10))
    mx, my = spec.get("margin", (22, 18))
    view = (min(p[0] for p in pts) - mx, min(p[1] for p in pts) - my, max(p[0] for p in pts) + mx, max(p[1] for p in pts) + my)
    w, h = view[2] - view[0], view[3] - view[1]
    if w > h:
        view = (view[0], view[1] - (w - h) / 2, view[2], view[3] + (w - h) / 2)
    else:
        view = (view[0] - (h - w) / 2, view[1], view[2] + (h - w) / 2, view[3])
    imgs, durs = [], []
    nf = len(P0)
    for i, (Pp, Np, ps) in enumerate(P0):
        im = draw(Pp, Np, spec.get("hilite"), eq, sc, view, pose=ps, size=size, back_leg="b_thigh" in ps)
        imgs.append(im)
        durs.append(frame_ms)
    # holds: at key poses 0 and (the far end)
    durs[0] = hold[0]
    if not cycle:
        mid = us.index(max(us))
        durs[mid] = hold[1]
    return imgs, durs


def _animate_front(spec, steps, size):
    poses = spec["poses"]
    m = len(poses)
    last = m - 1
    hold = spec.get("hold", (600, 500))
    if m == 2:
        us = [ease(i / steps) * last for i in range(steps + 1)]
        us = us + us[-2::-1]
    else:
        seg = max(2, round(steps * 2 / last))
        up = [ease(i / (last * seg)) * last for i in range(last * seg + 1)]
        us = up + up[-2::-1]

    def at(u):
        if u >= last:
            return poses[-1]
        i = int(u)
        return _lerp_front(poses[i], poses[i + 1], u - i)
    fps = [at(u) for u in us]
    Ps = [fbuild(p) for p in fps]
    pts = []
    for P in Ps:
        pts += [v for k, v in P.items() if not k.startswith("_")]
    eq, sc = _gear_list(spec.get("equipment")), _gear_list(spec.get("scene"))
    for g in (eq, sc):
        if g:
            for b in g.bounds:
                pts += [(b[0], b[1]), (b[2], b[3])]
            for fn in g.ptsfn:
                pts += fn(Ps[0])
    if spec.get("floor", True):
        pts.append((0, FLOOR + 10))
    mx, my = spec.get("margin", (24, 20))
    view = (min(p[0] for p in pts) - mx, min(p[1] for p in pts) - my, max(p[0] for p in pts) + mx, max(p[1] for p in pts) + my)
    w, h = view[2] - view[0], view[3] - view[1]
    if w > h:
        view = (view[0], view[1] - (w - h) / 2, view[2], view[3] + (w - h) / 2)
    else:
        view = (view[0] - (h - w) / 2, view[1], view[2] + (h - w) / 2, view[3])
    imgs = [fdraw(P, p, spec.get("hilite"), eq, sc, view, size=size, floor=spec.get("floor", True)) for P, p in zip(Ps, fps)]
    durs = [spec.get("frame_ms", 70)] * len(imgs)
    durs[0] = hold[0]
    durs[us.index(max(us))] = hold[1]
    return imgs, durs


def animate(pa, pb, rotation=0.0, hilite=None, equipment=None, hands_floor=False, scene=None, steps=9, size=W,
            lying=False):
    """Legacy entry point: loop A -> B -> A."""
    return animate_spec(dict(poses=[pa, pb], rotation=rotation, hilite=hilite, equipment=equipment, scene=scene),
                        steps=steps, size=size)


def save_webp(imgs, durs, path, max_kb=45):
    """Save an animated webp trying a few qualities until it is below max_kb (decimal KB); returns size in bytes."""
    best = None
    for q, m in ((80, 6), (70, 6), (60, 6), (50, 6), (40, 6), (30, 6)):
        imgs[0].save(path, save_all=True, append_images=imgs[1:], duration=durs, loop=0, quality=q, method=m)
        import os
        sz = os.path.getsize(path)
        best = sz
        if sz <= max_kb * 1000:
            break
    return best
