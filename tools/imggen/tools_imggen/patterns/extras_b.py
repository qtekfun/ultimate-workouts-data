"""Helpers for the pull / core / cardio / mobility movement patterns (patterns_b.py).

Everything here is independent of figure.py (only constants / capsule() are imported, with a fallback
import path) so that engine changes do not break it.

Coordinate system (all "world"): x grows to the right (the figure faces +x), y grows DOWN, the floor top is y = 0.
A standing figure has its ankle at (0, -6).  Poses are written as targets (ankle, hip, wrist...) and solved with
2-link IK, so hands really sit on the equipment and feet really sit on the floor.

Pose kwargs (see mk()):
  A       ankle of the near leg                       hip     hip joint (or shin/thigh angles, from "up")
  torso   torso angle from up (+ towards +x), head    head angle (default = torso)
  W / uarm,farm   near wrist target (IK) or arm angles from "down" (+ towards +x);  ah = elbow bulge hint
  W2 / FA        far wrist target (IK) or (uarm, farm);  ah2 = hint
  A2      far ankle target;  or  FL = (thigh, shin) angles from down for the far leg;  kh / kh2 knee hints
  foot / foot2   foot direction in degrees (screen angle, 0 = pointing +x, -90 = pointing up)
  hide / hide2   do not draw near / far arm;  behind: near arm drawn behind torso;  front2: far arm drawn in front
"""
import math
import os
import sys
from PIL import Image, ImageDraw

_HERE = os.path.dirname(os.path.abspath(__file__))
try:
    from tools_imggen import figure as F  # engine package (when it exists)
except Exception:
    try:
        from .. import figure as F  # noqa
    except Exception:
        sys.path.insert(0, os.path.abspath(os.path.join(_HERE, "..", "..")))
        sys.path.insert(0, os.path.abspath(os.path.join(_HERE, "..")))
        import figure as F  # noqa

W_PX = 480
SS = 3
BG, SKIN, SHIRT, SHORTS, SHOE, HAIR = F.BG, F.SKIN, F.SHIRT, F.SHORTS, F.SHOE, F.HAIR
HILITE, FLOORC, EQUIP, BENCHC = F.HILITE, F.FLOORC, F.EQUIP, F.BENCHC
METAL = (150, 158, 178)
METAL_D = (118, 126, 146)
SKIN_FAR = (212, 166, 132)
SHIRT_FAR = (38, 80, 182)
SHORTS_FAR = (42, 49, 70)
RUBBER = (70, 76, 94)
ACCENT = (222, 96, 60)
BANDC = (232, 120, 60)
CABLEC = (60, 66, 84)
MATC = (98, 168, 150)
BALLC = (120, 186, 220)
KBC = (186, 76, 62)
LEN = dict(shin=70, thigh=76, torso=92, neck=12, head=16, uarm=50, farm=46, foot=24)
GROUND_ANKLE = (0.0, -6.0)


def vup(a, n=1.0):
    r = math.radians(a)
    return (math.sin(r) * n, -math.cos(r) * n)


def vdown(a, n=1.0):
    r = math.radians(a)
    return (math.sin(r) * n, math.cos(r) * n)


def add(p, q):
    return (p[0] + q[0], p[1] + q[1])


def sub(p, q):
    return (p[0] - q[0], p[1] - q[1])


def mul(p, k):
    return (p[0] * k, p[1] * k)


def dist(p, q):
    return math.hypot(p[0] - q[0], p[1] - q[1])


def lerp(a, b, t):
    return a + (b - a) * t


def lerp2(p, q, t):
    return (p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t)


def ease(t):
    return t * t * (3 - 2 * t)


def ik2(p0, p1, l1, l2, hint):
    """Joint position of a 2-link chain p0 -> joint -> p1' (p1' = reachable point towards p1); bulges towards hint."""
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    d0 = math.hypot(dx, dy) or 1e-6
    d = min(max(d0, abs(l1 - l2) + 1e-3), l1 + l2 - 1e-3)
    ux, uy = dx / d0, dy / d0
    a = (l1 * l1 - l2 * l2 + d * d) / (2 * d)
    h = math.sqrt(max(l1 * l1 - a * a, 0))
    base = (p0[0] + ux * a, p0[1] + uy * a)
    px, py = -uy, ux
    s = 1 if (px * hint[0] + py * hint[1]) >= 0 else -1
    j = (base[0] + px * h * s, base[1] + py * h * s)
    end = (p0[0] + ux * d, p0[1] + uy * d)
    return j, end, d0 - d


def ang_up(p, q):
    return math.degrees(math.atan2(q[0] - p[0], -(q[1] - p[1])))


def ang_down(p, q):
    return math.degrees(math.atan2(q[0] - p[0], q[1] - p[1]))


def mk(A=GROUND_ANKLE, hip=None, shin=0.0, thigh=0.0, torso=0.0, head=None, W=None, uarm=0.0, farm=0.0, ah=(0, 1),
       W2=None, FA=None, ah2=(0, 1), A2=None, FL=None, kh=(1, 0), kh2=(1, 0), foot=0.0, foot2=0.0,
       hide=False, hide2=False, behind=False, front2=False, sh_up=0.0, hand=None, E=None, E2=None, twist=0.0, **_):
    J = {"miss": 0.0, "twist": float(twist)}
    J["ankle"] = (float(A[0]), float(A[1]))
    if hip is not None:
        k, h, m = ik2(J["ankle"], hip, LEN["shin"], LEN["thigh"], kh)
        J["knee"], J["hip"] = k, h
        J["miss"] = max(J["miss"], m)
    else:
        J["knee"] = add(J["ankle"], vup(shin, LEN["shin"]))
        J["hip"] = add(J["knee"], vup(thigh, LEN["thigh"]))
    head = torso if head is None else head
    J["torso_a"], J["head_a"] = torso, head
    J["shoulder"] = add(J["hip"], vup(torso, LEN["torso"]))
    J["head"] = add(J["shoulder"], vup(head, LEN["neck"] + LEN["head"]))
    S = (J["shoulder"][0], J["shoulder"][1] - sh_up)
    J["aroot"] = S
    if E is not None and W is not None:
        J["elbow"], J["wrist"] = (float(E[0]), float(E[1])), (float(W[0]), float(W[1]))
    elif W is not None:
        e, w, m = ik2(S, W, LEN["uarm"], LEN["farm"], ah)
        J["elbow"], J["wrist"] = e, w
        J["miss"] = max(J["miss"], m)
    else:
        J["elbow"] = add(S, vdown(uarm, LEN["uarm"]))
        J["wrist"] = add(J["elbow"], vdown(farm, LEN["farm"]))
    if E2 is not None and W2 is not None:
        J["elbow2"], J["wrist2"] = (float(E2[0]), float(E2[1])), (float(W2[0]), float(W2[1]))
    elif W2 is not None:
        e, w, m = ik2(S, W2, LEN["uarm"], LEN["farm"], ah2)
        J["elbow2"], J["wrist2"] = e, w
        J["miss2"] = m
    elif FA is not None:
        J["elbow2"] = add(S, vdown(FA[0], LEN["uarm"]))
        J["wrist2"] = add(J["elbow2"], vdown(FA[1], LEN["farm"]))
    if A2 is not None:
        k, a, m = ik2(J["hip"], A2, LEN["thigh"], LEN["shin"], kh2)
        J["knee2"], J["ankle2"] = k, a
    elif FL is not None:
        J["knee2"] = add(J["hip"], vdown(FL[0], LEN["thigh"]))
        J["ankle2"] = add(J["knee2"], vdown(FL[1], LEN["shin"]))
    if hand is not None:
        J["hand_pt"] = (J["wrist"][0] + hand[0], J["wrist"][1] + hand[1])
    fr = math.radians(foot)
    J["toe"] = (J["ankle"][0] + math.cos(fr) * LEN["foot"], J["ankle"][1] + math.sin(fr) * LEN["foot"])
    if "ankle2" in J:
        fr = math.radians(foot2)
        J["toe2"] = (J["ankle2"][0] + math.cos(fr) * LEN["foot"] * 0.85, J["ankle2"][1] + math.sin(fr) * LEN["foot"] * 0.85)
    J["hide"], J["hide2"], J["behind"], J["front2"] = hide, hide2, behind, front2
    J["foot_a"] = foot
    return J


