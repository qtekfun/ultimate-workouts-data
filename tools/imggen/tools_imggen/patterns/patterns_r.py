"""Neck / shoulder / wrist / ankle / hip mobility, wall drills, rotations and a few odd drills (keys specs, extras_b engine).

Patterns: neck, shoulder_roll, arm_circle, wrist, ankle_circle, wall_drill_r, hip_circle, leg_swing, floor_top (top-view floor work), leg_swing_r,
twist_stand, ext_rot, roll_down, body_up, leg_raise_stand, bob_drill, quad_rot.
Adds optional kwargs to extras_b.mk / mkf (shx, hd, toek, bub / hd, turn, nod) and a 'top' view_kind to render_spec;
all of them are inert for specs that do not use them.
"""
import math
from PIL import Image, ImageDraw
try:
    from . import extras_b as X
except ImportError:  # pragma: no cover
    import extras_b as X
try:
    from . import patterns_x as PX
except Exception:  # pragma: no cover
    PX = None

PATTERNS = {}
TEST_VARIANTS = {}
SS = X.SS
add, sub, mul, lerp = X.add, X.sub, X.mul, X.lerp
vup = X.vup
LEG, TOR = 146.0, 92.0
S0 = (0.0, -244.0)  # standing shoulder
SKIN2 = (214, 162, 124)


def pat(name, *tests):
    def deco(fn):
        PATTERNS[name] = fn
        TEST_VARIANTS[name] = list(tests) or [("none", [], None)]
        return fn
    return deco


def has(var, *n):
    return any(x in var for x in n)


def spec(keys, equipment=None, scene=None, front=None, hilite=None, **kw):
    d = dict(keys=keys, rotation=0.0, equipment=equipment, scene=scene, front=front, hilite=hilite)
    d.update(kw)
    return d


# ------------------------------------------------------------------------------------------ engine extensions
_mk0 = getattr(X.mk, "_orig", X.mk)
_mkf0 = getattr(X.mkf, "_orig", X.mkf)
_rs0 = getattr(X.render_spec, "_orig", X.render_spec)


def _mk(*a, shx=0.0, hd=None, toek=1.0, bub=0.0, **kw):
    J = _mk0(*a, **kw)
    if shx:
        for k in ("aroot", "elbow", "wrist", "elbow2", "wrist2", "hand_pt"):
            if k in J:
                J[k] = (J[k][0] + shx, J[k][1])
    if hd is not None:
        J["head"] = (J["head"][0] + hd[0], J["head"][1] + hd[1])
    if toek != 1.0:
        J["toe"] = lerp_pt(J["ankle"], J["toe"], toek)
    J["bub"] = bub
    return J


def _mkf(*a, hd=None, turn=0.0, nod=0.0, hp=None, hp2=None, pp=(0.0, 0.0), **kw):
    J = _mkf0(*a, **kw)
    J['pp'] = pp
    if hp is not None:
        J["hp"], J["hp2"] = hp, hp2 or hp
    if hd is not None:
        J["head"] = add(J["S"], hd)
    J["turn"], J["nod"] = turn, nod
    return J


def lerp_pt(p, q, t):
    return (p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t)


def _render(spec_, size=360, steps=None):
    if spec_.get("view_kind") == "top":
        return render_top(spec_, size)
    return _rs0(spec_, size=size, steps=steps)


_mk._orig, _mkf._orig, _render._orig = _mk0, _mkf0, _rs0
X.mk, X.mkf, X.render_spec = _mk, _mkf, _render
mk, mkf = _mk, _mkf


# ------------------------------------------------------------------------------------------ small items
def head_item():
    """Repaints the front-view head (equipment layer, below the arms) with turn / nod: eyes, nose and hair follow."""
    def fn(d, T, J, s):
        k = s * SS
        hx, hy = T(J["head"])
        r = X.LEN["head"] * k
        ha = math.radians(J["head_a"])
        ux, uy, px, py = math.sin(ha), -math.cos(ha), math.cos(ha), math.sin(ha)
        nod, ang = J.get("nod", 0.0), J.get("turn", 0.0) * 1.15
        d.ellipse([hx - r - .5 * k, hy - r - .5 * k, hx + r + .5 * k, hy + r + .5 * k], fill=X.SKIN)
        c = math.degrees(math.atan2(uy, ux))
        hw = 84 + 28 * max(nod, 0) - 25 * max(-nod, 0) + 18 * abs(math.sin(ang))
        d.pieslice([hx - r, hy - r, hx + r, hy + r], c - hw, c + hw, fill=X.HAIR)
        dn = 0.05 + 0.42 * nod

        def at(ex, ey_down):
            return (hx + px * ex - ux * ey_down, hy + py * ex - uy * ey_down)
        for sg in (-1, 1):
            a2 = ang + sg * 0.42
            if math.cos(a2) > 0.25:
                p = at(r * 0.92 * math.sin(a2), r * dn)
                d.ellipse([p[0] - 2 * k, p[1] - 2 * k, p[0] + 2 * k, p[1] + 2 * k], fill=(30, 30, 40))
        if abs(ang) > 0.3:
            p = at(r * 0.98 * math.sin(ang), r * dn * 0.4 - r * 0.2)
            d.ellipse([p[0] - 2.6 * k, p[1] - 2.6 * k, p[0] + 2.6 * k, p[1] + 2.6 * k], fill=SKIN2)
    return X.Item(fn)


def trace(center, rx, ry=None, kind="circle"):
    """Faint dotted orbit drawn behind the figure (scene layer)."""
    ry = ry or rx

    def fn(d, T, J, s):
        k = s * SS
        c = center(J) if callable(center) else center
        for i in range(40):
            a = i / 40 * 2 * math.pi
            p = T((c[0] + rx * math.cos(a), c[1] + ry * math.sin(a)))
            d.ellipse([p[0] - 1.4 * k, p[1] - 1.4 * k, p[0] + 1.4 * k, p[1] + 1.4 * k], fill=(255, 120, 20, 120))
    def ext(J):
        c = center(J) if callable(center) else center
        return [(c[0] - rx, c[1] - ry), (c[0] + rx, c[1] + ry)]
    return X.Item(fn, ext)


