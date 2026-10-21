"""Patterns for rehab / mobility / breathing / balance drills (agent z).

Same conventions as patterns_b.py (key poses rendered by extras_b.render_spec).  Extra "channel" trick: the mk() kwarg
`hand=(c0, c1)` is stored in J["hand_pt"]; chan(J, i) reads it back, so a key pose can carry two animation parameters
(breath, pulse, roller shift...) that the cue items interpolate for free.
"""
import math
from PIL import Image, ImageDraw
try:
    from . import extras_b as X
    from .patterns_b import make_spec, has, shoulder_of, hands_head
except ImportError:  # pragma: no cover
    import extras_b as X
    from patterns_b import make_spec, has, shoulder_of, hands_head

mk = X.mk
SS = X.SS
PATTERNS = {}
TEST_VARIANTS = {}
LYING_VIEW = (-135, -95, 150, 30)
ROLLC = (88, 112, 172)
ROLLT = (206, 216, 240)
WALLC = (205, 211, 224)


_mkf_orig = X.mkf


def _mkf_pin(**kw):
    """mkf with explicit elbows: eL / eR = (x, y) override the IK elbow (forearm may be foreshortened)."""
    eL, eR = kw.pop("eL", None), kw.pop("eR", None)
    J = _mkf_orig(**kw)
    for tag, e, w in (("L", eL, kw.get("wL")), ("R", eR, kw.get("wR"))):
        if e is not None:
            J["e" + tag] = (float(e[0]), float(e[1]))
            if w is not None:
                J["w" + tag] = (float(w[0]), float(w[1]))
    return J


if X.mkf is _mkf_orig:
    X.mkf = _mkf_pin


def pat(name, *tests):
    def deco(fn):
        PATTERNS[name] = fn
        TEST_VARIANTS[name] = list(tests) or [("none", [], None)]
        return fn
    return deco


# ------------------------------------------------------------------------------------------------ small helpers
def overlay(d, fn):
    """Alpha-correct drawing: fn(od) draws RGBA shapes on a transparent layer that is composited onto d's image."""
    img = d._image
    ov = Image.new("RGBA", img.size, (0, 0, 0, 0))
    fn(ImageDraw.Draw(ov))
    img.alpha_composite(ov)


def chan(J, i=0):
    return J["hand_pt"][i] - J["wrist"][i]


def npt(J, f0=None):
    th = math.radians(J["torso_a"])
    return (math.cos(th), math.sin(th))


def on_torso(J, f, off=0.0):
    h, s = J["hip"], J["shoulder"]
    n = npt(J)
    return (h[0] + (s[0] - h[0]) * f + n[0] * off, h[1] + (s[1] - h[1]) * f + n[1] * off)


def cap_item(a_fn, b_fn, r, col, extent=True):
    def fn(d, T, J, s):
        X.capsule(d, T(a_fn(J)), T(b_fn(J)), r * s * SS, r * s * SS, col)
    return X.Item(fn, (lambda J: [a_fn(J), b_fn(J)]) if extent else None)


def bump(f0, f1, amp, i=0, r=14.2, tint=True):
    """Torso region that rises with channel i: belly / chest breathing cue (tinted orange so the cue reads)."""
    def fn(d, T, J, s):
        c = chan(J, i)
        a, b = on_torso(J, f0, amp * c), on_torso(J, f1, amp * c)
        X.capsule(d, T(a), T(b), r * s * SS, r * s * SS, X.SHIRT)
        if tint:
            overlay(d, lambda od: X.capsule(od, T(a), T(b), (r - 2) * s * SS, (r - 2) * s * SS,
                                            (255, 120, 20, int(40 + 110 * c))))
    return X.Item(fn)


def dent(f0, f1, depth, i=0, ry=13.0):
    """Belly drawn in: a background-coloured notch carved into the front of the torso (stomach vacuum)."""
    def fn(d, T, J, s):
        c = chan(J, i)
        k = s * SS
        n = npt(J)
        m = on_torso(J, (f0 + f1) / 2, 14.2 + ry - depth * c)
        h, sh = J["hip"], J["shoulder"]
        half = math.hypot(sh[0] - h[0], sh[1] - h[1]) * (f1 - f0) / 2
        ang = math.atan2(sh[1] - h[1], sh[0] - h[0])
        pts = []
        for j in range(0, 33):
            t = 2 * math.pi * j / 32
            u, v = half * math.cos(t), ry * math.sin(t)
            pts.append(T((m[0] + u * math.cos(ang) - v * math.sin(ang), m[1] + u * math.sin(ang) + v * math.cos(ang))))
        d.polygon(pts, fill=X.BG + (255,))
        # keep the orange abs tint along the dent edge
        p0, p1 = on_torso(J, f0 + 0.05, 14.2 - depth * c * 0.9), on_torso(J, f1 - 0.05, 14.2 - depth * c * 0.9)
        overlay(d, lambda od: X.capsule(od, T(p0), T(p1), 3.0 * k, 3.0 * k, (255, 120, 20, 150)))
    return X.Item(fn)


def glow_pts(fn_pts, r, i=0, lo=0.0, shrink=0.0, ring=False):
    """Orange glow at a point computed from J, alpha follows channel i (pulse cue)."""
    def fn(d, T, J, s):
        c = chan(J, i)
        p = fn_pts(J)
        x, y = T(p)
        k = s * SS
        rr = (r - shrink * c) * k
        a = int(40 + 175 * (lo + (1 - lo) * c))
        def go(od):
            if ring:
                od.ellipse([x - rr, y - rr, x + rr, y + rr], outline=(255, 120, 20, 230), width=int(3 * k))
                od.ellipse([x - rr * 0.55, y - rr * 0.55, x + rr * 0.55, y + rr * 0.55], fill=(255, 120, 20, a))
            else:
                od.ellipse([x - rr, y - rr, x + rr, y + rr], fill=(255, 120, 20, a))
        overlay(d, go)
    return X.Item(fn, lambda J: [add(fn_pts(J), (-r, -r)), add(fn_pts(J), (r, r))])