def to_engine_pose(J):
    """Engine-style pose dict (angles, anchored at the ankle) + 'at' offset, for engines that only know angles."""
    p = dict(shin=ang_up(J["ankle"], J["knee"]), thigh=ang_up(J["knee"], J["hip"]), torso=J["torso_a"],
             head=J["head_a"], uarm=ang_down(J["shoulder"], J["elbow"]), farm=ang_down(J["elbow"], J["wrist"]),
             at=J["ankle"])
    if "knee2" in J:
        p["b_thigh"] = ang_down(J["hip"], J["knee2"])
        p["b_shin"] = ang_down(J["knee2"], J["ankle2"])
    return p


# ----------------------------------------------------------------------------- key-pose interpolation
def lerp_kw(a, b, t):
    out = {}
    for k in set(a) | set(b):
        va, vb = a.get(k), b.get(k)
        if va is None or vb is None:
            out[k] = vb if va is None else va
        elif isinstance(va, bool) or isinstance(vb, bool) or callable(va):
            out[k] = vb if t >= 0.5 else va
        elif isinstance(va, (tuple, list)):
            out[k] = tuple(lerp(x, y, t) for x, y in zip(va, vb))
        else:
            out[k] = lerp(va, vb, t)
    return out


def normalize_keys(keys):
    """Make key poses interpolable: when some keys use IK targets (W/E/hip/A2...) and others angles (uarm/FA/FL...),
    bake the missing targets from the solved pose so that every key defines the same set of targets."""
    keys = [dict(k) for k in keys]
    def any_has(name):
        return any(k.get(name) is not None for k in keys)
    if keys and "_f" not in keys[0] and "H" not in keys[0]:
        Js = [mk(**k) for k in keys]
        for name, jkey in (("hip", "hip"), ("W", "wrist"), ("E", "elbow"), ("W2", "wrist2"), ("E2", "elbow2"),
                           ("A2", "ankle2")):
            if any_has(name):
                for k, J in zip(keys, Js):
                    if k.get(name) is None and jkey in J:
                        k[name] = J[jkey]
        # E needs W (and vice versa) so that both are used as explicit joints
        for en, wn in (("E", "W"), ("E2", "W2")):
            if any_has(en):
                for k, J in zip(keys, Js):
                    if k.get(wn) is None:
                        k[wn] = J["wrist" if wn == "W" else "wrist2"]
    return keys


def sequence(keys, loop="pingpong", steps=None, linear=False, hold=(600, 450), frame_ms=70):
    """Return a list of (kwargs, ms).  loop: 'pingpong' (k0..kn..k0, pauses at both ends) or 'cycle' (k0..kn, k0)."""
    n = len(keys)
    if loop == "pingpong":
        steps = steps or max(3, round(10.5 / (n - 1)))
        path = list(range(n)) + list(range(n - 2, -1, -1))
        segs = list(zip(path[:-1], path[1:]))
    else:
        steps = steps or max(2, round(21 / n))
        segs = [(i, (i + 1) % n) for i in range(n)]
    seq = []
    for si, (i, j) in enumerate(segs):
        for s in range(steps):
            t = s / steps
            ms = frame_ms
            if loop == "pingpong" and s == 0:
                if si == 0:
                    ms = hold[0]
                elif i == n - 1 and si == n - 1:
                    ms = hold[1]
            seq.append((lerp_kw(keys[i], keys[j], t if linear else ease(t)), ms))
    return seq


# ----------------------------------------------------------------------------- drawing
MUSC = {  # muscle -> (segment, side, (t0, t1), width)
    "quads": ("thigh", +1, (0.1, 0.9), 9), "hamstrings": ("thigh", -1, (0.1, 0.9), 9),
    "glutes": ("hipblob", -1, (0, 1), 0), "calves": ("shin", -1, (0.15, 0.85), 7),
    "biceps": ("uarm", +1, (0.1, 0.9), 7), "triceps": ("uarm", -1, (0.1, 0.9), 7),
    "forearms": ("farm", 0, (0.1, 0.9), 6), "chest": ("torso", +1, (0.55, 0.95), 12),
    "abs": ("torso", +1, (0.05, 0.5), 12), "back": ("torso", -1, (0.3, 0.95), 12),
    "lats": ("torso", -1, (0.25, 0.8), 12), "shoulders": ("shoulderblob", 0, (0, 1), 0),
    "traps": ("trapblob", 0, (0, 1), 0), "obliques": ("torso", 0, (0.05, 0.55), 13),
    "serratus": ("torso", +1, (0.45, 0.75), 10),
}


def capsule(d, a, b, ra, rb, col):
    F.capsule(d, a, b, ra, rb, col)


def disc(d, c, r, col):
    d.ellipse([c[0] - r, c[1] - r, c[0] + r, c[1] + r], fill=col)


class Item:
    """Equipment / scene element.  fn(d, T, J, s) draws it; ext(J) returns world points to keep in view."""

    def __init__(self, fn, ext=None):
        self.fn = fn
        self.ext = ext

    def __call__(self, d, T, J, s):
        self.fn(d, T, J, s)

    def extent(self, J):
        return self.ext(J) if self.ext else []


def many(*items):
    items = [i for i in items if i is not None]

    def fn(d, T, J, s):
        for i in items:
            i(d, T, J, s)

    def ext(J):
        pts = []
        for i in items:
            if hasattr(i, "extent"):
                pts += i.extent(J)
        return pts

    return Item(fn, ext)


def _normals(J):
    t = math.radians(J["head_a"])
    th = math.radians(J["torso_a"])
    S, K, A, H = J["shoulder"], J["knee"], J["ankle"], J["hip"]
    N = {}
    N["torso"] = (math.cos(th), math.sin(th))
    sa = math.radians(ang_up(A, K))
    N["shin"] = (math.cos(sa), math.sin(sa))
    ta = math.radians(ang_up(K, H))
    N["thigh"] = (math.cos(ta), math.sin(ta))
    ua = math.radians(ang_down(J["aroot"], J["elbow"]))
    N["uarm"] = (math.cos(ua), -math.sin(ua))
    fa = math.radians(ang_down(J["elbow"], J["wrist"]))
    N["farm"] = (math.cos(fa), -math.sin(fa))
    N["head"] = (math.cos(t), math.sin(t))
    return N