def lbox(x0, y0, x1, y1, col, r=2):
    return X.box(x0, y0, x1, y1, col, r)


WALLC = (206, 212, 226)


def wallv(x, side, top=-430):
    x0, x1 = (x - 18, x) if side < 0 else (x, x + 18)
    return X.box(x0, top, x1, 0, WALLC, 2)


def inset_frame(d, T, c, w, k):
    x, y = T(c)
    d.rounded_rectangle([x - w * k, y - w * k, x + w * k, y + w * k], radius=6 * k, fill=(255, 255, 255, 215),
                        outline=(170, 178, 198), width=int(1.4 * k))
    return x, y


def twist_inset(anchor=(150, -330), mult=55.0):
    """Plan-view icon (head, shoulders, fixed hips; figure faces right, viewer at the bottom): shoulders turn with J['twist']."""
    def fn(d, T, J, s):
        k = s * SS
        x, y = inset_frame(d, T, anchor, 30, k)
        a = math.radians(J.get("twist", 0.0) * mult)
        for sg in (-1, 1):
            d.ellipse([x - 9 * k - 3 * k, y + sg * 9 * k - 4 * k, x - 9 * k + 5 * k, y + sg * 9 * k + 4 * k], fill=X.SHOE)
        X.capsule(d, (x, y - 9 * k), (x, y + 9 * k), 4.5 * k, 4.5 * k, X.SHORTS)
        cs, sn = math.cos(a), math.sin(a)
        p0, p1 = (x - sn * 14 * k, y - cs * 14 * k), (x + sn * 14 * k, y + cs * 14 * k)  # shoulder line, rotates clockwise
        X.capsule(d, p0, p1, 4.6 * k, 4.6 * k, X.SHIRT)
        hx_, hy_ = x + cs * 3 * k, y + sn * 3 * k
        X.disc(d, (hx_, hy_), 8 * k, X.SKIN)
        d.pieslice([hx_ - 8 * k, hy_ - 8 * k, hx_ + 8 * k, hy_ + 8 * k], math.degrees(a) + 90, math.degrees(a) + 270, fill=X.HAIR)
        X.disc(d, (hx_ + cs * 9 * k, hy_ + sn * 9 * k), 2.1 * k, SKIN2)
    return X.Item(fn, lambda J: [add(anchor, (-32, -32)), add(anchor, (32, 32))])


# ------------------------------------------------------------------------------------------ neck (front / profile)
def fk(hx=0.0, hy=-28.0, roll=0.0, turn=0.0, nod=0.0, **kw):
    d = dict(H=(0, -152), lean=0.0, head=roll, hd=(hx, hy), turn=turn, nod=nod, aR=(0, 0), aL=(0, 0))
    d.update(kw)
    return d


def hand_head(side, hx, hy, roll, up=14.0, dx=0.0):
    """Arm of `side` (+1 = screen right) reaching onto the head; returns kwargs."""
    c = (hx, S0[1] + hy)
    t = (c[0] + dx, c[1] - up)
    key = "wR" if side > 0 else "wL"
    return {key: t, ("hR" if side > 0 else "hL"): (side * 1.0, 0.1)}


def neck_circle(amp=1.0, cw=True, n=24, cars=False):
    keys = []
    for i in range(n):
        ph = (-1 if cw else 1) * 2 * math.pi * i / n   # 0 = chin down; screen clockwise = down -> left -> up -> right
        l, f = math.sin(ph), math.cos(ph)
        keys.append(fk(hx=15 * amp * l, hy=-27 + 3.5 * f * amp, roll=24 * amp * l, nod=0.95 * f, turn=0.0 + 0.1 * l,
                       aR=(5, 4), aL=(-5, -4)))
    return keys


@pat("neck", ("none", ["circle", "cw"], "traps"), ("none", ["half"], "traps"), ("none", ["tilt"], "traps"), ("none", ["turn"], "traps"),
     ("none", ["tuck"], "traps"), ("none", ["stretch", "left"], "traps"), ("none", ["levator", "right"], "traps"),
     ("none", ["flex"], "traps"), ("none", ["ext"], "traps"), ("none", ["resist"], "traps"))