def add(p, q):
    return (p[0] + q[0], p[1] + q[1])


def seg_glow(a_key, b_key, f0, f1, w, off, i=0, lo=0.15):
    """Muscle overlay on a limb segment (J keys a_key -> b_key) with alpha = pulse channel."""
    def fn(d, T, J, s):
        c = chan(J, i)
        a, b = J[a_key], J[b_key]
        dx, dy = b[0] - a[0], b[1] - a[1]
        n = math.hypot(dx, dy) or 1
        nx, ny = dy / n, -dx / n
        if ny > 0:
            nx, ny = -nx, -ny
        p0 = (a[0] + dx * f0 + nx * off, a[1] + dy * f0 + ny * off)
        p1 = (a[0] + dx * f1 + nx * off, a[1] + dy * f1 + ny * off)
        ov = (255, 120, 20, int(70 + 130 * (lo + (1 - lo) * c)))
        overlay(d, lambda od: X.capsule(od, T(p0), T(p1), w * s * SS, w * s * SS, ov))
    return X.Item(fn)


def closed_eyes():
    """Front layer: cover the eye with skin and draw a closed-lid line."""
    def fn(d, T, J, s):
        k = s * SS
        sx, sy = T(J["shoulder"])
        hx, hy = T(J["head"])
        ux, uy = hx - sx, hy - sy
        un = math.hypot(ux, uy) or 1
        ux, uy = ux / un, uy / un
        t = math.radians(J["head_a"])
        nx, ny = math.cos(t), math.sin(t)
        r = X.LEN["head"] * k
        ex, ey = hx + nx * r * 0.55 + ux * r * 0.05, hy + ny * r * 0.55 + uy * r * 0.05
        d.ellipse([ex - 3.2 * k, ey - 3.2 * k, ex + 3.2 * k, ey + 3.2 * k], fill=X.SKIN)
        px, py = -uy, ux
        d.line([(ex - px * 2.6 * k, ey - py * 2.6 * k), (ex + px * 2.6 * k, ey + py * 2.6 * k)], fill=(30, 30, 40),
               width=int(1.3 * k))
    return X.Item(fn)


def wall(x, top=-330, w=22):
    return X.box(x, top, x + w, 0, WALLC, 2)


def hands_on(kw, pairs):
    return dict(kw, **pairs)


# ================================================================================================== BREATHING
def _supine(legs="bent", hipx=0.0):
    hip = (hipx, -14)
    base = dict(hip=hip, torso=-90, head=-92, foot=0, foot2=0)
    if legs == "bent":
        base.update(A=(hipx + 84, -6), A2=(hipx + 88, -6), kh=(0, -1), kh2=(0, -1))
    elif legs == "9090":
        base.update(A=(hipx + 70, -90), A2=(hipx + 72, -90), kh=(-1, -1), kh2=(-1, -1), foot=-90, foot2=-90)
    else:
        base.update(A=(hipx + 144, -8), A2=(hipx + 146, -8), kh=(0, -1), kh2=(0, -1), foot=-75, foot2=-75)
    return base


def _hand_belly_key(base, c, amp_b=7.0, amp_c=0.0, far_on_chest=True):
    """Supine key pose: near hand on the belly (rides the belly), far hand on the chest -> channel c."""
    kw = dict(base)
    S = shoulder_of(kw)
    h = kw["hip"]
    kw["E"] = (S[0] + 44, h[1] - 6)
    kw["W"] = (h[0] - 24, h[1] - 18 - amp_b * c)
    kw["ah"] = (0, -1)
    if far_on_chest:
        kw["E2"] = (S[0] + 14, h[1] - 8)
        kw["W2"] = (h[0] - 66, h[1] - 18 - amp_c * c)
        kw["front2"] = True
    kw["hand"] = (c, 0)
    return kw


@pat("breathing", ("none", [], "abs"), ("none", ["lying"], "abs"), ("none", ["seated"], "abs"),
     ("none", ["wall"], "abs"), ("none", ["90_90"], "abs"), ("none", ["vacuum"], "abs"), ("none", ["standing"], "abs"),
     ("none", ["relaxed"], "abs"))
def breathing(eq, var, hil):
    hil = None
    if has(var, "standing", "seated"):
        return _upright_breath(var, hil)
    scene = X.mat(-200, 190)
    if has(var, "wall"):
        base = _supine("9090")
        scene = X.many(scene, wall(80, -330))
        for k in ("A", "A2"):
            base[k] = (72 if k == "A" else 73, -90)
    elif has(var, "90_90"):
        base = _supine("9090")
        scene = X.many(scene, X.box(20, -84, 104, 0, X.BENCHC, 4))
    else:
        base = _supine("bent")
    vac = has(var, "vacuum")
    cs = [0.0, 1.0]
    keys = []
    for c in cs:
        # vacuum: belly sinks in (amp < 0) on the "in" key; the other drills: belly rises
        kw = _hand_belly_key(base, c, amp_b=(-7.0 if vac else 9.0), amp_c=(0 if vac else 3.0))
        if vac:
            S0 = shoulder_of(base)
            for k_ in ("E2", "W2", "front2"):
                kw.pop(k_, None)
            kw.pop("E", None)
            kw["W"] = (S0[0] + 94, -7)
            kw["ah"] = (0.3, 1)
        keys.append(kw)
    equip = X.many(dent(0.06, 0.52, 9.0)) if vac else X.many(bump(0.05, 0.50, 9.0), bump(0.62, 0.95, 3.0, tint=False))
    hold = (1100, 900)
    sp = make_spec(keys, equip, scene, hilite=hil, lying=True, hold=hold, steps=10, view=LYING_VIEW)
    return sp