def draw_frame(J, hilite, equip, scene, front, view, size=360, floor=True, extra_back=None):
    minx, miny, maxx, maxy = view
    pad = 50
    s = min((W_PX - 2 * pad) / (maxx - minx), (W_PX - 2 * pad) / (maxy - miny), 2.4)
    cx, cy = (minx + maxx) / 2, (miny + maxy) / 2

    def T(p):
        return ((p[0] - cx) * s + W_PX / 2) * SS, ((p[1] - cy) * s + W_PX / 2) * SS

    k = s * SS
    img = Image.new("RGBA", (W_PX * SS, W_PX * SS), BG + (255,))
    d = ImageDraw.Draw(img, "RGBA")
    if floor:
        fy = T((0, 0))[1]
        d.rounded_rectangle([20 * SS, fy, (W_PX - 20) * SS, fy + 6 * SS], radius=3 * SS, fill=FLOORC)
    if scene:
        scene(d, T, J, s)
    N = _normals(J)

    def cap(a, b, ra, rb, col):
        capsule(d, T(J[a]), T(J[b]), ra * k, rb * k, col)

    def arm(pref, col_s, col_a, hide):
        if hide:
            return
        sh = "aroot"
        el, wr = "elbow" + pref, "wrist" + pref
        capsule(d, T(J[sh]), T(J[el]), 8.5 * k, 6.6 * k, col_s)
        capsule(d, T(J[el]), T(J[wr]), 6.4 * k, 5.0 * k, col_a)
        disc(d, T(J[wr]), 6.5 * k, col_a)

    if "elbow2" in J and not J["front2"]:
        arm("2", SHIRT_FAR, SKIN_FAR, J["hide2"])
    if J["behind"]:
        arm("", SHIRT, SKIN, J["hide"])
    if "knee2" in J:
        cap("hip", "knee2", 11.5, 8.5, SHORTS_FAR)
        cap("knee2", "ankle2", 8.5, 6.2, SKIN_FAR)
        cap("ankle2", "toe2", 6.5, 5.5, (222, 224, 232))
    cap("ankle", "toe", 6.5, 5.5, SHOE)
    cap("ankle", "knee", 6.4, 8.8, SKIN)
    cap("knee", "hip", 9.6, 12.5, SHORTS)
    cap("hip", "shoulder", 14, 14.5, SHIRT)
    hx, hy = T(J["head"])
    r = LEN["head"] * k
    capsule(d, T(J["shoulder"]), T(J["head"]), 5 * k, 5 * k, SKIN)
    d.ellipse([hx - r, hy - r, hx + r, hy + r], fill=SKIN)
    sx_, sy_ = T(J["shoulder"])
    ux, uy = hx - sx_, hy - sy_
    un = math.hypot(ux, uy) or 1
    ux, uy = ux / un, uy / un
    nx, ny = N["head"]
    cx_, cy_ = ux * 0.75 - nx * 0.65, uy * 0.75 - ny * 0.65
    c = math.degrees(math.atan2(cy_, cx_))
    d.pieslice([hx - r, hy - r, hx + r, hy + r], c - 105, c + 105, fill=HAIR)
    ex_, ey_ = hx + nx * r * 0.55 + ux * r * 0.05, hy + ny * r * 0.55 + uy * r * 0.05
    er = 2.2 * k
    d.ellipse([ex_ - er, ey_ - er, ex_ + er, ey_ + er], fill=(30, 30, 40))
    tw = J.get("twist", 0.0)
    if abs(tw) > 0.05:
        # torso rotation cue (seen from the side): chest turned to the viewer (collar, lighter chest) or back turned away (spine)
        hp_, sh2 = J["hip"], J["shoulder"]
        nn = N["torso"]
        if tw > 0:
            c0 = (hp_[0] + (sh2[0] - hp_[0]) * 0.68 + nn[0] * 7, hp_[1] + (sh2[1] - hp_[1]) * 0.68 + nn[1] * 7)
            cc = T(c0)
            tdir = (sh2[0] - hp_[0], sh2[1] - hp_[1])
            tn = math.hypot(*tdir) or 1
            tdir = (tdir[0] / tn, tdir[1] / tn)
            a_ = T((c0[0] - tdir[0] * 19 + nn[0] * 1, c0[1] - tdir[1] * 19 + nn[1] * 1))
            b_ = T((c0[0] + tdir[0] * 19 + nn[0] * 1, c0[1] + tdir[1] * 19 + nn[1] * 1))
            capsule(d, a_, b_, 7.5 * tw * k, 7.5 * tw * k, (84, 134, 232))
            v0 = (sh2[0] - tdir[0] * 3 + nn[0] * 6, sh2[1] - tdir[1] * 3 + nn[1] * 6)
            d.line([T(v0), T((v0[0] - tdir[0] * 11 + nn[0] * 4 * tw, v0[1] - tdir[1] * 11 + nn[1] * 4 * tw))], fill=(30, 66, 160), width=int(1.6 * k))
            if tw > 0.35:  # face turns to the viewer: second eye
                ex2, ey2 = hx + nx * r * 0.18 + ux * r * 0.05, hy + ny * r * 0.18 + uy * r * 0.05
                d.ellipse([ex2 - er, ey2 - er, ex2 + er, ey2 + er], fill=(30, 30, 40))
        else:
            a_ = T((sh2[0] - nn[0] * 12 - (sh2[0] - hp_[0]) * 0.05, sh2[1] - nn[1] * 12 - (sh2[1] - hp_[1]) * 0.05))
            b_ = T((hp_[0] + (sh2[0] - hp_[0]) * 0.25 - nn[0] * 12, hp_[1] + (sh2[1] - hp_[1]) * 0.25 - nn[1] * 12))
            d.line([a_, b_], fill=(30, 66, 160), width=int(1.8 * k))
            if tw < -0.35:  # back of the head
                d.ellipse([hx - r, hy - r, hx + r, hy + r], fill=HAIR)
    def do_hilite(img, d):
        if hilite not in MUSC:
            return img, d
        seg, side, (t0, t1), w = MUSC[hilite]
        ends = {"thigh": ("knee", "hip"), "shin": ("ankle", "knee"), "torso": ("hip", "shoulder"),
                "uarm": ("shoulder", "elbow"), "farm": ("elbow", "wrist")}
        ov = Image.new("RGBA", img.size, (0, 0, 0, 0))
        od = ImageDraw.Draw(ov, "RGBA")
        if seg in ends:
            a, b = J[ends[seg][0]], J[ends[seg][1]]
            n = N[seg]
            pa = (a[0] + (b[0] - a[0]) * t0 + n[0] * side * w * 0.5, a[1] + (b[1] - a[1]) * t0 + n[1] * side * w * 0.5)
            pb = (a[0] + (b[0] - a[0]) * t1 + n[0] * side * w * 0.5, a[1] + (b[1] - a[1]) * t1 + n[1] * side * w * 0.5)
            capsule(od, T(pa), T(pb), w * 0.6 * k, w * 0.6 * k, HILITE)
        elif seg == "hipblob":
            p = T(J["hip"])
            n = N["torso"]
            q = (-n[0] * 8, -n[1] * 8)
            od.ellipse([p[0] + q[0] * k - 13 * k, p[1] + q[1] * k - 13 * k, p[0] + q[0] * k + 13 * k,
                        p[1] + q[1] * k + 13 * k], fill=HILITE)
        elif seg == "trapblob":
            sh, hd = J["shoulder"], J["head"]
            p = T((sh[0] + (hd[0] - sh[0]) * 0.2, sh[1] + (hd[1] - sh[1]) * 0.2))
            od.ellipse([p[0] - 11 * k, p[1] - 11 * k, p[0] + 11 * k, p[1] + 11 * k], fill=HILITE)
        else:
            p = T(J["shoulder"])
            od.ellipse([p[0] - 10 * k, p[1] - 10 * k, p[0] + 10 * k, p[1] + 10 * k], fill=HILITE)
        img = Image.alpha_composite(img, ov)
        d = ImageDraw.Draw(img, "RGBA")
        return img, d

    ARM_SEGS = ("uarm", "farm", "shoulderblob", "trapblob")
    late = hilite in MUSC and MUSC[hilite][0] in ARM_SEGS
    if not late:
        img, d = do_hilite(img, d)
    if "elbow2" in J and J["front2"]:
        arm("2", SHIRT_FAR, SKIN_FAR, J["hide2"])
    if equip:
        equip(d, T, J, s)
    if not J["behind"]:
        arm("", SHIRT, SKIN, J["hide"])
    if late:
        img, d = do_hilite(img, d)
    if front:
        front(d, T, J, s)
    return img.convert("RGB").resize((size, size), Image.LANCZOS)