def neck(eq, var, hil):
    hil = hil or "traps"
    view = (-84, -322, 84, -168)
    if not has(var, 'stretch', 'levator'):
        view = (-66, -310, 66, -190)
    front_eq = head_item()
    if has(var, "tuck", "flex", "ext", "resist", "extension"):
        pv = (-86, -324, 86, -166)
        base = dict(A=(0, -6), hip=(0, -152), torso=0, kh=(1, 0), foot=0, uarm=2, farm=3)

        def hp(head, hd=(0, 0)):
            return add(add(S0, vup(head, 28)), hd)

        def N(head):
            return (math.cos(math.radians(head)), math.sin(math.radians(head)))
        if has(var, "tuck"):
            a = dict(base, head=0, hd=(9, 1))
            b = dict(base, head=0, hd=(-7, 1))
            return spec([a, b], hilite=hil, view=pv, hold=(700, 800), steps=9)
        if has(var, "flex"):  # chin to chest, hands behind the head
            def key(h):
                c = hp(h)
                bk = sub(c, mul(N(h), 15))
                return dict(base, head=h, W=add(bk, (-2, -7)), ah=(0.3, 1), W2=add(bk, (2, -3)), ah2=(0.3, 1), front2=True)
            return spec([key(0), key(58)], hilite=hil, view=pv, hold=(600, 900), steps=10)
        if has(var, "resist"):  # hand behind the head resists the head pushing back
            def key(h):
                c = hp(h)
                bk = sub(c, mul(N(h), 17))
                return dict(base, head=h, W2=add(bk, (0, 4)), ah2=(-1, 0.4), front2=True)
            return spec([key(0), key(-20), key(-20)], hilite=hil, view=pv, hold=(600, 900), steps=8)
        # ext: look up, hand on the collarbone
        def key(h):
            return dict(base, head=h, W=(11, -229), ah=(-0.4, 1))
        return spec([key(0), key(-44)], hilite=hil, view=pv, hold=(600, 1000), steps=10)
    lat = 1 if has(var, "left") else -1
    if has(var, "circle", "cars", "cw", "ccw"):
        cw = not has(var, "ccw")
        keys = neck_circle(1.2 if has(var, "cars") else 1.0, cw=cw, cars=has(var, "cars"))
        return spec(keys, front_eq, hilite=hil, view_kind="front", view=view, loop="cycle", steps=1, linear=True, frame_ms=100 if not has(var, "cars") else 125)
    if has(var, "half"):
        keys = []
        for ph in (-90, -60, -30, 0, 30, 60, 90):
            l, f = math.sin(math.radians(ph)), math.cos(math.radians(ph))
            keys.append(fk(hx=15 * l, hy=-27 + 3.5 * f, roll=24 * l, nod=0.95 * f, aR=(5, 4), aL=(-5, -4)))
        return spec(keys, front_eq, hilite=hil, view_kind="front", view=view, hold=(300, 300), steps=3, frame_ms=75)
    if has(var, "tilt"):
        r = fk(aR=(5, 4), aL=(-5, -4))
        a = fk(hx=13, hy=-26, roll=26, aR=(5, 4), aL=(-5, -4))
        b = fk(hx=-13, hy=-26, roll=-26, aR=(5, 4), aL=(-5, -4))
        return spec([r, a, r, b], front_eq, hilite=hil, view_kind="front", view=view, loop="cycle", steps=5, hold=(600, 450))
    if has(var, "turn"):
        r = fk(aR=(5, 4), aL=(-5, -4))
        a = fk(turn=1.0, aR=(5, 4), aL=(-5, -4))
        b = fk(turn=-1.0, aR=(5, 4), aL=(-5, -4))
        return spec([r, a, r, b], front_eq, hilite=hil, view_kind="front", view=view, loop="cycle", steps=5)
    if has(var, "levator"):
        kw = dict(roll=lat * 24, hx=lat * 13, hy=-25, turn=lat * 0.8, nod=0.85)
        k1 = fk(**kw, aR=(5, 4), aL=(-5, -4))
        k1.update(hand_head(lat, kw["hx"], kw["hy"], kw["roll"], up=10, dx=-lat * 6))
        k1[("aL" if lat > 0 else "aR")] = (-lat * 8, -lat * 8)
        k0 = fk(aR=(5, 4), aL=(-5, -4))
        return spec([k0, k1], front_eq, hilite=hil, view_kind="front", view=view, hold=(700, 1100), steps=10)
    # lateral stretch with a hand on the head
    kw = dict(roll=lat * 28, hx=lat * 14, hy=-25.5)
    k1 = fk(**kw)
    k1.update(hand_head(lat, kw["hx"], kw["hy"], kw["roll"], up=14, dx=0))
    k1[("aL" if lat > 0 else "aR")] = (-lat * 14, -lat * 8)
    k0 = fk(aR=(5, 4), aL=(-5, -4))
    return spec([k0, k1], front_eq, hilite=hil, view_kind="front", view=view, hold=(700, 1100), steps=10)


# ------------------------------------------------------------------------------------------ shoulders / arms
@pat("shoulder_roll", ("none", ["forward"], "traps"), ("none", ["backward"], "traps"))
def shoulder_roll(eq, var, hil):
    fwd = not has(var, "backward", "back")
    n = 24
    keys = []
    for i in range(n):
        th = 2 * math.pi * i / n * (1 if fwd else -1)  # top -> front -> bottom -> back (wheel turning forward)
        keys.append(dict(A=(0, -6), hip=(0, -152), torso=0, head=0, kh=(1, 0), foot=0, uarm=2, farm=4, FA=(0, 3),
                         sh_up=11 * math.cos(th) + 2, shx=11 * math.sin(th), hd=(3 * math.sin(th), 0)))
    orbit = trace(lambda J: (0.0, S0[1] + 2), 11)
    return spec(keys, None, orbit, hilite=hil or "traps", view=(-90, -330, 90, -140), loop="cycle", steps=1, linear=True, frame_ms=100)


@pat("arm_circle", ("none", ["forward"], "shoulders"), ("none", ["backward"], "shoulders"))
def arm_circle(eq, var, hil):
    fwd = not has(var, "backward", "back")
    n = 24
    keys = []
    for i in range(n):
        th = 360.0 * i / n * (1 if fwd else -1)
        t2 = th - 14 * (1 if fwd else -1)
        keys.append(dict(A=(0, -6), hip=(0, -152), torso=0, head=0, kh=(1, 0), foot=0, uarm=th, farm=th, FA=(t2, t2)))
    return spec(keys, None, None, hilite=hil or "shoulders", view=(-125, -362, 125, -120), loop="cycle", steps=1, linear=True, frame_ms=95)