def _upright_breath(var, hil):
    seated = has(var, "seated")
    if seated:
        hip = (0, -58)
        base = dict(A=(70, -6), hip=hip, torso=0, head=0, kh=(1, 0), foot=0)
        scene = X.many(X.box(-24, -48, 30, -34, X.BENCHC, 5), X.post_rect(-4, -34, 4, 0))
    else:
        base = dict(A=(0, -6), hip=(0, -152), torso=0, head=0, kh=(1, 0), foot=0)
        scene = None
    keys = []
    for c in (0.0, 1.0):
        kw = dict(base)
        h = kw["hip"]
        S = shoulder_of(kw)
        kw["W"] = (h[0] + 17, h[1] - 44 - 3 * c)
        kw["E"] = (h[0] - 14, h[1] - 52)
        kw["ah"] = (-1, 0.2)
        kw["hand"] = (c, 0)
        keys.append(kw)
    equip = X.many(bump(0.1, 0.5, 4.5), bump(0.55, 0.95, 5.5))
    return make_spec(keys, equip, scene, hilite=hil, hold=(1000, 900), steps=10)


# ================================================================================================== PELVIC
def _pelvis_marker():
    """Pelvis drawn as a short orange bar through the hip; its angle follows channel 0 (-1 anterior .. +1 posterior)."""
    def fn(d, T, J, s):
        c = chan(J, 0)
        h = J["hip"]
        ang = math.radians(-90 + 24 * (1 - 2 * (1 - c)) * 0.0 + 22 * (1 - c) - 11 * c * 0)
        # pelvic bar: vertical-ish line in the body; tilts about the hip
        a = math.radians(6 + 26 * (1 - c) - 6 * c)
        u = (math.sin(a), -math.cos(a))
        p0 = (h[0] - u[0] * 17 + 0, h[1] - u[1] * 17)
        p1 = (h[0] + u[0] * 17, h[1] + u[1] * 17)
        X.capsule(d, T(p0), T(p1), 3.4 * s * SS, 3.4 * s * SS, (255, 120, 20, 235))
        X.disc(d, T(p1), 4.4 * s * SS, (255, 120, 20, 235))
    return X.Item(fn, lambda J: [add(J["hip"], (-20, -20)), add(J["hip"], (20, 20))])


def _lumbar_gap():
    """Dark crescent between the lower back and the floor: big when the back is arched, closed when pressed flat."""
    def fn(d, T, J, s):
        c = chan(J, 0)
        h = J["hip"]
        k = s * SS
        g = 8.5 * (1 - c)
        if g < 0.6:
            return
        cx = h[0] - 34
        pts = []
        for i in range(0, 13):
            t = i / 12
            x = cx - 22 + 44 * t
            y = -g * math.sin(math.pi * t) * 1.0
            pts.append(T((x, y - 0.2)))
        pts += [T((cx + 22, -0.2)), T((cx - 22, -0.2))]
        overlay(d, lambda od: od.polygon(pts, fill=(40, 48, 70, 170)))
    return X.Item(fn)


@pat("pelvic_tilt", ("none", [], "abs"), ("none", ["wave"], "abs"))
def pelvic_tilt(eq, var, hil):
    hil = hil or "abs"
    base = _supine("bent")
    keys = []
    mat = X.mat(-200, 190)
    wave = has(var, "wave")
    seq = [(0.0, 0.0), (1.0, 0.0)] + ([(1.0, 1.0)] if wave else [])
    for c, lift in seq:
        kw = dict(base)
        kw["hip"] = (0, -14 - 9 * lift)
        kw["A"] = (84, -6)
        kw["A2"] = (88, -6)
        S = X.add(kw["hip"], X.vup(-90, 92))
        kw["W"] = (S[0] + 94, -7)
        kw["ah"] = (0.3, 1)
        kw["W2"] = (S[0] + 98, -7)
        kw["ah2"] = (0.3, 1)
        kw["torso"] = -90 + 4 * lift
        kw["hand"] = (c, lift)
        keys.append(kw)
    equip = X.many(_lumbar_gap(), _pelvis_marker())
    return make_spec(keys, equip, mat, hilite=hil, lying=True, hold=(900, 700), steps=9, view=LYING_VIEW)


# --------------------------------------------------------------------------------------------- kegels
@pat("pelvic_floor", ("none", [], None), ("none", ["quick"], None), ("none", ["reverse"], None),
     ("none", ["seated"], None))
def pelvic_floor(eq, var, hil):
    quick = has(var, "quick")
    rev = has(var, "reverse")
    seated = has(var, "seated")
    if seated:
        base = dict(A=(70, -6), hip=(0, -58), torso=0, head=0, kh=(1, 0), foot=0)
        base["W"] = (40, -92)
        base["ah"] = (0, 1)
        scene = X.many(X.box(-24, -48, 30, -34, X.BENCHC, 5), X.post_rect(-4, -34, 4, 0))
        pf = lambda J: (J["hip"][0] - 1, J["hip"][1] + 14)
    else:
        base = _supine("bent")
        S = shoulder_of(base)
        base["W"] = (S[0] + 94, -7)
        base["ah"] = (0.3, 1)
        base["W2"] = (S[0] + 98, -7)
        base["ah2"] = (0.3, 1)
        scene = X.mat(-200, 190)
        pf = lambda J: (J["hip"][0] + 2, J["hip"][1] + 6)
    keys = []
    pulses = [0, 1, 0, 1, 0, 1, 0] if quick else [0, 1]
    for c in (pulses if quick else [0, 1]):
        v = (1 - c) if rev else c
        kw = dict(base)
        kw["hand"] = (v, 0)
        keys.append(kw)
    equip = glow_pts(pf, 19, i=0, lo=0.0, shrink=6.0 if not rev else -6.0, ring=True)
    if quick:
        return make_spec(keys, equip, scene, lying=not seated, loop="cycle", steps=2, hold=(500, 400), view=None if seated else LYING_VIEW)
    return make_spec(keys, equip, scene, lying=not seated, hold=(1100, 800), steps=9)