def _all_points(J):
    return [v for k_, v in J.items() if isinstance(v, tuple) and len(v) == 2 and k_ not in ("miss",)]


def _mkany(kw):
    return mkf(**kw["_f"]) if "_f" in kw else mk(**kw)


def render_spec(spec, size=360, steps=None):
    """Render a pattern spec -> (frames, durations).  spec['keys']: list of mk() kwargs (key poses)."""
    keys = spec["keys"]
    if spec.get("view_kind") != "front":
        keys = normalize_keys(keys)
    seq = sequence(keys, loop=spec.get("loop", "pingpong"), steps=steps or spec.get("steps"),
                   linear=spec.get("linear", False), hold=spec.get("hold", (600, 450)), frame_ms=spec.get("frame_ms", 70))
    Js = []
    front_kind = spec.get("view_kind") == "front"
    for kw, ms in seq:
        Js.append(mkf(**kw) if front_kind else mk(**kw))
    equip, scene, front = spec.get("equipment"), spec.get("scene"), spec.get("front")
    pts = []
    for J in Js:
        pts += _all_points(J)
        for it in (equip, scene, front):
            if it is not None and hasattr(it, "extent"):
                pts += it.extent(J)
    pts += [(0, 0)]
    mx = spec.get("margin", (28, 24))
    view = (min(p[0] for p in pts) - mx[0], min(p[1] for p in pts) - mx[1],
            max(p[0] for p in pts) + mx[0], max(p[1] for p in pts) + mx[1])
    if spec.get("view"):
        view = spec["view"]
    imgs, durs = [], []
    for J, (kw, ms) in zip(Js, seq):
        if front_kind:
            img = draw_front(J, spec.get("hilite"), equip, scene, front, view, size)
        else:
            img = draw_frame(J, spec.get("hilite"), equip, scene, front, view, size)
        imgs.append(img)
        durs.append(ms)
    return imgs, durs, Js


def save_webp(imgs, durs, path, quality=70, max_kb=44):
    """Save an animated WebP; lowers the quality until the file is below max_kb."""
    q = quality
    while True:
        imgs[0].save(path, save_all=True, append_images=imgs[1:], duration=durs, loop=0, quality=q, method=6)
        size = os.path.getsize(path)
        if size <= max_kb * 1024 or q <= 30:
            return size
        q -= 8


# ----------------------------------------------------------------------------- equipment (mid layer: before near arm)
def barbell(anchor="wrist", half=60, plate=21, off=(0, 0), dx_hand=0):
    def fn(d, T, J, s):
        x, y = T((J[anchor][0] + off[0], J[anchor][1] + off[1]))
        k = s * SS
        d.rounded_rectangle([x - half * k, y - 2.6 * k, x + half * k, y + 2.6 * k], radius=2 * k, fill=METAL)
        for sx in (-1, 1):
            for off_, hh, col in ((half - 12, plate, EQUIP), (half - 5, plate * 0.68, RUBBER)):
                cx_ = x + sx * off_ * k
                d.rounded_rectangle([cx_ - 3.5 * k, y - hh * k, cx_ + 3.5 * k, y + hh * k], radius=2.5 * k, fill=col)
    return Item(fn, lambda J: [(J[anchor][0] - half - 6 + off[0], J[anchor][1] - plate + off[1]),
                               (J[anchor][0] + half + 6 + off[0], J[anchor][1] + plate + off[1])])


def dumbbell(anchor="wrist", off=(0, 0), size=1.0, heads=True):
    def fn(d, T, J, s):
        x, y = T((J[anchor][0] + off[0], J[anchor][1] + off[1]))
        k = s * SS * size
        d.rounded_rectangle([x - 16 * k, y - 2.6 * k, x + 16 * k, y + 2.6 * k], radius=2 * k, fill=METAL)
        for dx in (-15, 15):
            d.rounded_rectangle([x + (dx - 4.5) * k, y - 11.5 * k, x + (dx + 4.5) * k, y + 11.5 * k], radius=3 * k, fill=EQUIP)
    return Item(fn, lambda J: [(J[anchor][0] - 22 + off[0], J[anchor][1] - 14 + off[1]), (J[anchor][0] + 22 + off[0], J[anchor][1] + 14 + off[1])])


def kettlebell(anchor="wrist", along="farm", r=12.5, gap=0.0):
    """Kettlebell gripped at its handle (at the wrist); the bell trails along the forearm direction."""
    def geom(J):
        if along == "down":
            u = (0.0, 1.0)
        elif along == "up":
            u = (0.0, -1.0)
        else:
            e, w = J["elbow"], J[anchor]
            n = dist(e, w) or 1
            u = ((w[0] - e[0]) / n, (w[1] - e[1]) / n)
        w = J[anchor]
        c = (w[0] + u[0] * (r + 4 + gap), w[1] + u[1] * (r + 4 + gap))
        return w, c, u

    def fn(d, T, J, s):
        w, c, u = geom(J)
        k = s * SS
        wx, wy = T(w)
        cx_, cy_ = T(c)
        px, py = -u[1], u[0]
        # handle: a half ring around the hand on the far side of the bell
        pts = []
        for i in range(13):
            a = math.pi * i / 12
            lat = -math.cos(a) * 8.5
            fwd = -math.sin(a) * 7.0 - 1.0
            pts.append((wx + (px * lat + u[0] * fwd) * k, wy + (py * lat + u[1] * fwd) * k))
        d.line(pts, fill=KBC, width=int(3.4 * k), joint="curve")
        disc(d, (cx_, cy_), r * k, KBC)
        disc(d, (cx_ - r * 0.32 * k, cy_ - r * 0.32 * k), r * 0.22 * k, (104, 112, 136))
    return Item(fn, lambda J: [add(geom(J)[1], (r + 8, r + 8)), add(geom(J)[1], (-r - 8, -r - 8))])


def dumbbell_end(anchor="wrist", r=11.5):
    """Dumbbell seen end-on (handle across the body, supinated grip): a plate disc behind the fist."""
    def fn(d, T, J, s):
        x, y = T(J[anchor])
        k = s * SS
        disc(d, (x, y), r * k, EQUIP)
        disc(d, (x, y), (r - 3.5) * k, RUBBER)
    return Item(fn, lambda J: [add(J[anchor], (-r - 2, -r - 2)), add(J[anchor], (r + 2, r + 2))])