@pat("wrist", ("none", ["stretch"], "forearms"), ("none", ["circle"], "forearms"))
def wrist(eq, var, hil):
    hil = hil or "forearms"
    if has(var, "circle"):
        n = 24
        keys = []
        for i in range(n):
            ph = 2 * math.pi * i / n
            keys.append(dict(H=(0, -152), aR=(24, 166), aL=(-24, -166), hp=(15 * math.sin(ph), -20 - 7 * math.cos(ph)),
                             hp2=(15 * math.sin(ph), -20 - 7 * math.cos(ph))))
        # the hand is drawn in the front layer from the wrist to the tip (hp)
        keys = [dict(k, aR=(24, 166)) for k in keys]

        def fn(d, T, J, s):
            k = s * SS
            for w, h in (("wR", "hp"), ("wL", "hp2")):
                p = add(J[w], J[h])
                X.capsule(d, T(J[w]), T(p), 7.0 * k, 6.0 * k, X.SKIN)
                X.disc(d, T(p), 6.0 * k, X.SKIN)
        items = X.Item(fn)
        orb = trace(lambda J: (J["wR"][0], J["wR"][1] - 20), 15, 7)
        return spec_with_hand(keys, items, orb, hil)
    far = dict(A=(0, -6), hip=(0, -152), torso=0, head=0, kh=(1, 0), foot=0)

    def key(ux, ax, hand, w2=None):
        k = dict(far, uarm=ux, farm=ax, hand=hand, front2=True)
        if w2 is None:
            k.update(FA=(3, 3))
        return k
    S = S0
    wr = (S[0] + 50 * math.sin(math.radians(74)) + 46 * math.sin(math.radians(80)), S[1] + 50 * math.cos(math.radians(74)) + 46 * math.cos(math.radians(80)))
    k0 = dict(far, uarm=3, farm=3, FA=(3, 3), hand=(0, 18))
    k1 = dict(far, uarm=74, farm=80, hand=(1, -24), W2=(wr[0] + 10, wr[1] + 14), ah2=(0, 1), front2=True)
    k2 = dict(far, uarm=74, farm=80, hand=(-13, -20), W2=(wr[0] - 3, wr[1] - 18), ah2=(0, 1), front2=True)
    return spec([k0, k1, k2], X.fist("hand_pt"), None, hilite=hil, view=(-70, -330, 150, -140), hold=(500, 1300), steps=8)


def spec_with_hand(keys, items, orb, hil):
    return spec(keys, None, orb, items, hilite=hil, view_kind="front", view=(-80, -312, 80, -176), loop="cycle", steps=1, linear=True, frame_ms=100)


@pat("ankle_circle", ("none", ["cw"], None), ("none", ["ccw"], None))
def ankle_circle(eq, var, hil):
    cw = not has(var, "ccw")
    hip = (0, -14)
    n = 24
    leg_a = math.radians(32)
    A = add(hip, (135 * math.cos(leg_a), -135 * math.sin(leg_a)))
    base = dict(hip=hip, torso=-14, head=-10, A=A, kh=(0, -1), A2=(146, -9), kh2=(0, -1), foot2=-80, W=(-34, -7), ah=(-0.6, -1))
    neutral = -32 - 90
    keys = []
    for i in range(n):
        ph = 2 * math.pi * i / n * (1 if cw else -1)
        keys.append(dict(base, foot=neutral + 48 * math.cos(ph), toek=0.62 + 0.38 * abs(math.cos(ph))))
    ring = trace(lambda J: (J["ankle"][0] + 4, J["ankle"][1] - 24), 14, 6)
    return spec(keys, None, X.many(X.mat(-90, 230), ring), hilite=hil, view=(20, -150, 190, -20), loop="cycle", steps=1, linear=True, frame_ms=100, lying=True)


# ------------------------------------------------------------------------------------------ wall drills (profile)
@pat("wall_drill_r", ("none", ["angel"], "traps"), ("none", ["slide"], "traps"), ("none", ["serratus"], "serratus"))
def wall_drill_r(eq, var, hil):
    base = dict(A=(0, -6), kh=(1, 0), foot=0)
    if has(var, "angel"):
        hip = (0, -150)
        S = add(hip, vup(0, TOR))

        def key(up):
            ey = S[1] + 2 - 50 * up
            return dict(base, hip=hip, torso=0, head=0, E=(-8, ey), W=(-8, ey - 46 - 4 * up), E2=(-5, ey), W2=(-5, ey - 46 - 4 * up))
        return spec([key(0), key(1.0)], None, wallv(-15, -1), hilite=hil or "traps", hold=(700, 800), steps=10,
                    view=(-60, -345, 100, 10))
    serr = has(var, "serratus")

    def key(rise, hx):
        hip = (hx, -150)
        sx = 62 - math.sqrt(2500 - rise * rise)
        t = math.degrees(math.asin(max(-1, min(1, (sx - hx) / TOR))))
        S = add(hip, vup(t, TOR))
        E = (62, S[1] - rise)
        return dict(base, hip=hip, torso=t, head=t * 0.7, E=E, W=(62, E[1] - 46), E2=(60, E[1] + 2), W2=(60, E[1] - 44))
    ks = [key(0, 0), key(46 if serr else 30, -16 if serr else -6)]
    return spec(ks, None, wallv(70, +1), hilite=hil or "traps", hold=(700, 900), steps=10, view=(-70, -400, 120, 10))


# ------------------------------------------------------------------------------------------ hips and legs
@pat("hip_circle", ("none", [], "glutes"))
def hip_circle(eq, var, hil):
    R, n, keys = 20.0, 24, []
    for i in range(n):
        ph = 2 * math.pi * i / n
        px, py = R * math.cos(ph), R * math.sin(ph)
        th = math.asin(-px / 146)
        H = (px, -6 - 146 * math.cos(th))
        lean = -math.degrees(math.asin(px / TOR))
        keys.append(dict(H=H, lean=lean, head=0, lR=(math.degrees(th),) * 2, lL=(math.degrees(th),) * 2,
                         wR=(px + 24, H[1] - 8), hR=(1, 0.2), wL=(px - 24, H[1] - 8), hL=(-1, 0.2), pp=(px, py)))

    def fn(d, T, J, s):
        k = s * SS
        x, y = inset_frame(d, T, (110, -250), 28, k)
        for i in range(30):
            a = i / 30 * 2 * math.pi
            X.disc(d, (x + 15 * math.cos(a) * k, y + 15 * math.sin(a) * k), 1.1 * k, (255, 120, 20, 150) if False else (240, 150, 70))
        px_, py_ = J["pp"]
        X.disc(d, (x + px_ * 0.75 * k, y + py_ * 0.75 * k), 5 * k, X.SHORTS)
        X.capsule(d, (x - 10 * k, y + 20 * k), (x + 10 * k, y + 20 * k), 2 * k, 2 * k, X.SKIN)
    ins = X.Item(fn, lambda J: [(80, -280), (140, -220)])
    return spec(keys, None, None, ins, hilite=hil or "glutes", view_kind="front", view=(-110, -330, 150, -2), loop="cycle", steps=1, linear=True, frame_ms=100)