# ================================================================================================== QUAD SET
@pat("quad_set", ("mat", [], "quads"))
def quad_set(eq, var, hil):
    hip = (0, -14)
    base = dict(hip=hip, torso=-90, head=-92, A=(146, -9), kh=(0, -1), A2=(70, -6), kh2=(0, -1), foot=-60, foot2=0)
    S = X.add(hip, X.vup(-90, 92))
    base["W"] = (S[0] + 94, -7)
    base["ah"] = (0.3, 1)
    keys = []
    for c in (0.0, 1.0):
        kw = dict(base)
        kw["foot"] = -60 - 28 * c
        kw["A"] = (146, -9 - 5 * c)
        kw["hand"] = (c, 0)
        keys.append(kw)
    # towel roll under the knee, quad glows when it works
    knee = (73, -8)
    towel = X.pad((72, -8), (90, -8), r=8, col=(236, 210, 150))
    scene = X.many(X.mat(-200, 190), towel)
    equip = seg_glow("knee", "hip", 0.1, 0.9, 9, 6, lo=0.0)
    # hip->knee glow uses knee/hip joints
    return make_spec(keys, equip, scene, lying=True, hold=(900, 800), steps=8, view=(-135, -80, 170, 25))


# ================================================================================================== DORSIFLEXION
@pat("dorsiflexion", ("band", [], None))
def dorsiflexion(eq, var, hil):
    hip = (0, -14)
    base = dict(hip=hip, torso=-90, head=-92, A=(146, -9), kh=(0, -1), A2=(146, -8), kh2=(0, -1))
    S = X.add(hip, X.vup(-90, 92))
    base["W"] = (S[0] + 94, -7)
    base["ah"] = (0.3, 1)
    keys = []
    for c in (0.0, 1.0):
        kw = dict(base)
        kw["foot"] = -34 - 70 * c
        kw["foot2"] = -80
        kw["hand"] = (c, 0)
        keys.append(kw)
    post = (230, -30)
    scene = X.many(X.mat(-200, 190), X.box(post[0] - 8, -60, post[0] + 8, 0, X.BENCHC, 3))
    equip = X.many(X.band_line(post, to="toe", post=False), seg_glow("knee", "ankle", 0.2, 0.8, 4.5, 5.5, lo=0.0))
    return make_spec(keys, equip, scene, lying=True, hold=(800, 700), steps=8, view=(-135, -80, 250, 25))


# ================================================================================================== NECK FLEXION
def _plate(anchor="head"):
    def fn(d, T, J, s):
        k = s * SS
        t = math.radians(J["head_a"])
        n = (math.cos(t), math.sin(t))
        u = (-n[1], n[0])
        c = (J["head"][0] + n[0] * 19, J["head"][1] + n[1] * 19)
        a = (c[0] - u[0] * 17, c[1] - u[1] * 17)
        b = (c[0] + u[0] * 17, c[1] + u[1] * 17)
        X.capsule(d, T(a), T(b), 4 * k, 4 * k, X.EQUIP)
        X.capsule(d, T((a[0] + n[0] * 5, a[1] + n[1] * 5)), T((b[0] + n[0] * 5, b[1] + n[1] * 5)), 2.4 * k, 2.4 * k,
                  X.METAL)
    return X.Item(fn, lambda J: [add(J["head"], (-36, -36)), add(J["head"], (36, 36))])


@pat("neck_flexion", ("bench", [], "traps"))
def neck_flexion(eq, var, hil):
    hil = hil or "traps"
    top = 46
    hip = (60, -top - 14)
    base = dict(hip=hip, torso=-90, head=-124, A=(hip[0] + 62, -6), kh=(0, -1), foot=0, A2=(hip[0] + 66, -6), kh2=(0, -1),
                foot2=0)
    S = X.add(hip, X.vup(-90, 92))
    keys = []
    for c, hd in ((0.0, -126), (1.0, -34)):
        kw = dict(base)
        kw["head"] = hd
        H = X.add(S, X.vup(hd, 28))
        t = math.radians(hd)
        pl = (H[0] + math.cos(t) * 23, H[1] + math.sin(t) * 23)
        kw["W"] = pl
        kw["ah"] = (0.5, -1)
        keys.append(kw)
    scene = X.bench(S[0] - 6, hip[0] + 40, top, thick=12, legs=(0.12, 0.88))
    return make_spec(keys, _plate(), scene, hilite=hil, lying=True, hold=(800, 700), steps=8)


# ================================================================================================== CALM (meditation / rest)
def _timer(x, y, r=17):
    def fn(d, T, J, s):
        k = s * SS
        c = chan(J, 1)
        px, py = T((x, y))
        d.ellipse([px - r * k, py - r * k, px + r * k, py + r * k], fill=(255, 255, 255, 235), outline=(120, 128, 150, 255),
                  width=int(2 * k))
        d.pieslice([px - (r - 3) * k, py - (r - 3) * k, px + (r - 3) * k, py + (r - 3) * k], -90, -90 + 358 * max(c, 0.02),
                   fill=(255, 140, 50, 255))
    return X.Item(fn, lambda J: [(x - r - 2, y - r - 2), (x + r + 2, y + r + 2)])


def _aura(cx, cy):
    def fn(d, T, J, s):
        k = s * SS
        c = chan(J, 0)
        px, py = T((cx, cy))
        for i, base_r in enumerate((36, 52, 68)):
            rr = (base_r + 5 * c * (i + 1)) * k
            d.ellipse([px - rr, py - rr, px + rr, py + rr], outline=(255, 150, 70, int(120 - 28 * i - 30 * c)),
                      width=int(2.2 * k))
    return X.Item(fn)