def cable_tower(x, pul_y, side=-1, w=26, stack_h=92, wheel=True, beam_to=None):
    """Weight-stack column standing on the floor at world x (the column occupies [x+side*w, x]); pulley wheel at (x, pul_y)."""
    def fn(d, T, J, s):
        k = s * SS
        x0, x1 = sorted((x, x + side * w))
        top = min(pul_y - 12, -stack_h - 10)
        tl, br = T((x0, top)), T((x1, 0))
        d.rounded_rectangle([tl[0], tl[1], br[0], br[1]], radius=3 * k, fill=BENCHC)
        # stack plates
        yy = -4
        while yy > -stack_h:
            a, b = T((x0 + 4, yy - 7)), T((x1 - 4, yy))
            d.rounded_rectangle([a[0], a[1], b[0], b[1]], radius=1.5 * k, fill=(176, 184, 202))
            yy -= 9
        # pulley arm + wheel
        px, py = T((x, pul_y))
        a = T((x + side * w * 0.5, pul_y))
        d.rounded_rectangle([min(a[0], px) - 2 * k, py - 3 * k, max(a[0], px) + 2 * k, py + 3 * k], radius=2 * k, fill=EQUIP)
        if beam_to is not None:
            bx0, bx1 = sorted((beam_to, x))
            a_, b_ = T((bx0, pul_y - 3)), T((bx1, pul_y + 3))
            d.rounded_rectangle([a_[0], a_[1], b_[0], b_[1]], radius=2 * k, fill=EQUIP)
            px, py = T((beam_to, pul_y))
        if wheel:
            disc(d, (px, py), 7.5 * k, EQUIP)
            disc(d, (px, py), 3 * k, (170, 178, 196))
    return Item(fn, lambda J: [(x - 30, pul_y - 14), (x + 30, 0)])


def cable_line(pul, anchor="wrist", handle="d", pul_dx=0.0):
    """Cable from a fixed pulley to the hand; handle drawn at the hand."""
    def fn(d, T, J, s):
        k = s * SS
        w = J[anchor]
        p = T(pul)
        q = T(w)
        d.line([p, q], fill=CABLEC, width=int(2.2 * k))
        if handle == "rope":
            u = (q[0] - p[0], q[1] - p[1])
            n = math.hypot(*u) or 1
            u = (u[0] / n, u[1] / n)
            for sx in (6, 13):
                disc(d, (q[0] + u[0] * sx * k, q[1] + u[1] * sx * k), 3.6 * k, (230, 120, 60))
            d.line([q, (q[0] + u[0] * 13 * k, q[1] + u[1] * 13 * k)], fill=(214, 200, 170), width=int(3.4 * k))
        elif handle == "bar":
            d.rounded_rectangle([q[0] - 2.6 * k, q[1] - 2.6 * k, q[0] + 2.6 * k, q[1] + 2.6 * k], radius=2 * k, fill=METAL)
            d.rounded_rectangle([q[0] - 17 * k, q[1] - 2.8 * k, q[0] + 17 * k, q[1] + 2.8 * k], radius=2 * k, fill=METAL)
        elif handle == "vbar":
            # wide lat bar seen from the side: short bar with knobs
            d.rounded_rectangle([q[0] - 24 * k, q[1] - 2.6 * k, q[0] + 24 * k, q[1] + 2.6 * k], radius=2 * k, fill=METAL)
            for sx in (-24, 24):
                disc(d, (q[0] + sx * k, q[1]), 4 * k, EQUIP)
        elif handle == "vgrip":
            d.polygon([(q[0] - 12 * k, q[1] + 7 * k), (q[0] + 12 * k, q[1] + 7 * k), (q[0], q[1] - 2 * k)], fill=METAL_D)
            d.rounded_rectangle([q[0] - 12 * k, q[1] + 3 * k, q[0] + 12 * k, q[1] + 8 * k], radius=2 * k, fill=METAL)
        elif handle == "d":
            d.rounded_rectangle([q[0] - 8 * k, q[1] - 3 * k, q[0] + 8 * k, q[1] + 3 * k], radius=2.5 * k, fill=METAL)
        elif handle == "strap":
            d.rounded_rectangle([q[0] - 7 * k, q[1] - 3 * k, q[0] + 7 * k, q[1] + 3 * k], radius=2.5 * k, fill=(200, 160, 100))
    return Item(fn, lambda J: [pul, J[anchor]])


def band_line(anchor_pt, to="wrist", post=True, sag=0.0, width=3.4):
    """Resistance band from a fixed point to the hand."""
    def fn(d, T, J, s):
        k = s * SS
        a = anchor_pt(J) if callable(anchor_pt) else anchor_pt
        w = J[to]
        if post:
            p = T(a)
            disc(d, p, 5 * k, EQUIP)
        pa, pw = T(a), T(w)
        mx, my = (pa[0] + pw[0]) / 2, (pa[1] + pw[1]) / 2 + sag * k
        pts = []
        for i in range(0, 13):
            t = i / 12
            x = (1 - t) ** 2 * pa[0] + 2 * (1 - t) * t * mx + t * t * pw[0]
            y = (1 - t) ** 2 * pa[1] + 2 * (1 - t) * t * my + t * t * pw[1]
            pts.append((x, y))
        d.line(pts, fill=BANDC, width=int(width * k), joint="curve")
        disc(d, pw, 5 * k, BANDC)
    return Item(fn, lambda J: [anchor_pt(J) if callable(anchor_pt) else anchor_pt, J[to]])


def box(x0, y0, x1, y1, col=BENCHC, radius=4):
    def fn(d, T, J, s):
        a, b = T((x0, y0)), T((x1, y1))
        d.rounded_rectangle([a[0], a[1], b[0], b[1]], radius=radius * s * SS, fill=col)
    return Item(fn, lambda J: [(x0, y0), (x1, y1)])


def post_rect(x0, y0, x1, y1, col=BENCHC):
    return box(x0, y0, x1, y1, col, radius=1.5)


def mat(x0=-150, x1=150, h=5, col=MATC):
    def fn(d, T, J, s):
        a, b = T((x0, -h)), T((x1, 0))
        d.rounded_rectangle([a[0], a[1], b[0], b[1] + 2 * s * SS], radius=3 * s * SS, fill=col)
    return Item(fn, lambda J: [(x0, -h), (x1, 0)])


def bench(x0, x1, top, thick=11, legs=(0.12, 0.88), col=BENCHC):
    """Flat bench, top surface at height `top` above floor (world y = -top)."""
    def fn(d, T, J, s):
        k = s * SS
        a, b = T((x0, -top)), T((x1, -top + thick))
        d.rounded_rectangle([a[0], a[1], b[0], b[1]], radius=4 * k, fill=col)
        for f in legs:
            xx = x0 + (x1 - x0) * f
            p, q = T((xx - 3, -top + thick)), T((xx + 3, 0))
            d.rectangle([p[0], p[1], q[0], q[1]], fill=col)
            ft0, ft1 = T((xx - 11, -3)), T((xx + 11, 0))
            d.rounded_rectangle([ft0[0], ft0[1], ft1[0], ft1[1]], radius=1.5 * k, fill=col)
    return Item(fn, lambda J: [(x0, -top), (x1, 0)])


def pad(p0, p1, r=7, col=(70, 78, 100)):
    """Padded cushion drawn as a capsule between two world points."""
    def fn(d, T, J, s):
        capsule(d, T(p0), T(p1), r * s * SS, r * s * SS, col)
    return Item(fn, lambda J: [p0, p1])


def tbar_scene(pivot):
    def fn(d, T, J, s):
        k = s * SS
        w = J["wrist"]
        p = T(pivot)
        q = T((w[0] - 6, w[1] + 2))
        capsule(d, p, q, 3.2 * k, 3.2 * k, METAL_D)
        for dx, hh in ((6, 17), (15, 17)):
            x = p[0] + dx * k
            d.rounded_rectangle([x - 3.5 * k, p[1] - hh * k, x + 3.5 * k, p[1] + hh * k], radius=2.5 * k, fill=EQUIP)
        disc(d, p, 4 * k, EQUIP)
    return Item(fn, lambda J: [(pivot[0] - 8, pivot[1] - 20), (pivot[0] + 20, 0)])