@pat("leg_swing_r", ("none", ["fb"], "hamstrings"), ("none", ["cross"], "hamstrings"))
def leg_swing_r(eq, var, hil):
    n = 24
    if has(var, "cross"):
        keys = []
        for i in range(n):
            th = 1 + 32 * math.cos(2 * math.pi * i / n)
            keys.append(dict(H=(0, -152), lean=0, head=0, aL=(-62, -80), wL=(-76, -228), hL=(-0.2, 1), lL=(0, 0), lR=(th, th * 0.9)))
        return spec(keys, None, wallv(-78, -1), hilite=hil or "hamstrings", view_kind="front", view=(-110, -330, 130, 8), loop="cycle",
                    steps=1, linear=True, frame_ms=90)
    keys = []
    hip = (0, -150)
    for i in range(n):
        th = 8 + 42 * math.cos(2 * math.pi * i / n)
        r = math.radians(th)
        A = (hip[0] + 142 * math.sin(r), hip[1] + 142 * math.cos(r))
        keys.append(dict(hip=hip, A=A, kh=(1, 0), torso=-0.12 * th, head=0, foot=th * 0.5, A2=(0, -6), kh2=(1, 0), W=(86, -226), ah=(0, 1)))
    return spec(keys, None, wallv(92, +1), hilite=hil or "hamstrings", view=(-100, -330, 130, 8), loop="cycle", steps=1, linear=True, frame_ms=90)


@pat("leg_raise_stand", ("none", [], "abs"))
def leg_raise_stand(eq, var, hil):
    hip = (0, -150)

    def key(a):
        r = math.radians(a)
        A = (hip[0] + 138 * math.sin(r), hip[1] + 138 * math.cos(r)) if a > 3 else (0, -6)
        return dict(hip=hip, A=A, kh=(1, 0.3), torso=0, head=0, foot=-a * 0.4, A2=(0, -6), kh2=(1, 0), W=(16, -158), ah=(-1, 0.3))
    return spec([key(0), key(78)], None, None, hilite=hil or "abs", hold=(600, 900), steps=10)


# ------------------------------------------------------------------------------------------ standing rotations (profile + plan inset)
@pat("twist_stand", ("none", ["front"], "obliques"), ("none", ["cactus"], "abs"), ("none", ["cross"], "obliques"), ("none", ["wall"], "obliques"))
def twist_stand(eq, var, hil):
    n = 24
    hip = (0, -150)
    base = dict(A=(0, -6), hip=hip, kh=(1, 0), foot=0, A2=(0, -6), kh2=(1, 0))
    keys, scene = [], None
    S = add(hip, vup(0, TOR))
    amp = 0.7 if has(var, "cross") else 1.0
    for i in range(n):
        tw = amp * math.sin(2 * math.pi * i / n)
        al = math.radians(tw * 55)
        k = dict(base, torso=0, head=0, twist=tw)
        if has(var, "cactus"):
            e = (S[0] + 46 * math.sin(al), S[1] + 2)
            e2 = (S[0] - 46 * math.sin(al), S[1] + 2)
            k.update(E=e, W=(e[0], e[1] - 46), E2=e2, W2=(e2[0], e2[1] - 46))
        elif has(var, "cross"):
            k.update(E=(S[0] + 22, S[1] + 30), W=(S[0] + 5, S[1] + 8), E2=(S[0] + 20, S[1] + 34), W2=(S[0] - 3, S[1] + 4), front2=True)
        elif has(var, "wall"):
            tw2 = 0.5 + 0.5 * math.sin(2 * math.pi * i / n)
            k.update(twist=tw2 * 0.9, W=(94, S[1] + 6), ah=(0, 1), W2=(10 - 52 * tw2, S[1] + 22 - 40 * tw2), ah2=(0, 1))
        else:
            r_ = 92 * math.cos(al)
            k.update(W=(S[0] + r_, S[1] + 6), ah=(0, 1), W2=(S[0] + r_ - 2, S[1] + 10), ah2=(0, 1))
        keys.append(k)
    sc = wallv(96, +1) if has(var, "wall") else None
    return spec(keys, None, sc, twist_inset((-100, -330)), hilite=hil or "obliques", loop="cycle", steps=1, linear=True, frame_ms=100,
                view=(-140, -370, 130, 10))


@pat("roll_down", ("none", [], "back"))
def roll_down(eq, var, hil):
    def key(hx, hy, t, h):
        return dict(A=(0, -6), hip=(hx, hy), torso=t, head=h, kh=(1, 0), foot=0, uarm=0 if t > 40 else 3, farm=0 if t > 40 else 3)
    ks = [key(0, -150, 0, 0), key(-6, -148, 26, 62), key(-14, -146, 68, 100), key(-20, -142, 108, 130)]
    return spec(ks, None, None, hilite=hil or "back", hold=(700, 1000), steps=6)