@pat("calm", ("none", ["seated"], None), ("none", ["standing"], None))
def calm(eq, var, hil):
    if has(var, "standing"):  # rest between sets: stand relaxed, hands on hips, timer ring
        keys = []
        for c in (0.0, 1.0):
            kw = dict(A=(0, -6), hip=(0, -152), torso=0, head=-4, kh=(1, 0), foot=0)
            h = kw["hip"]
            kw["W"] = (h[0] + 10, h[1] - 6)
            kw["E"] = (h[0] - 20, h[1] - 52)
            kw["ah"] = (-1, 0.4)
            kw["hand"] = (c, c)
            keys.append(kw)
        scene = _timer(75, -250)
        equip = X.many(bump(0.55, 0.95, 4.0))
        return make_spec(keys, equip, scene, hold=(900, 700), steps=10)
    # seated cross-legged meditation: breath rises, soft rings
    keys = []
    for c in (0.0, 1.0):
        kw = dict(A=(5, -8), shin=90, thigh=-85, torso=0, head=-2, foot=-20,
                  FL=(87, -87), foot2=-20, hand=(c, 0))
        kw["W"] = (58, -26)
        kw["ah"] = (-0.6, 1)
        kw["W2"] = (66, -28)
        kw["ah2"] = (-0.6, 1)
        kw["front2"] = False
        kw.pop("A", None)
        kw["A"] = (5, -8)
        keys.append(kw)
    equip = X.many(bump(0.55, 0.95, 3.5))
    return make_spec(keys, equip, _aura(0, -80), hold=(1100, 900), steps=4, view=(-100, -165, 100, 25))


# ================================================================================================== FOAM ROLL
def _roller(r=15, ball=False, rx=0.0):
    """Roller (end-on circle) resting on the floor at x = rx; spins as the body slides (channel 0 = slide in px)."""
    def fn(d, T, J, s):
        k = s * SS
        sh = chan(J, 0)
        cx, cy = T((rx, -r))
        d.ellipse([cx - r * k, cy - r * k, cx + r * k, cy + r * k], fill=ROLLC)
        a0 = math.radians(-90 + math.degrees(sh / r))
        for j in range(3 if not ball else 1):
            a = a0 + j * 2 * math.pi / 3
            d.ellipse([cx + math.cos(a) * r * 0.62 * k - 2.4 * k, cy + math.sin(a) * r * 0.62 * k - 2.4 * k,
                       cx + math.cos(a) * r * 0.62 * k + 2.4 * k, cy + math.sin(a) * r * 0.62 * k + 2.4 * k], fill=ROLLT)
        d.ellipse([cx - 3 * k, cy - 3 * k, cx + 3 * k, cy + 3 * k], fill=(60, 78, 128))
    return X.Item(fn, lambda J: [(rx - r, -2 * r), (rx + r, 0)])


def _contact(rx=0.0, r=15, dy=-4):
    def fn(d, T, J, s):
        k = s * SS
        x, y = T((rx, -2 * r + dy))
        rr = 11 * k
        overlay(d, lambda od: od.ellipse([x - rr, y - rr, x + rr, y + rr], fill=(255, 120, 20, 150)))
    return X.Item(fn)


def shift_kw(kw, dx):
    out = dict(kw)
    for k in ("A", "hip", "W", "E", "W2", "E2", "A2"):
        if out.get(k) is not None:
            out[k] = (out[k][0] + dx, out[k][1])
    out["hand"] = (dx, 0)
    return out


def _fr(kw, seg, f, rx=0.0):
    """x offset so that the point at fraction f of body segment `seg` ('thigh','shin','torso') sits at x=rx."""
    J = mk(**kw)
    a, b = {"thigh": ("hip", "knee"), "shin": ("knee", "ankle"), "torso": ("hip", "shoulder")}[seg]
    return rx - (J[a][0] + (J[b][0] - J[a][0]) * f)


def _roll_pose(part, var):
    """-> (base key pose with the roller at x=0, anchor segment, fraction, travel)"""
    if part == "quads":
        hy = -50
        base = dict(hip=(0, hy), A=(-144, -22), kh=(0, -1), torso=82, head=40, foot=70)
        S = mk(**base)["shoulder"]
        base.update(E=(S[0] + 4, -9), W=(S[0] + 46, -9), ah=(0, 1))
        return base, "thigh", 0.55, 22
    if part == "calves":
        base = dict(hip=(0, -39), A=(146, -38), kh=(0, -1), torso=-24, head=-14, foot=-60,
                    A2=(147, -54), kh2=(0, -1), foot2=-60)
        S = mk(**base)["shoulder"]
        base.update(W=(S[0] - 34, -6), ah=(-1, 0.3))
        return base, "shin", 0.55, 22
    if part == "hamstrings":
        base = dict(hip=(0, -52), A=(146, -9), kh=(0, -1), torso=-24, head=-14, foot=-70)
        S = mk(**base)["shoulder"]
        base.update(W=(S[0] - 34, -6), ah=(-1, 0.3))
        return base, "thigh", 0.5, 22
    if part == "glutes":
        r = 7 if has(var, "ball") else 15
        base = dict(hip=(0, -2 * r - 12), A=(66, -6), kh=(0, -1), A2=(70, -6), kh2=(0, -1), torso=-34, head=-26, foot=0,
                    foot2=0)
        S = mk(**base)["shoulder"]
        base.update(W=(S[0] - 22, -6), ah=(-1, 0.3))
        return base, "torso", 0.0, 14
    if part == "adductors":
        base = dict(hip=(0, -46), A=(-146, -24), kh=(0, -1), torso=82, head=40, foot=70, FL=(80, -75), foot2=-80)
        S = mk(**base)["shoulder"]
        base.update(E=(S[0] + 4, -9), W=(S[0] + 46, -9), ah=(0, 1))
        return base, "adduct", 0.5, 20
    if part == "it_band":
        base = dict(hip=(0, -40), torso=-90, head=-92, A=(96, -6), kh=(0, -1), A2=(146, -42), kh2=(0, -1), foot=0, foot2=-80)
        S = mk(**base)["shoulder"]
        base.update(E2=(S[0] + 30, -9), W2=(S[0] + 52, -9), front2=False, W=(S[0] + 34, -6), ah=(-1, 0.2))
        return base, "thigh", 0.5, 22
    if part == "tibialis":
        base = dict(hip=(0, -84), A=(-70, -36), kh=(1, 0.3), torso=88, head=60, foot=100)
        S = mk(**base)["shoulder"]
        base.update(W=(S[0] + 2, -6), ah=(-0.3, 1))
        return base, "shin", 0.8, 14
    # upper back
    base = dict(hip=(0, -46), torso=-92, head=-100, A=(66, -6), kh=(0, -1), foot=0)
    base = hands_head(base)
    return base, "torso", 0.78, 24