def tbar_handle(pivot):
    def fn(d, T, J, s):
        k = s * SS
        x, y = T(J["wrist"])
        d.rounded_rectangle([x - 15 * k, y - 3 * k, x + 15 * k, y + 3 * k], radius=2 * k, fill=METAL)
    return Item(fn)


def lever_arm(pivot, handle="bar"):
    """Machine lever arm from a fixed pivot to the hand."""
    def fn(d, T, J, s):
        k = s * SS
        p, q = T(pivot), T(J["wrist"])
        capsule(d, p, q, 3.6 * k, 3.6 * k, EQUIP)
        disc(d, p, 6 * k, METAL_D)
        d.rounded_rectangle([q[0] - 3.2 * k, q[1] - 3.2 * k, q[0] + 3.2 * k, q[1] + 3.2 * k], radius=2 * k, fill=METAL)
        d.rounded_rectangle([q[0] - 14 * k, q[1] - 3.2 * k, q[0] + 14 * k, q[1] + 3.2 * k], radius=2 * k, fill=METAL)
    return Item(fn, lambda J: [pivot, J["wrist"]])


def thigh_pad():
    """Hold-down pad over the thighs (front layer)."""
    def fn(d, T, J, s):
        k = s * SS
        h, kn = J["hip"], J["knee"]
        dx, dy = kn[0] - h[0], kn[1] - h[1]
        n = math.hypot(dx, dy) or 1
        nx, ny = dy / n, -dx / n  # normal pointing up for a thigh going forward
        if ny > 0:
            nx, ny = -nx, -ny
        ux, uy = dx / n, dy / n
        c = (h[0] + dx * 0.72 + nx * 20, h[1] + dy * 0.72 + ny * 20)
        capsule(d, T((c[0] - ux * 13, c[1] - uy * 13)), T((c[0] + ux * 13, c[1] + uy * 13)), 8 * k / (s * SS) * s * SS, 8 * k / (s * SS) * s * SS, (70, 78, 100))
        a, b = T((c[0] + nx * 6, c[1] + ny * 6)), T((c[0] + nx * 40, c[1] + ny * 40))
        capsule(d, a, b, 2.4 * k, 2.4 * k, EQUIP)
    return Item(fn, lambda J: [J["hip"], J["knee"]])


def pullup_frame(xb, bar_y, post_dx=78):
    """Wall/frame mounted pull-up bar seen from the side: bar end-on, arm to the post."""
    def fn(d, T, J, s):
        k = s * SS
        px = xb + post_dx
        a, b = T((xb, bar_y - 4)), T((px + 8, bar_y + 4))
        d.rounded_rectangle([a[0], a[1], b[0], b[1]], radius=3 * k, fill=BENCHC)
        p, q = T((px - 6, bar_y - 4)), T((px + 8, 0))
        d.rectangle([p[0], p[1], q[0], q[1]], fill=BENCHC)
        f0, f1 = T((px - 30, -5)), T((px + 32, 0))
        d.rounded_rectangle([f0[0], f0[1], f1[0], f1[1]], radius=2 * k, fill=EQUIP)
        c = T((xb, bar_y))
        disc(d, c, 5.2 * k, METAL)
        disc(d, c, 2.2 * k, METAL_D)
    return Item(fn, lambda J: [(xb - 30, bar_y - 14), (xb + post_dx + 34, 0)])


def fist(anchor="hand_pt"):
    """Skin capsule from the wrist to a hand point (wrist-curl style hand)."""
    def fn(d, T, J, s):
        k = s * SS
        capsule(d, T(J["wrist"]), T(J[anchor]), 5.8 * k, 5.2 * k, SKIN)
    return Item(fn)


def ball(cx, cy, r, col=BALLC):
    def fn(d, T, J, s):
        c = T((cx, cy))
        k = s * SS
        disc(d, c, r * k, col)
        disc(d, (c[0] - r * 0.3 * k, c[1] - r * 0.35 * k), r * 0.22 * k, (170, 214, 238))
    return Item(fn, lambda J: [(cx - r, cy - r), (cx + r, cy + r)])


# ----------------------------------------------------------------------------- front-view figure (jumping jack, side bend ...)
def mkf(H=(0, -152), lean=0.0, head=None, aR=(0, 0), aL=(0, 0), lR=(0, 0), lL=(0, 0), rot=0.0, pivot=None,
        off=(0, 0), sw=17, hw=9, wR=None, wL=None, hR=(0.6, 1), hL=(-0.6, 1), eyes=True, face=1, ry=None, eR=None):
    """Front-facing figure.  Angles from 'down', positive towards screen-right.  rot = rotate whole body (deg, clockwise)
    around `pivot` (default hip), off = translation applied last."""
    J = {"kind": "front"}
    head = lean if head is None else head
    S = add(H, vup(lean, LEN["torso"]))
    perp = (math.cos(math.radians(lean)), math.sin(math.radians(lean)))
    J["H"], J["S"] = H, S
    J["SR"], J["SL"] = add(S, mul(perp, sw)), add(S, mul(perp, -sw))
    J["HR"], J["HL"] = add(H, (hw, 0)), add(H, (-hw, 0))
    J["head"] = add(S, vup(head, LEN["neck"] + LEN["head"]))
    for tag, sh, ang in (("R", J["SR"], aR), ("L", J["SL"], aL)):
        J["e" + tag] = add(sh, vdown(ang[0], LEN["uarm"]))
        J["w" + tag] = add(J["e" + tag], vdown(ang[1], LEN["farm"]))
    for tag, hp, ang in (("R", J["HR"], lR), ("L", J["HL"], lL)):
        J["k" + tag] = add(hp, vdown(ang[0], LEN["thigh"]))
        J["a" + tag] = add(J["k" + tag], vdown(ang[1], LEN["shin"]))
    # feet: pointing outward (down-ish when the body is rotated)
    J["fR"] = add(J["aR"], (12, 5))
    J["fL"] = add(J["aL"], (-12, 5))
    if rot:
        pv = pivot or H
        c, s_ = math.cos(math.radians(rot)), math.sin(math.radians(rot))
        for k_ in list(J):
            v = J[k_]
            if isinstance(v, tuple):
                x, y = v[0] - pv[0], v[1] - pv[1]
                J[k_] = (pv[0] + x * c - y * s_, pv[1] + x * s_ + y * c)
    for k_ in list(J):
        v = J[k_]
        if isinstance(v, tuple):
            J[k_] = (v[0] + off[0], v[1] + off[1])
    J["rot"], J["head_a"], J["lean"], J["face"], J["ry"] = rot, head, lean, face, ry
    for tag, tgt, hint in (("R", wR, hR), ("L", wL, hL)):
        if tgt is not None:
            t_ = tgt(J) if callable(tgt) else tgt
            e, w, _ = ik2(J["S" + tag], t_, LEN["uarm"], LEN["farm"], hint)
            J["e" + tag], J["w" + tag] = e, w
    if eR is not None:  # explicit near elbow (wR is then the hand, no IK): forearm drawn foreshortened on the floor
        J["eR"] = eR(J) if callable(eR) else eR
        J["wR"] = wR(J) if callable(wR) else wR
    return J