@pat("body_up", ("none", [], "triceps"))
def body_up(eq, var, hil):
    xb, yb = 200, -70
    A = (0, -6)

    def key(S, hint):
        hip = PX.hip_between(A, S, LEG, TOR) if PX else (S[0] * 0.6, S[1] * 0.6)
        t = X.ang_up(hip, S)
        return dict(A=A, hip=hip, torso=t, head=t, W=(xb, yb), ah=hint, foot=12, kh=(0, -1))
    bar = X.Item(lambda d, T, J, s: (X.disc(d, T((xb, yb)), 6 * s * SS, X.METAL), X.disc(d, T((xb, yb)), 2.6 * s * SS, X.METAL_D),
                                   d.rectangle([*T((xb + 12, yb - 4)), *T((xb + 20, 0))], fill=X.BENCHC),
                                   d.rectangle([*T((xb, yb - 3)), *T((xb + 14, yb + 3))], fill=X.BENCHC),
                                   d.rounded_rectangle([*T((xb - 6, -4)), *T((xb + 34, 0))], radius=2 * s * SS, fill=X.EQUIP)),
                 lambda J: [(xb - 10, yb - 12), (xb + 36, 0)])
    return spec([key((180, -160), (0, 1)), key((220, -102), (-0.2, -1))], bar, None, hilite=hil or "triceps", hold=(600, 700), steps=10)


@pat("bob_drill", ("none", [], "abs"))
def bob_drill(eq, var, hil):
    wl = -212

    def key(hy, hx=0.0, bub=0.0):
        return dict(A=(0, -6), hip=(hx, hy), torso=0, head=4, kh=(1, 0), foot=0, W=(52, wl - 4), ah=(0, 1), W2=(54, wl - 2), ah2=(0, 1), bub=bub, hd=(0, 0))
    ks = [key(-150), key(-110, -6), key(-66, -10), key(-66, -10, 0.4), key(-66, -10, 1.0), key(-100, -6), key(-140)]

    def water(d, T, J, s):
        k = s * SS
        a, b = T((-170, wl)), T((200, 0))
        od = d
        yy_ = a[1]
        while yy_ < b[1]:   # striped fill = translucent water after downsampling
            od.rectangle([a[0], yy_, b[0], yy_ + 2 * SS * 0.9], fill=(96, 168, 236))
            yy_ += 4 * SS * 0.9
        od.rectangle([a[0], a[1] - 1.5 * k, b[0], a[1] + 1.5 * k], fill=(60, 130, 215))
        bb = J.get("bub", 0.0)
        if bb > 0:
            hx, hy = J["head"]
            for j in range(4):
                yy = hy + 2 - bb * 48 * (0.4 + 0.2 * j)
                xx = hx + 15 + 4 * ((j * 7) % 3) - 3
                p = T((xx, yy))
                rr = (2.6 + 0.6 * j) * k
                od.ellipse([p[0] - rr, p[1] - rr, p[0] + rr, p[1] + rr], outline=(235, 245, 255), width=int(1.2 * k), fill=(200, 225, 250))
    wat = X.Item(water, lambda J: [(-120, wl - 30), (130, 0)])
    return spec(ks, None, None, wat, hilite=hil or "abs", loop="cycle", steps=3, view=(-100, -310, 120, 10))


@pat("quad_rot", ("none", ["near"], "back"), ("none", ["far"], "back"))
def quad_rot(eq, var, hil):
    far = has(var, "far", "left")
    leg = dict(A=(-72, -8), shin=90, thigh=0, foot=180)
    S = (90, -84)
    support = dict(W2=(92, -6.5), ah2=(0, -1)) if not far else dict(W=(92, -6.5), ah=(0, -1))
    H = add(S, vup(60, 28))
    bk = (H[0] + 0.5 * -15 + 0, H[1] - 0.87 * 15)
    bk = (bk[0] + 0, bk[1])

    def pose(tw, torso, head, e, w):
        d = dict(leg, torso=torso, head=head, twist=tw, **support)
        if far:
            d.update(E2=e, W2=w, front2=False)
        else:
            d.update(E=e, W=w)
        return d
    k0 = pose(0, 90, 60, (S[0] + 8, S[1] + 34), (bk[0] - 4, bk[1] + 4))
    k1 = pose(-0.9 if far else 0.9, 78, 38, (66, -132), (bk[0] - 4, bk[1] - 2))
    return spec([k0, k1], None, X.mat(-130, 170), hilite=hil or "back", hold=(600, 900), steps=10, lying=True)


# ------------------------------------------------------------------------------------------ plan (top) view
def dirv(a, n=1.0):
    r = math.radians(a)
    return (math.sin(r) * n, -math.cos(r) * n)


def plan_J(P):
    J = {"miss": 0.0}
    hp, pa, ta = P["hp"], P.get("pa", 0.0), P.get("ta", 0.0)
    sc = add(hp, dirv(ta, TOR * P.get("tn", 1.0)))
    J["hp"], J["sc"] = hp, sc
    J["head"] = add(sc, dirv(P.get("hc", ta), 28 * P.get("hn", 1.0)))
    J["ha"] = P.get("ha", ta)
    for s, sg in (("r", 1), ("l", -1)):
        hj, sj = add(hp, dirv(pa + 90, 11 * sg)), add(sc, dirv(ta + 90, 18 * sg))
        J["h" + s], J["s" + s] = hj, sj
        if "k" + s in P:
            J["k" + s], J["a" + s] = P["k" + s], P["a" + s]
        else:
            (a1, f1), (a2, f2) = P["t" + s], P["s" + s]
            J["k" + s] = add(hj, dirv(a1, 76 * f1))
            J["a" + s] = add(J["k" + s], dirv(a2, 70 * f2))
        dx, dy = J["a" + s][0] - J["k" + s][0], J["a" + s][1] - J["k" + s][1]
        n_ = math.hypot(dx, dy) or 1
        J["o" + s] = (J["a" + s][0] + dx / n_ * 20, J["a" + s][1] + dy / n_ * 20)
        if "w" + s in P:
            e, w, _ = X.ik2(sj, P["w" + s], 50, 46, P.get("h" + s, (0, 1)))
        else:
            (b1, g1), (b2, g2) = P["u" + s], P["v" + s]
            e = add(sj, dirv(b1, 50 * g1))
            w = add(e, dirv(b2, 46 * g2))
        J["e" + s], J["w" + s] = e, w
    for k_ in ("bar0", "bar1"):
        if k_ in P:
            J[k_] = P[k_]
    return J