@pat("foam_roll", ("none", ["quads"], "quads"), ("none", ["calves"], "calves"), ("none", ["hamstrings"], "hamstrings"),
     ("none", ["glutes"], "glutes"), ("none", ["adductors"], None), ("none", ["it_band"], "quads"),
     ("none", ["tibialis"], "calves"), ("none", ["upper_back"], "back"), ("none", ["glutes", "ball"], "glutes"))
def foam_roll(eq, var, hil):
    part = next((v for v in var if v in ("quads", "calves", "hamstrings", "glutes", "adductors", "it_band", "tibialis",
                                          "upper_back")), "quads")
    base, seg, f, trav = _roll_pose(part, var)
    base = dict(base)
    if seg == "torso" and f == 0.0:
        pass
    off = -37.0 if seg == "adduct" else (_fr(base, seg, f, 0.0) if seg != "torso" or f > 0 else 0.0)
    base = shift_kw(base, off)
    ball = has(var, "ball")
    keys = [shift_kw(base, -trav), shift_kw(base, trav)]
    for kw in keys:  # channel = slide relative to the neutral pose
        pass
    rr = 7 if ball else 15
    keys = []
    for sgn in (-1, 1):
        k = shift_kw(base, sgn * trav)
        k["hand"] = (sgn * trav, 0)
        keys.append(k)
    scene = None
    equip = X.many(_roller(rr, ball), _contact(0.0, rr))
    return make_spec(keys, equip, scene, hilite=hil, lying=part != "tibialis", hold=(700, 500), steps=9)


# ================================================================================================== ROTATOR CUFF ROTATION
def _vdumbbell(anchor="wL", size=0.9):
    def fn(d, T, J, s):
        x, y = T(J[anchor])
        k = s * SS * size
        d.rounded_rectangle([x - 2.6 * k, y - 15 * k, x + 2.6 * k, y + 15 * k], radius=2 * k, fill=X.METAL)
        for dy in (-14, 14):
            d.rounded_rectangle([x - 11 * k, y + (dy - 4.5) * k, x + 11 * k, y + (dy + 4.5) * k], radius=3 * k, fill=X.EQUIP)
    return X.Item(fn, lambda J: [add(J[anchor], (-14, -20)), add(J[anchor], (14, 20))])


def _front_rot(eq, var, hil):
    internal = has(var, "reverse")
    H = (0, -152)
    S = (0, -244)
    SL = (S[0] - 17, S[1])
    E0 = (SL[0] - 3, SL[1] + 50)

    def key(phi):
        r = math.radians(phi)   # 0 = forearm pointing forward (towards the viewer), + = outwards
        W = (E0[0] - 46 * math.sin(r), E0[1] + 8 * math.cos(r))
        return dict(H=H, lean=0, aR=(4, 6), aL=(-4, -6), wL=W, hL=(-1, 0.7), eL=E0)
    a, b = key(-52), key(48)
    if internal:
        a, b = b, a
    side = -1 if internal else 1
    tx = -150 if internal else 150
    scene = equip = None
    if eq == "cable":
        scene = X.cable_tower(tx + 10 * side, E0[1] + 4, side=side, w=26, stack_h=70)
        equip = X.cable_line((tx + 10 * side, E0[1] + 4), anchor="wL", handle="d")
    elif eq == "band":
        scene = X.box(tx - 6, -260, tx + 6, 0, X.BENCHC, 3)
        equip = X.band_line((tx, E0[1] + 4), to="wL", post=True)
    elif eq == "dumbbell":
        equip = _vdumbbell()
    return make_spec([a, b], equip, scene, hilite=hil or "shoulders", view_kind="front", hold=(700, 600), steps=10)


def _side_rot(eq, var, hil):
    internal = has(var, "reverse")
    bench = has(var, "bench")
    top = 40 if bench else 0
    hip = (0, -14 - top)
    base = dict(hip=hip, torso=-90, head=-92, A=(128, hip[1] + 8 if not bench else -6), kh=(0, -1),
                A2=(132, -6 if not bench else -6), kh2=(0, -1), foot=-70, foot2=-70)
    if bench:
        base.update(A=(128, -top - 8), A2=(132, -top - 8), kh=(0, -1), kh2=(0, -1))
    S = X.add(hip, X.vup(-90, 92))
    E = (S[0] + 46, hip[1] - 12)
    # far arm (bottom arm) under the head
    def key(th):
        W = (E[0], E[1] - 46 * math.sin(math.radians(th)))
        return dict(base, E=E, W=W, ah=(0, -1), E2=(S[0] + 6, hip[1] + 4), W2=(S[0] - 14, hip[1] + 2))
    a, b = key(10 if not bench else -80), key(88 if not bench else 78)
    if internal and not bench:
        a, b = b, a
    equip = X.dumbbell_end("wrist") if eq == "dumbbell" else None
    scene = X.bench(S[0] - 22, hip[0] + 150, top, thick=12, legs=(0.08, 0.92)) if bench else X.mat(-160, 190)
    return make_spec([a, b], equip, scene, hilite=hil or "shoulders", lying=True, hold=(700, 600), steps=10)


@pat("rotation", ("dumbbell", ["lying"], "shoulders"), ("dumbbell", ["lying", "reverse"], "shoulders"),
     ("dumbbell", ["lying", "reverse", "bench"], "shoulders"), ("cable", ["standing"], "shoulders"),
     ("cable", ["standing", "reverse"], "shoulders"), ("band", ["standing"], "shoulders"),
     ("dumbbell", ["standing"], "shoulders"))
def rotation(eq, var, hil):
    if has(var, "lying", "bench"):
        return _side_rot(eq, var, hil)
    return _front_rot(eq, var, hil)