def draw_front(J, hilite, equip, scene, front, view, size=360):
    minx, miny, maxx, maxy = view
    pad = 50
    s = min((W_PX - 2 * pad) / (maxx - minx), (W_PX - 2 * pad) / (maxy - miny), 2.4)
    cx, cy = (minx + maxx) / 2, (miny + maxy) / 2

    def T(p):
        return ((p[0] - cx) * s + W_PX / 2) * SS, ((p[1] - cy) * s + W_PX / 2) * SS

    k = s * SS
    img = Image.new("RGBA", (W_PX * SS, W_PX * SS), BG + (255,))
    d = ImageDraw.Draw(img, "RGBA")
    fy = T((0, 0))[1]
    d.rounded_rectangle([20 * SS, fy, (W_PX - 20) * SS, fy + 6 * SS], radius=3 * SS, fill=FLOORC)
    if scene:
        scene(d, T, J, s)

    def cap(a, b, ra, rb, col):
        capsule(d, T(J[a]), T(J[b]), ra * k, rb * k, col)

    rot = J["rot"]
    # legs
    for t in ("L", "R"):
        cap("H" + t, "k" + t, 11, 9, SHORTS)
        cap("k" + t, "a" + t, 8, 6.2, SKIN)
        sgn = 1 if t == "R" else -1
        cap("a" + t, "f" + t, 6.5, 5.5, SHOE)
    # torso: trapezoid (shoulders wide, hips narrower) + pelvis
    poly = [T(J["SL"]), T(J["SR"]), T(add(J["HR"], (0, 0))), T(J["HL"])]
    pw = 6
    cs = T(J["S"])
    ch = T(J["H"])
    capsule(d, T(J["HL"]), T(J["HR"]), 12 * k, 12 * k, SHORTS)
    d.polygon(poly, fill=SHIRT)
    capsule(d, T(J["SL"]), T(J["SR"]), 8.5 * k, 8.5 * k, SHIRT)
    capsule(d, T(J["H"]), T(J["S"]), 17 * k, 16 * k, SHIRT)
    # neck + head
    capsule(d, T(J["S"]), T(J["head"]), 5 * k, 5 * k, SKIN)
    hx, hy = T(J["head"])
    r = LEN["head"] * k
    d.ellipse([hx - r, hy - r, hx + r, hy + r], fill=SKIN)
    ha = math.radians(J["head_a"])
    ux, uy = math.sin(ha), -math.cos(ha)  # up of the head on screen
    px, py = math.cos(ha), math.sin(ha)
    c = math.degrees(math.atan2(uy, ux))
    d.pieslice([hx - r, hy - r, hx + r, hy + r], c - 95, c + 95, fill=HAIR)
    if J.get("face", 1):
        for sg in (-1, 1):
            ex, ey = hx + px * sg * r * 0.38 - ux * r * 0.05, hy + py * sg * r * 0.38 - uy * r * 0.05
            d.ellipse([ex - 2 * k, ey - 2 * k, ex + 2 * k, ey + 2 * k], fill=(30, 30, 40))
    if hilite:
        ov = Image.new("RGBA", img.size, (0, 0, 0, 0))
        od = ImageDraw.Draw(ov, "RGBA")
        def seg(a, b, f0, f1, w):
            pa = (a[0] + (b[0] - a[0]) * f0, a[1] + (b[1] - a[1]) * f0)
            pb = (a[0] + (b[0] - a[0]) * f1, a[1] + (b[1] - a[1]) * f1)
            capsule(od, T(pa), T(pb), w * k, w * k, HILITE)
        if hilite in ("abs", "obliques", "serratus"):
            seg(J["H"], J["S"], 0.12, 0.62, 9 if hilite == "abs" else 13)
        elif hilite in ("chest", "back", "lats"):
            seg(J["H"], J["S"], 0.55, 0.92, 13)
        elif hilite in ("shoulders", "traps"):
            for t in ("L", "R"):
                disc(od, T(J["S" + t]), 9 * k, HILITE)
        elif hilite in ("quads", "hamstrings", "glutes"):
            for t in ("L", "R"):
                seg(J["H" + t], J["k" + t], 0.1, 0.9, 8)
        elif hilite == "calves":
            for t in ("L", "R"):
                seg(J["k" + t], J["a" + t], 0.1, 0.9, 6)
        elif hilite in ("biceps", "triceps"):
            for t in ("L", "R"):
                seg(J["S" + t], J["e" + t], 0.1, 0.9, 6)
        elif hilite == "forearms":
            for t in ("L", "R"):
                seg(J["e" + t], J["w" + t], 0.1, 0.9, 5)
        img = Image.alpha_composite(img, ov)
        d = ImageDraw.Draw(img, "RGBA")
    if equip:
        equip(d, T, J, s)
    for t in ("L", "R"):
        sh = "S" + t
        capsule(d, T(J[sh]), T(J["e" + t]), 7.8 * k, 6.4 * k, SHIRT)
        capsule(d, T(J["e" + t]), T(J["w" + t]), 6.2 * k, 5.0 * k, SKIN)
        disc(d, T(J["w" + t]), 6.3 * k, SKIN)
    if front:
        front(d, T, J, s)
    return img.convert("RGB").resize((size, size), Image.LANCZOS)


def fx_dumbbell(anchor, size=1.0):
    def fn(d, T, J, s):
        x, y = T(J[anchor])
        k = s * SS * size
        d.rounded_rectangle([x - 15 * k, y - 2.6 * k, x + 15 * k, y + 2.6 * k], radius=2 * k, fill=METAL)
        for dx in (-14, 14):
            d.rounded_rectangle([x + (dx - 4.5) * k, y - 11 * k, x + (dx + 4.5) * k, y + 11 * k], radius=3 * k, fill=EQUIP)
    return Item(fn, lambda J: [add(J[anchor], (-20, -14)), add(J[anchor], (20, 14))])


def rot_pt(p, th, pv):
    c, s_ = math.cos(math.radians(th)), math.sin(math.radians(th))
    x, y = p[0] - pv[0], p[1] - pv[1]
    return (pv[0] + x * c - y * s_, pv[1] + x * s_ + y * c)


def rotate_kw(kw, th, pv, dy=0.0):
    """Rotate a profile key pose (clockwise on screen by th degrees) about pv, then lift by -dy."""
    out = dict(kw)
    for k_ in ("A", "hip", "W", "E", "W2", "E2", "A2"):
        if out.get(k_) is not None:
            q = rot_pt(out[k_], th, pv)
            out[k_] = (q[0], q[1] - dy)
    for k_ in ("torso", "head", "foot", "foot2", "shin", "thigh"):
        if k_ in out and out[k_] is not None:
            out[k_] = out[k_] + th
    if "head" not in out:
        out["head"] = out.get("torso", 0) + th
    for k_ in ("FA", "FL"):
        if out.get(k_) is not None:
            out[k_] = (out[k_][0] - th, out[k_][1] - th)
    for k_ in ("uarm", "farm"):
        if k_ in out and out[k_] is not None:
            out[k_] = out[k_] - th
    if out.get("hand") is not None:
        h = rot_pt(out["hand"], th, (0, 0))
        out["hand"] = h
    return out


def torso_pad(f0, f1, off, r=8, col=(70, 78, 100)):
    """Machine pad following the front of the torso (mid layer)."""
    def pts(J):
        h, sh = J["hip"], J["shoulder"]
        t = math.radians(J["torso_a"])
        n = (math.cos(t), math.sin(t))
        a = (h[0] + (sh[0] - h[0]) * f0 + n[0] * off, h[1] + (sh[1] - h[1]) * f0 + n[1] * off)
        b = (h[0] + (sh[0] - h[0]) * f1 + n[0] * off, h[1] + (sh[1] - h[1]) * f1 + n[1] * off)
        return a, b

    def fn(d, T, J, s):
        a, b = pts(J)
        capsule(d, T(a), T(b), r * s * SS, r * s * SS, col)
    return Item(fn, lambda J: list(pts(J)))