def draw_top(J, hilite, equip, scene, mode, arms_top, view, size=360):
    minx, miny, maxx, maxy = view
    s = min((X.W_PX - 100) / (maxx - minx), (X.W_PX - 100) / (maxy - miny), 2.4)
    cx, cy = (minx + maxx) / 2, (miny + maxy) / 2
    k = s * SS

    def T(p):
        return ((p[0] - cx) * s + X.W_PX / 2) * SS, ((p[1] - cy) * s + X.W_PX / 2) * SS
    img = Image.new("RGBA", (X.W_PX * SS, X.W_PX * SS), X.BG + (255,))
    d = ImageDraw.Draw(img, "RGBA")
    if scene:
        scene(d, T, J, s)

    def cap(a, b, ra, rb, col):
        X.capsule(d, T(J[a]), T(J[b]), ra * k, rb * k, col)

    def arms():
        for sd in "lr":
            cap("s" + sd, "e" + sd, 8, 6.4, X.SHIRT)
            cap("e" + sd, "w" + sd, 6.2, 5, X.SKIN)
            X.disc(d, T(J["w" + sd]), 6 * k / k * k, X.SKIN)
    if not arms_top:
        arms()
    for sd in "lr":
        cap("h" + sd, "k" + sd, 11, 9, X.SHORTS)
        cap("k" + sd, "a" + sd, 8.5, 6.2, X.SKIN)
        cap("a" + sd, "o" + sd, 6.5, 5.5, X.SHOE)
    cap("hl", "hr", 12, 12, X.SHORTS)
    cap("hp", "sc", 14, 15, X.SHIRT)
    cap("sl", "sr", 9, 9, X.SHIRT)
    if hilite:
        ov = Image.new("RGBA", img.size, (0, 0, 0, 0))
        od = ImageDraw.Draw(ov, "RGBA")
        hp_, sc_ = J["hp"], J["sc"]

        def seg(a, b, f0, f1, w):
            X.capsule(od, T(lerp_pt(a, b, f0)), T(lerp_pt(a, b, f1)), w * k, w * k, X.HILITE)
        if hilite in ("glutes", "hips"):
            seg(J["hl"], J["hr"], 0, 1, 11)
        elif hilite in ("quads", "hamstrings", "adductors"):
            for sd in "lr":
                seg(J["h" + sd], J["k" + sd], 0.1, 0.95, 7)
        elif hilite in ("shoulders", "traps"):
            seg(J["sl"], J["sr"], 0, 1, 8)
        elif hilite == "back" or hilite == "lats":
            seg(hp_, sc_, 0.2, 0.9, 10)
        else:
            seg(hp_, sc_, 0.25, 0.85, 10)
        img = Image.alpha_composite(img, ov)
        d = ImageDraw.Draw(img, "RGBA")
    hx, hy = T(J["head"])
    r = X.LEN["head"] * k
    sx_, sy_ = T(J["sc"])
    X.capsule(d, (sx_, sy_), (hx, hy), 5 * k, 5 * k, X.SKIN)
    d.ellipse([hx - r, hy - r, hx + r, hy + r], fill=X.SKIN)
    ha = J["ha"]
    fx, fy = math.sin(math.radians(ha)), -math.cos(math.radians(ha))
    px, py = -fy, fx
    cdeg = math.degrees(math.atan2(fy, fx))
    if mode == "up":      # face to the viewer: forehead / hair on the far side, eyes and chin
        d.pieslice([hx - r, hy - r, hx + r, hy + r], cdeg - 75, cdeg + 75, fill=X.HAIR)
        for sg in (-1, 1):
            ex, ey = hx + px * sg * r * 0.38 - fx * r * 0.22, hy + py * sg * r * 0.38 - fy * r * 0.22
            d.ellipse([ex - 2 * k, ey - 2 * k, ex + 2 * k, ey + 2 * k], fill=(30, 30, 40))
        d.ellipse([hx - fx * r * 0.62 - 3 * k, hy - fy * r * 0.62 - 1.5 * k, hx - fx * r * 0.62 + 3 * k, hy - fy * r * 0.62 + 1.5 * k], fill=SKIN2)
    else:                 # seen from behind / above: hair, ears, nose pointing the way the face looks
        d.ellipse([hx - r, hy - r, hx + r, hy + r], fill=X.HAIR)
        for sg in (-1, 1):
            ex, ey = hx + px * sg * r * 1.0, hy + py * sg * r * 1.0
            d.ellipse([ex - 2.6 * k, ey - 3.4 * k, ex + 2.6 * k, ey + 3.4 * k], fill=X.SKIN)
        nx, ny = hx + fx * r * 1.08, hy + fy * r * 1.08
        d.ellipse([nx - 3 * k, ny - 3 * k, nx + 3 * k, ny + 3 * k], fill=SKIN2)
    if arms_top:
        arms()
    if equip:
        equip(d, T, J, s)
    return img.convert("RGB").resize((size, size), Image.LANCZOS)


def render_top(sp, size=360):
    keys = sp["keys"]
    seq = X.sequence(keys, loop=sp.get("loop", "pingpong"), steps=sp.get("steps"), linear=sp.get("linear", False),
                     hold=sp.get("hold", (600, 450)), frame_ms=sp.get("frame_ms", 70))
    Js = [plan_J(kw) for kw, ms in seq]
    equip, scene = sp.get("equipment"), sp.get("scene")
    pts = []
    for J in Js:
        pts += [v for k_, v in J.items() if isinstance(v, tuple) and len(v) == 2]
        for it in (equip, scene):
            if it is not None and hasattr(it, "extent"):
                pts += it.extent(J)
    view = sp.get("view") or (min(p[0] for p in pts) - 26, min(p[1] for p in pts) - 26, max(p[0] for p in pts) + 26, max(p[1] for p in pts) + 26)
    imgs = [draw_top(J, sp.get("hilite"), equip, scene, sp.get("head_mode", "up"), sp.get("arms_top", False), view, size) for J in Js]
    return imgs, [ms for _, ms in seq], Js