# ================================================================================================== SHOULDER ARC (dislocates / band drills)
def _stick_end(anchor="wrist", r=5.5, col=(206, 170, 120)):
    def fn(d, T, J, s):
        x, y = T(J[anchor])
        k = s * SS
        d.ellipse([x - r * k, y - r * k, x + r * k, y + r * k], fill=col, outline=(150, 118, 80), width=int(1.4 * k))
    return X.Item(fn, lambda J: [add(J[anchor], (-8, -8)), add(J[anchor], (8, 8))])


@pat("shoulder_arc", ("none", [], "shoulders"), ("band", [], "shoulders"), ("band", ["single_arm"], "shoulders"))
def shoulder_arc(eq, var, hil):
    hil = hil or "shoulders"
    base = dict(A=(0, -6), hip=(0, -152), torso=0, head=0, kh=(1, 0), foot=0)
    single = has(var, "single_arm")
    angs = [20, 100, 176] if single else [88, 180, 238]
    keys = []
    for a in angs:
        kw = dict(base, uarm=a, farm=a)
        if single:
            kw["FA"] = (4, 8)
        else:
            kw["FA"] = (a, a)
        keys.append(kw)
    if single:
        equip = X.band_line((-175, -120), to="wrist", post=True)
        return make_spec(keys, equip, None, hilite=hil, hold=(700, 600), steps=7)
    return make_spec(keys, _stick_end(col=(206, 170, 120) if eq != "band" else X.BANDC), None, hilite=hil,
                     hold=(700, 600), steps=7)


# ================================================================================================== BALANCE
def _bosu(ang_fn):
    def fn(d, T, J, s):
        k = s * SS
        c = chan(J, 0)
        ang = ang_fn(c)
        pts = []
        for i in range(0, 25):
            t = i / 24
            x = -46 + 92 * t
            y = -24 * math.sin(math.pi * t) ** 0.8
            pts.append(X.rot_pt((x, y), ang, (0, 0)))
        base = [X.rot_pt((46, 0), ang, (0, 0)), X.rot_pt((-46, 0), ang, (0, 0))]
        d.polygon([T(p) for p in pts + base], fill=(70, 120, 200))
        d.polygon([T((x * 0.0 + p[0], p[1])) for p in pts[2:23]] and [T(p) for p in pts[3:22]], fill=(86, 142, 226))
        q0, q1 = X.rot_pt((-50, 0), ang, (0, 0)), X.rot_pt((50, 0), ang, (0, 0))
        X.capsule(d, T(q0), T(q1), 3.5 * k, 3.5 * k, (60, 66, 84))
    return X.Item(fn, lambda J: [(-52, -28), (52, 4)])


@pat("balance", ("none", [], "glutes"), ("none", ["eyes_closed"], "glutes"), ("none", ["bosu"], "glutes"),
     ("none", ["hinge"], "hamstrings"), ("kettlebell", ["hinge", "kb"], "glutes"), ("kettlebell", ["circles"], "glutes"))
def balance(eq, var, hil):
    hil = hil or "glutes"
    closed = has(var, "eyes_closed")
    if has(var, "circles"):
        return _kb_circles(hil)
    if has(var, "hinge"):
        return _hinge(eq, var, hil)
    bosu = has(var, "bosu")
    lift = 24 if bosu else 0
    base = dict(A=(0, -6 - lift), hip=(0, -152 - lift), torso=0, head=0, kh=(1, 0), foot=0, FL=(72, 6), foot2=-20)
    keys = []
    sway = [(0, 0.0), (1, 1.0), (2, 0.0), (3, -1.0)]
    for _, c in sway:
        kw = dict(base)
        if bosu:
            ang = 6 * c
            kw["A"] = X.rot_pt((0, -30), ang, (0, 0))
            kw["hip"] = (kw["A"][0], -176)
            kw["torso"] = -3 * c
            kw["head"] = -3 * c
        else:
            kw["torso"] = 1.2 * c
            kw["head"] = 1.2 * c
        h = kw["hip"]
        kw["W"] = (h[0] + 10, h[1] - 6)
        kw["E"] = (h[0] - 20, h[1] - 52)
        kw["ah"] = (-1, 0.4)
        kw["hand"] = (c, 0)
        keys.append(kw)
    scene = _bosu(lambda c: 6 * c) if bosu else None
    front = closed_eyes() if closed else None
    return make_spec(keys, None, scene, front=front, hilite=hil, loop="cycle", steps=5, hold=(600, 600))


def _hinge(eq, var, hil):
    kb = has(var, "kb")
    hip = (0, -150)
    stand = dict(A=(0, -6), hip=hip, torso=0, head=0, kh=(1, 0), foot=0, A2=(-8, -6), kh2=(1, 0), foot2=0)
    t = 78
    S = X.add(hip, X.vup(t, 92))
    hing = dict(A=(0, -6), hip=hip, torso=t, head=64, kh=(1, 0.2), foot=0, A2=(-142, -150), kh2=(0, -1), foot2=70)
    if kb:
        hing.update(W=(S[0] + 6, S[1] + 94), ah=(-1, 0.2))
        stand.update(W=(hip[0] + 6, hip[1] + 12), ah=(0, 1))
        stand["W"] = (8, -108 + 0)
        stand["E"] = (-4, -150)
        hing["E"] = (S[0] + 2, S[1] + 48)
        stand["W"] = (6, -112)
        hing["W"] = (S[0] + 6, S[1] + 94)
        equip = X.kettlebell("wrist", "down", r=10)
        # airplane: open the hips -> chest turns up a little, leg lifts
        open_ = dict(hing, torso=48, head=40, A2=(-130, -190), foot2=70)
        S2 = X.add(hip, X.vup(48, 92))
        open_["E"] = (S2[0] + 2, S2[1] + 48)
        open_["W"] = (S2[0] + 6, S2[1] + 94)
        return make_spec([stand, hing, open_], equip, None, hilite=hil, hold=(700, 600), steps=7)
    hing.update(W=(S[0] + 92, S[1] + 4), ah=(0, 1))
    stand.update(W=(hip[0] + 8, hip[1] - 6), E=(hip[0] - 20, hip[1] - 52), ah=(-1, 0.4))
    hing["E"] = (S[0] + 46, S[1] + 4)
    return make_spec([stand, hing], None, None, hilite=hil, hold=(700, 700), steps=9)