def held_pair(anchor="wrist", kind="dumbbell"):
    """Weight held in both hands that can pass behind the torso (J['behind']): returns (back item, front item)."""
    base = {"dumbbell": lambda: dumbbell(anchor), "kettlebell": lambda: kettlebell(anchor, "down", r=10),
            "ball": lambda: ball_at(anchor, 14)}[kind]()
    def back_fn(d, T, J, s):
        if J["behind"]:
            base(d, T, J, s)
    def front_fn(d, T, J, s):
        if not J["behind"]:
            base(d, T, J, s)
    return Item(back_fn, base.ext), Item(front_fn, base.ext)


def ball_at(anchor, r=14, col=ACCENT):
    def fn(d, T, J, s):
        c = T(J[anchor])
        disc(d, c, r * s * SS, col)
        disc(d, (c[0] - r * 0.3 * s * SS, c[1] - r * 0.3 * s * SS), r * 0.25 * s * SS, (240, 160, 120))
    return Item(fn, lambda J: [add(J[anchor], (-r - 2, -r - 2)), add(J[anchor], (r + 2, r + 2))])


def rope_front(handle_l="wL", handle_r="wR"):
    """Jump rope seen from the front: cubic curve between the hands, apex height J['ry'] (world y)."""
    def pts(J):
        p0, p3 = J[handle_l], J[handle_r]
        ry = J["ry"]
        p1, p2 = (p0[0] - 70, ry), (p3[0] + 70, ry)
        out = []
        for i in range(25):
            t = i / 24
            x = (1 - t) ** 3 * p0[0] + 3 * (1 - t) ** 2 * t * p1[0] + 3 * (1 - t) * t * t * p2[0] + t ** 3 * p3[0]
            y = (1 - t) ** 3 * p0[1] + 3 * (1 - t) ** 2 * t * p1[1] + 3 * (1 - t) * t * t * p2[1] + t ** 3 * p3[1]
            out.append((x, min(y, -0.5)))
        return out

    def fn(d, T, J, s):
        k = s * SS
        d.line([T(p) for p in pts(J)], fill=(214, 120, 60), width=int(2.6 * k), joint="curve")
        for h in (handle_l, handle_r):
            c = T(J[h])
            d.rounded_rectangle([c[0] - 3 * k, c[1] - 9 * k, c[0] + 3 * k, c[1] + 9 * k], radius=2.5 * k, fill=(60, 66, 84))
    return Item(fn, lambda J: pts(J))


def bike_items(C=(0, -40), crank=34):
    """Stationary bike: (scene item, crank/pedal item).  Crank follows the feet (J ankle / ankle2)."""
    def scene_fn(d, T, J, s):
        k = s * SS
        sx, sy = -50, -143
        hb = (62, -172)
        # floor stand
        for x0, x1 in ((-96, -36), (50, 118)):
            a, b = T((x0, -6)), T((x1, 0))
            d.rounded_rectangle([a[0], a[1], b[0], b[1]], radius=2 * k, fill=EQUIP)
        capsule(d, T(C), T((-70, -4)), 3.6 * k, 3.6 * k, BENCHC)
        capsule(d, T(C), T((84, -4)), 3.6 * k, 3.6 * k, BENCHC)
        # flywheel
        fc = T((74, -52))
        disc(d, fc, 27 * k, (170, 178, 196))
        disc(d, fc, 22 * k, (196, 203, 217))
        disc(d, fc, 4 * k, EQUIP)
        capsule(d, T(C), T((sx, sy + 8)), 3.6 * k, 3.6 * k, BENCHC)
        capsule(d, T(C), T((hb[0] - 4, hb[1] + 8)), 3.6 * k, 3.6 * k, BENCHC)
        capsule(d, T((hb[0] - 4, hb[1] + 8)), T(hb), 3.2 * k, 3.2 * k, BENCHC)
        capsule(d, T(hb), T((hb[0] + 14, hb[1] - 2)), 3 * k, 3 * k, EQUIP)
        # saddle
        capsule(d, T((sx - 16, sy)), T((sx + 14, sy - 1)), 6 * k, 5 * k, EQUIP)
        # far crank + pedal
        if "ankle2" in J:
            p = (J["ankle2"][0] + 12, J["ankle2"][1] + 8)
            capsule(d, T(C), T(p), 3 * k, 3 * k, METAL_D)
            d.rounded_rectangle([T(p)[0] - 9 * k, T(p)[1] - 2 * k, T(p)[0] + 9 * k, T(p)[1] + 2 * k], radius=k, fill=METAL_D)
        disc(d, T(C), 6 * k, EQUIP)

    def front_fn(d, T, J, s):
        k = s * SS
        p = (J["ankle"][0] + 12, J["ankle"][1] + 8)
        capsule(d, T(C), T(p), 3.4 * k, 3.4 * k, METAL)
        d.rounded_rectangle([T(p)[0] - 10 * k, T(p)[1] - 2.4 * k, T(p)[0] + 10 * k, T(p)[1] + 2.4 * k], radius=k, fill=METAL)
        disc(d, T(C), 4 * k, METAL_D)
    return Item(scene_fn, lambda J: [(-110, -190), (125, 0)]), Item(front_fn)


def rower_items(foot_x=105, rail_y=-40, front_x=205):
    def scene_fn(d, T, J, s):
        k = s * SS
        a, b = T((-130, rail_y - 3)), T((front_x - 30, rail_y + 3))
        d.rounded_rectangle([a[0], a[1], b[0], b[1]], radius=2 * k, fill=BENCHC)
        for x in (-124, front_x - 40):
            p, q = T((x - 3, rail_y + 3)), T((x + 3, 0))
            d.rectangle([p[0], p[1], q[0], q[1]], fill=BENCHC)
            f0, f1 = T((x - 14, -4)), T((x + 14, 0))
            d.rounded_rectangle([f0[0], f0[1], f1[0], f1[1]], radius=2 * k, fill=EQUIP)
        # flywheel cage
        fc = T((front_x, -50))
        disc(d, fc, 38 * k, (170, 178, 196))
        disc(d, fc, 30 * k, (196, 203, 217))
        disc(d, fc, 5 * k, EQUIP)
        p, q = T((front_x - 24, -38)), T((front_x + 6, 0))
        d.rectangle([p[0], p[1], q[0], q[1]], fill=BENCHC)
        # foot plate
        capsule(d, T((foot_x + 20, -10)), T((foot_x + 20, -74)), 4 * k, 4 * k, EQUIP)
        capsule(d, T((foot_x + 20, -10)), T((foot_x + 4, -10)), 3 * k, 3 * k, EQUIP)

    def seat_fn(d, T, J, s):
        k = s * SS
        x = J["hip"][0]
        a, b = T((x - 22, rail_y - 13)), T((x + 20, rail_y - 3))
        d.rounded_rectangle([a[0], a[1], b[0], b[1]], radius=4 * k, fill=(70, 78, 100))

    def chain_fn(d, T, J, s):
        k = s * SS
        p, q = T((front_x - 38, -62)), T(J["wrist"])
        d.line([p, q], fill=CABLEC, width=int(2 * k))
        c = T(J["wrist"])
        d.rounded_rectangle([c[0] - 2.8 * k, c[1] - 16 * k, c[0] + 2.8 * k, c[1] + 16 * k], radius=2 * k, fill=METAL) if False else d.rounded_rectangle([c[0] - 16 * k, c[1] - 2.8 * k, c[0] + 16 * k, c[1] + 2.8 * k], radius=2 * k, fill=METAL)
    return Item(scene_fn, lambda J: [(-135, -90), (front_x + 40, 0)]), Item(seat_fn), Item(chain_fn)