def matr(x0, y0, x1, y1, col=X.MATC):
    return X.box(x0, y0, x1, y1, col, 10)


def bar_item(w=3.4):
    def fn(d, T, J, s):
        k = s * SS
        X.capsule(d, T(J["bar0"]), T(J["bar1"]), w * k, w * k, X.METAL)
        for key in ("bar0", "bar1"):
            X.disc(d, T(J[key]), 6 * k, X.EQUIP)
    return X.Item(fn, lambda J: [J["bar0"], J["bar1"]])


def leg_pair(r, l):
    return {"tr": r[0], "sr": r[1], "tl": l[0], "sl": l[1]}


def arms_floor(spread=90, hand_len=1.0):
    return {"ur": (spread, 1.0), "vr": (spread, hand_len), "ul": (-spread, 1.0), "vl": (-spread, hand_len)}


@pat("floor_top", ("none", ["ninety"], "glutes"), ("none", ["iron"], "glutes"), ("none", ["crossover"], "glutes"), ("none", ["adductor"], "glutes"))
def floor_top(eq, var, hil):
    if has(var, "ninety"):   # seated, seen from above: both knees bent 90 degrees, legs windshield from one side to the other
        base = dict(hp=(0, 0), ta=0, tn=0.14, hn=0.55, wr=(36, 26), wl=(-36, 26), hr=(1, 0.3), hl=(-1, 0.3))

        def st(rt, rs, lt, ls, f1=1.0, f2=1.0):
            return dict(base, tr=(rt, f1), sr=(rs, f2), tl=(lt, f1), sl=(ls, f2))
        A, B = st(90, 180, 0, 90), st(0, 270, -90, 180)

        def mid(a, b):
            return dict(a, **{k: ((a[k][0] + b[k][0]) / 2, 0.7) for k in ("tr", "sr", "tl", "sl")})
        return spec([A, mid(A, B), B, mid(B, A)], None, matr(-150, -150, 150, 80), hilite=hil or "glutes", view_kind="top",
                    loop="cycle", steps=5, head_mode="top", view=(-125, -150, 125, 80))
    if has(var, "adductor"):   # quadruped from above: one leg out to the side, hips rock back towards the heels
        keys = []
        for back in (0, 0, 46):
            hy = 90 + back
            keys.append(dict(hp=(0, hy), ta=0, tn=hy / 92.0, hn=0.8, kr=(11, 78), ar=(11, 148), kl=(-72, 84), al=(-136, 74),
                             ur=(8, 0.4), vr=(0, 0.45), ul=(-8, 0.4), vl=(0, 0.45)))
        return spec(keys, None, matr(-170, -100, 80, 200), hilite=hil or "glutes", view_kind="top", head_mode="top",
                    hold=(600, 900), steps=10, view=(-165, -100, 75, 205))
    arms = dict(ur=(90, 1.0), vr=(90, 1.0), ul=(-90, 1.0), vl=(-90, 1.0))
    base = dict(hp=(0, 56), ta=0, tn=1.0, **arms)
    bent = ((0, 0.3), (180, 0.52))
    straight = ((178, 1.0), (178, 1.0))
    if has(var, "iron"):   # both knees drop to one side, shoulders stay flat
        def drop(sg):
            t, s_ = (sg * 72, 0.88), (180 - sg * 52, 0.8)
            return dict(base, **leg_pair((t, s_), (t, s_)))
        c = dict(base, **leg_pair(bent, bent))
        keys = [c, drop(1), c, drop(-1)]
    else:   # one bent leg crosses over the body, the other leg stays long
        def cross(side):
            if side > 0:
                return dict(base, **leg_pair(((-70, 0.8), (212, 0.9)), straight))
            return dict(base, **leg_pair(straight, ((70, 0.8), (148, 0.9))))
        c, c2 = dict(base, **leg_pair(bent, straight)), dict(base, **leg_pair(straight, bent))
        keys = [c, cross(1), c, c2, cross(-1), c2]
    return spec(keys, None, matr(-150, -110, 150, 220), hilite=hil or "glutes", view_kind="top", head_mode="up", loop="cycle", steps=5,
                hold=(600, 600), view=(-150, -125, 150, 215))


@pat("ext_rot", ("Barbell", [], "shoulders"))
def ext_rot(eq, var, hil):
    er = (26, 12)
    ks = []
    for beta in (0, 64):
        b = math.radians(beta)
        w = (er[0] + 46 * math.sin(b), er[1] - 46 * math.cos(b))
        u = (math.cos(b), math.sin(b))
        ks.append(dict(hp=(0, 0), ta=0, tn=0.12, hn=0.5, tr=(0, 0.1), sr=(0, 0.2), tl=(0, 0.1), sl=(0, 0.2),
                       kr=(11, -4), ar=(11, -14), kl=(-11, -4), al=(-11, -14),
                       ur=(165, 0.5), vr=(beta, 1.0), wl=(w[0] - u[0] * 62, w[1] - u[1] * 62), hl=(-1, 0.5),
                       bar0=(w[0] - u[0] * 78, w[1] - u[1] * 78), bar1=(w[0] + u[0] * 34, w[1] + u[1] * 34)))
    return spec(ks, bar_item(), matr(-110, -90, 120, 80), hilite=hil or "shoulders", view_kind="top", head_mode="top", hold=(600, 1000),
                steps=10, view=(-90, -100, 100, 40), arms_top=True)