def _kb_circles(hil):
    hip = (0, -148)
    base = dict(A=(0, -6), hip=hip, torso=0, head=0, kh=(1, 0.1), foot=0, A2=(-34, -62), kh2=(0.3, 1), foot2=60, FA=(2, 4))
    keys = []
    pts = [((36, -186), False), ((2, -192), False), ((-36, -186), True), ((2, -180), True)]
    for p, beh in pts:
        kw = dict(base)
        kw["W"] = p
        kw["ah"] = (0, 1)
        kw["behind"] = beh
        keys.append(kw)
    back, front = X.held_pair("wrist", "kettlebell")
    return make_spec(keys, front, back, hilite=hil, loop="cycle", steps=6)


# ================================================================================================== PALLOF PRESS
@pat("pallof_press", ("cable", [], "abs"), ("band", [], "obliques"))
def pallof_press(eq, var, hil):
    hil = "abs"
    H = (0, -152)
    start = dict(H=H, lean=0, eL=(-30, -196), wL=(8, -208), hL=(-1, 0.5), eR=(30, -196), wR=(12, -208), hR=(1, 0.5))
    out = dict(H=H, lean=0, eL=(-30, -214), wL=(-52, -184), hL=(-1, 0.5), eR=(24, -214), wR=(-46, -186), hR=(1, 0.5))
    y = -200
    if eq == "band":
        scene = X.box(166, -260, 178, 0, X.BENCHC, 3)
        equip = X.band_line((172, y), to="wL", post=True)
    else:
        scene = X.cable_tower(180, y, side=1, w=26, stack_h=70)
        equip = X.cable_line((180, y), anchor="wL", handle="d")
    return make_spec([start, out], equip, scene, hilite=hil, view_kind="front", hold=(700, 800), steps=10)


# ================================================================================================== PENDULUM
@pat("pendulum", ("dumbbell", [], "shoulders"))
def pendulum(eq, var, hil):
    hil = hil or "shoulders"
    base = dict(A=(0, -6), shin=12, thigh=-30, torso=65, head=50)
    S = shoulder_of(base)
    Wsup = (S[0] + 26, S[1] + 92)
    keys = []
    for dx, dy in ((40, -5), (0, 0), (-40, -5), (0, -10)):
        kw = dict(base, W=(S[0] + dx * 0.6 + 4, S[1] + 92 + dy), ah=(-1, 0.4), W2=Wsup, ah2=(0.3, 1))
        keys.append(kw)
    scene = X.many(X.box(Wsup[0] - 26, Wsup[1] + 6, Wsup[0] + 30, Wsup[1] + 18, X.BENCHC, 4),
                   X.post_rect(Wsup[0] - 20, Wsup[1] + 18, Wsup[0] - 15, 0), X.post_rect(Wsup[0] + 20, Wsup[1] + 18, Wsup[0] + 25, 0))
    return make_spec(keys, X.dumbbell("wrist"), scene, hilite=hil, loop="cycle", steps=6)


# ================================================================================================== HANG PULL (hangboard recruitment pulls)
@pat("hang_pull", ("bar", ["single_arm"], "lats"))
def hang_pull(eq, var, hil):
    hil = hil or "lats"
    bar_y = -330
    xb = 40
    keys = []
    for S_y, el in ((bar_y + 98, 0.0), (bar_y + 74, 1.0)):
        S = (xb - 6, S_y)
        hip = (S[0] - 4, S[1] + 92)
        kw = dict(A=(hip[0] - 40, hip[1] + 112), hip=hip, torso=2, head=6, kh=(1, 0), foot=40,
                  W=(xb, bar_y), ah=(0.6, 0.4) if el else (0.2, 1), W2=(S[0] + 4, S[1] + 94), ah2=(0.3, 1))
        keys.append(kw)
    def board(d, T, J, s):
        k = s * SS
        a, b = T((xb + 6, bar_y - 40)), T((xb + 40, 0))
        d.rectangle([a[0], a[1], b[0], b[1]], fill=WALLC)
        a, b = T((xb - 2, bar_y - 8)), T((xb + 10, bar_y + 4))
        d.rounded_rectangle([a[0], a[1], b[0], b[1]], radius=2 * k, fill=(206, 170, 120))
        a, b = T((xb + 2, bar_y - 3)), T((xb + 14, bar_y + 1))
        d.rectangle([a[0], a[1], b[0], b[1]], fill=(170, 134, 90))
    sc = X.Item(board, lambda J: [(xb - 4, bar_y - 40), (xb + 40, 0)])
    return make_spec(keys, None, sc, hilite=hil, hold=(700, 900), steps=8)


# ================================================================================================== HALF-KNEELING SINGLE-ARM PULLDOWN
@pat("kneeling_pulldown", ("cable", ["single_arm"], "lats"))
def kneeling_pulldown(eq, var, hil):
    hil = hil or "lats"
    hip = (0, -92)
    base = dict(A=(-70, -34), hip=hip, kh=(1, 0.3), foot=100, A2=(62, -6), kh2=(1, -0.2), foot2=0)
    a = dict(base, torso=-4, head=0)
    b = dict(base, torso=-14, head=-6)
    Sa, Sb = shoulder_of(a), shoulder_of(b)
    a["W"] = (Sa[0] + 14, Sa[1] - 92)
    a["ah"] = (1, 0)
    b["W"] = (Sb[0] + 22, Sb[1] + 8)
    b["ah"] = (-0.5, 1)
    pul = (Sa[0] + 14, -300)
    scene = X.cable_tower(130, -300, side=1, w=26, beam_to=pul[0])
    return make_spec([a, b], X.cable_line(pul, handle="d"), scene, hilite=hil, hold=(700, 700), steps=9)
