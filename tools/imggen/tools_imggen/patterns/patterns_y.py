"""Olympic lifts, loaded carries / conditioning, boxing, swimming, bear crawl and assorted drills (agent y).

Same conventions as patterns_b.py (keys specs rendered by extras_b.render_spec)."""
import math
try:
    from . import extras_b as X
    from .patterns_b import make_spec, has, shoulder_of
except ImportError:  # pragma: no cover
    import extras_b as X
    from patterns_b import make_spec, has, shoulder_of

mk = X.mk
PATTERNS = {}
TEST_VARIANTS = {}


def pat(name, *tests):
    def deco(fn):
        PATTERNS[name] = fn
        TEST_VARIANTS[name] = list(tests) or [("none", [], None)]
        return fn
    return deco


def sh_of(hip, torso):
    return X.add(hip, X.vup(torso, 92))


def L(ax, ay, bx, by, t):
    return (ax + (bx - ax) * t, ay + (by - ay) * t)


# ============================================================================================ OLYMPIC LIFTS
def kb_held(anchor="wrist", r=11.5):
    """Kettlebell in the hand: hangs below the hand when the forearm points down, rests on the forearm when it points up."""
    def geom(J):
        w, e = J[anchor], J["elbow" if anchor == "wrist" else "elbow2"]
        n = X.dist(e, w) or 1
        u = ((w[0] - e[0]) / n, (w[1] - e[1]) / n)
        s = max(-1.0, min(1.0, u[1] * 2.6))
        off = (r + 3) * s
        return w, (w[0] + u[0] * off, w[1] + u[1] * off), u

    def fn(d, T, J, s):
        w, c, u = geom(J)
        k = s * X.SS
        wx, wy = T(w)
        cx_, cy_ = T(c)
        px, py = -u[1], u[0]
        top = (wx + (c[0] - w[0]) * 0, wy)
        # handle: ring through the hand, on the side away from the bell
        pts = []
        sgn = 1 if X.dist(w, c) > 0.5 and ((c[0] - w[0]) * u[0] + (c[1] - w[1]) * u[1]) >= 0 else -1
        for i in range(13):
            a = math.pi * i / 12
            lat = -math.cos(a) * 8.0
            fwd = -math.sin(a) * 7.5 * sgn
            pts.append((wx + (px * lat + u[0] * fwd) * k, wy + (py * lat + u[1] * fwd) * k))
        X.ImageDraw.ImageDraw  # noqa
        d.line(pts, fill=X.KBC, width=int(3.4 * k), joint="curve")
        X.disc(d, (cx_, cy_), r * k, X.KBC)
        X.disc(d, (cx_ - r * 0.32 * k, cy_ - r * 0.32 * k), r * 0.22 * k, (104, 112, 136))
    return X.Item(fn, lambda J: [X.add(J[anchor], (r + 10, r + 10)), X.add(J[anchor], (-r - 10, -r - 10))])


def _lift_gear(eq, two):
    if eq == "barbell":
        return X.barbell("wrist", half=56, plate=16), None
    if eq == "kettlebell":
        a = kb_held("wrist")
        return (X.many(a, kb_held("wrist2")) if two else a), None
    a = X.dumbbell("wrist", size=0.85)
    return (X.many(a, X.dumbbell("wrist2", size=0.85)) if two else a), None


@pat("olympic_lift", ("barbell", ["snatch"], "shoulders"), ("barbell", ["clean"], "quads"), ("barbell", ["jerk"], "shoulders"),
     ("barbell", ["clean", "jerk"], "shoulders"), ("barbell", ["power", "clean"], "glutes"),
     ("barbell", ["clean", "press"], "shoulders"), ("dumbbell", ["snatch", "single_arm"], "glutes"),
     ("kettlebell", ["clean", "press", "double"], "shoulders"))
def olympic_lift(eq, var, hil):
    """Snatch / clean / jerk / clean&jerk / clean&press with barbell, dumbbell or kettlebell (single or double)."""
    eq = eq if eq in ("barbell", "dumbbell", "kettlebell") else "barbell"
    hil = hil or "glutes"
    snatch, jerk, press, clean = has(var, "snatch"), has(var, "jerk"), has(var, "press"), has(var, "clean")
    power = has(var, "power")
    two = eq == "barbell" or has(var, "double")
    bx = 26
    fl = {"barbell": -16, "dumbbell": -12, "kettlebell": -29}[eq]

    def P(hip, torso, W, head=None, A=(0, -6), foot=0, ah=(-1, 0.2), kh=(1, 0), **kw):
        d = dict(A=A, hip=hip, torso=torso, head=torso * 0.6 if head is None else head, W=W, ah=ah, kh=kh, foot=foot)
        if two:
            d.update(W2=(W[0] - 2, W[1] + 2), ah2=ah)
        else:
            d.update(FA=(-14, -8))
        d.update(kw)
        return d

    def rack(hip, torso, **kw):
        S = sh_of(hip, torso)
        return P(hip, torso, (S[0] + 26, S[1] - 14), ah=(1, 0.5), **kw)

    def over(hip, torso, dx=2, up=93, **kw):
        S = sh_of(hip, torso)
        return P(hip, torso, (S[0] + dx, S[1] - up), ah=(1, 0), **kw)

    start = P((-32, -84), 76, (bx, fl))
    first = P((-14, -102), 54, (bx - 2, -78))
    thigh = P((6, -130), 26, (bx + 4, -128))
    ext_w = (bx + 20, -204) if snatch else (bx + 14, -200)
    extend = P((14, -166), 0, ext_w, A=(8, -26), foot=-55, ah=(-0.4, -1))
    hang = P((2, -152), 6, (bx + 4, -148))
    sq = (-34, -78)
    if snatch:
        ch, ct = ((-14, -114), 8) if power else (sq, 14)
        keys = [start, first, thigh, extend, over(ch, ct, head=0), over((0, -152), 0, 4), over((0, -152), 0, 4), hang, first]
    else:
        ch, ct = ((-12, -112), 10) if power else (sq, 6)
        racked = rack((0, -152), 0)
        dip = rack((2, -126), 0)
        S = sh_of((6, -156), 0)
        drive = P((6, -156), 0, (S[0] + 10, S[1] - 70), A=(6, -22), foot=-50, ah=(1, 0.2))
        split = over((-4, -112), 2, 4, A=(52, -6), A2=(-62, -14), foot=0, foot2=-55, kh=(1, 0), kh2=(0.6, -1))
        rec = over((0, -152), 0, 4)
        pull = [start, first, thigh, extend, rack(ch, ct), racked]
        if jerk and not clean:
            keys = [racked, dip, drive, split, rec, dict(rec), racked, dict(racked)]
        elif jerk:
            keys = pull + [dip, drive, split, rec, dict(rec), racked, hang, first]
        elif press:
            S = sh_of((0, -152), 0)
            mid = P((0, -152), 0, (S[0] + 24, S[1] - 70), ah=(1, 0.3))
            keys = pull + [dict(racked), mid, over((0, -152), 0, 4), over((0, -152), 0, 4), mid, racked, hang, first]
        else:
            keys = pull + [dict(racked), hang, first]
    for k in keys:
        if k.get("A2") is None:
            for n in ("A2", "foot2", "kh2"):
                k.pop(n, None)
    equip, scene = _lift_gear(eq, two)
    return make_spec(keys, equip, scene, hilite=hil, loop="cycle", steps=3)


# ============================================================================================ small scene items
def water(surface, x0=-175, x1=190):
    """Translucent water body (front layer) with a surface line."""
    def fn(d, T, J, s):
        k = s * X.SS
        img = d._image
        ov = X.Image.new("RGBA", img.size, (0, 0, 0, 0))
        o = X.ImageDraw.Draw(ov)
        a, b = T((x0, surface)), T((x1, 0))
        o.rectangle([a[0], a[1], b[0], b[1]], fill=(70, 150, 225, 70))
        o.line([a, (b[0], a[1])], fill=(50, 130, 215, 220), width=int(2.6 * k))
        img.paste(X.Image.alpha_composite(img, ov))
    return X.Item(fn, lambda J: [(x0, surface), (x1, 0)])


def slab(anchor, w=50, t=6, off=(0, 0), col=(236, 190, 70)):
    def fn(d, T, J, s):
        k = s * X.SS
        x, y = T((J[anchor][0] + off[0], J[anchor][1] + off[1]))
        d.rounded_rectangle([x - w / 2 * k, y - t / 2 * k, x + w / 2 * k, y + t / 2 * k], radius=2.5 * k, fill=col)
    return X.Item(fn, lambda J: [(J[anchor][0] + off[0] - w, J[anchor][1] + off[1] - 8), (J[anchor][0] + off[0] + w, J[anchor][1] + off[1] + 8)])


def wall(x, top=-420, thick=14, col=(204, 210, 224), mark=None):
    def fn(d, T, J, s):
        k = s * X.SS
        a, b = T((x, top)), T((x + thick, 0))
        d.rectangle([a[0], a[1], b[0], b[1]], fill=col)
        if mark is not None:
            m = T((x, mark))
            d.rectangle([m[0] - 14 * k, m[1] - 2 * k, m[0], m[1] + 2 * k], fill=X.ACCENT)
    return X.Item(fn, lambda J: [(x - 4, top), (x + thick, 0)])


def gloves(anchors=("wrist", "wrist2"), r=9.5):
    def fn(d, T, J, s):
        k = s * X.SS
        for a in anchors:
            if a in J:
                c = T(J[a])
                X.disc(d, c, r * k, (200, 52, 52))
                X.disc(d, (c[0] - r * 0.3 * k, c[1] - r * 0.3 * k), r * 0.25 * k, (232, 120, 120))
    return X.Item(fn, lambda J: [X.add(J[a], (r, r)) for a in anchors if a in J] + [X.add(J[a], (-r, -r)) for a in anchors if a in J])


# ============================================================================================ TURKISH GET-UP
@pat("turkish_getup", ("dumbbell", [], "shoulders"), ("kettlebell", [], "shoulders"))
def turkish_getup(eq, var, hil):
    hil = hil or "shoulders"
    foot = (64, -6)

    def up(kw):
        S = shoulder_of(kw)
        kw["W"] = (S[0] + 1, S[1] - 94)
        kw["ah"] = (1, 0)
        return kw

    def pose(hip, torso, hand, A=foot, head=None, A2=None, kh=(0, -1), **kw):
        d = dict(A=A, hip=hip, torso=torso, head=torso if head is None else head, kh=kh, foot=-70 if A[1] < -8 else -10,
                 kh2=(0, -1), foot2=-10)
        if A2 is not None:
            d["A2"] = A2
        S = shoulder_of(d)
        d["W"] = (S[0] + 1, S[1] - 94)
        d["ah"] = (1, 0)
        if hand is not None:
            d["W2"], d["ah2"] = hand, (0.4, 1)
        d.update(kw)
        return d
    long_leg = (146, -10)
    lie = pose((0, -14), -90, (-52, -6), head=-92, A2=long_leg)
    roll = pose((0, -14), -50, (-42, -6), head=-40, A2=long_leg)
    post = pose((6, -14), -20, (-40, -6), head=-8, A2=long_leg)
    bridge = pose((24, -46), -48, (-46, -6), head=-30, A2=(96, -12), kh2=(0, -1))
    sweep = pose((16, -78), -8, None, head=0, A2=(-62, -9), kh2=(0.3, 1), FA=(8, 30), foot2=-60)
    lunge = pose((30, -92), 0, None, head=0, A2=(-50, -9), kh2=(0.3, 1), FA=(10, 30), foot2=-60)
    stand = pose((64, -152), 0, None, head=0, A2=(60, -6), kh2=(1, 0), FA=(6, 10), foot2=-5)
    keys = [lie, roll, post, bridge, sweep, lunge, stand]
    for kk in keys:
        kk["foot"] = -70 if kk["A"][1] > -8 else 0
    keys[-1]["foot"] = 0
    for kk in keys[:5]:
        kk["foot"] = -60
    equip = X.dumbbell("wrist", size=0.95) if eq != "kettlebell" else kb_held("wrist")
    return make_spec(keys, equip, X.mat(-150, 130, h=4), hilite=hil, lying=True, steps=3)


# ============================================================================================ DEVIL'S PRESS / THRUSTER
@pat("devils_press", ("dumbbell", [], "shoulders"))
def devils_press(eq, var, hil):
    from .patterns_b import _plank_kw
    hil = hil or "shoulders"
    db = lambda a: X.dumbbell(a, size=0.85)

    def two(kw, W):
        kw["W"] = W
        kw["W2"] = (W[0] - 2, W[1] + 2)
        kw.setdefault("ah", (0, 1))
        kw["ah2"] = kw["ah"]
        return kw
    stand = two(dict(A=(0, -6), hip=(0, -152), torso=0, head=0, kh=(1, 0), foot=0), (8, -150))
    hinge = two(dict(A=(0, -6), hip=(-36, -84), torso=76, head=56, kh=(1, 0), foot=0, ah=(-1, 0.2)), (52, -12))
    pk = _plank_kw(70, True)
    pk.pop("E", None)
    pk["kh"] = (0.3, -1)
    plank = two(pk, (70, -12))
    plank["ah"] = (-0.3, -1)
    plank["ah2"] = (-0.3, -1)
    mid = two(dict(A=(0, -6), hip=(-8, -142), torso=34, head=24, kh=(1, 0), foot=0, ah=(0, 1)), (66, -136))
    S = shoulder_of(dict(hip=(10, -164), torso=0))
    top = two(dict(A=(6, -22), hip=(10, -164), torso=0, head=0, kh=(1, 0), foot=-50, ah=(1, 0)), (S[0] + 2, S[1] - 93))
    top2 = two(dict(A=(0, -6), hip=(0, -152), torso=0, head=0, kh=(1, 0), foot=0, ah=(1, 0)), (4, -337))
    keys = [stand, hinge, plank, dict(hinge), mid, top, top2, dict(top2)]
    return make_spec(keys, X.many(db("wrist"), db("wrist2")), None, hilite=hil, loop="cycle", steps=3, hands_floor=True)


@pat("thruster", ("dumbbell", [], "shoulders"), ("kettlebell", [], "quads"))
def thruster(eq, var, hil):
    hil = hil or "shoulders"
    sq = (-32, -80)

    def pose(hip, torso, W, **kw):
        d = dict(A=(0, -6), hip=hip, torso=torso, head=torso * 0.4, kh=(1, 0), foot=0, W=W, ah=(1, 0.5),
                 W2=(W[0] - 2, W[1] + 2), ah2=(1, 0.5))
        d.update(kw)
        return d

    def rack(hip, torso):
        S = shoulder_of(dict(hip=hip, torso=torso))
        return pose(hip, torso, (S[0] + 20, S[1] - 14))
    S = shoulder_of(dict(hip=(0, -152), torso=0))
    keys = [rack((0, -152), 0), rack(sq, 12), rack((-14, -116), 8),
            pose((0, -152), 0, (S[0] + 22, S[1] - 55), ah=(1, 0.2), ah2=(1, 0.2)),
            pose((0, -152), 0, (S[0] + 3, S[1] - 93), ah=(1, 0), ah2=(1, 0), A=(2, -10)),
            pose((0, -152), 0, (S[0] + 3, S[1] - 93), ah=(1, 0), ah2=(1, 0)),
            pose((0, -152), 0, (S[0] + 22, S[1] - 55), ah=(1, 0.2), ah2=(1, 0.2))]
    if eq == "kettlebell":
        g = X.many(kb_held("wrist"), kb_held("wrist2"))
    else:
        g = X.many(X.dumbbell("wrist", size=0.8), X.dumbbell("wrist2", size=0.8))
    return make_spec(keys, g, None, hilite=hil, loop="cycle", steps=3)


# ============================================================================================ WALL BALL / BALL SLAM
@pat("wall_ball", ("swiss_ball", [], "quads"), ("none", [], "shoulders"))
def wall_ball(eq, var, hil):
    hil = hil or "quads"
    wx = 190
    tgt = 330
    r = 15

    def pose(hip, torso, W, ball, **kw):
        d = dict(A=(0, -6), hip=hip, torso=torso, head=torso * 0.3, kh=(1, 0), foot=0, W=W, ah=(1, 0.5),
                 W2=(W[0] - 2, W[1] + 2), ah2=(1, 0.5))
        d.update(kw)
        J = mk(**d)
        w = J["wrist"]
        d["hand"] = (ball[0] - w[0], ball[1] - w[1])
        return d

    def chest(hip, torso):
        S = shoulder_of(dict(hip=hip, torso=torso))
        W = (S[0] + 26, S[1] + 2)
        return pose(hip, torso, W, (W[0] + 10, W[1] - 8), ah=(0.3, 1), ah2=(0.3, 1))
    sq = chest((-30, -82), 14)
    mid = chest((-12, -118), 6)
    Sst = shoulder_of(dict(hip=(8, -158), torso=0))
    push_w = (Sst[0] + 40, Sst[1] - 80)
    push = pose((8, -158), 0, push_w, (push_w[0] + 12, push_w[1] - 6), A=(4, -16), foot=-35, ah=(1, 0), ah2=(1, 0))
    reach = pose((8, -158), 0, (Sst[0] + 50, Sst[1] - 70), (wx - r, -tgt), A=(4, -16), foot=-35, ah=(1, 0), ah2=(1, 0))
    fall = pose((0, -152), 0, (Sst[0] + 60, Sst[1] - 30), (wx - r - 30, -250), ah=(1, 0.2), ah2=(1, 0.2))
    catch = pose((-8, -140), 4, (Sst[0] + 40, Sst[1] + 6), (Sst[0] + 50, Sst[1] - 4), ah=(1, 0.5), ah2=(1, 0.5))
    keys = [sq, mid, push, reach, fall, catch, sq]
    colr = X.BALLC if eq == "swiss_ball" else X.ACCENT
    ball = X.ball_at("hand_pt", r, (214, 120, 70))
    return make_spec(keys, ball, wall(wx, top=-400, mark=-tgt), hilite=hil, loop="cycle", steps=3)


@pat("ball_slam", ("none", [], "lats"))
def ball_slam(eq, var, hil):
    hil = hil or "lats"
    r = 16

    def pose(hip, torso, W, ball, **kw):
        d = dict(A=(0, -6), hip=hip, torso=torso, head=torso * 0.5, kh=(1, 0), foot=0, W=W, ah=(1, 0.3),
                 W2=(W[0] - 2, W[1] + 2), ah2=(1, 0.3))
        d.update(kw)
        w = mk(**d)["wrist"]
        d["hand"] = (ball[0] - w[0], ball[1] - w[1])
        return d
    S0 = shoulder_of(dict(hip=(0, -148), torso=4))
    chest = pose((0, -148), 4, (S0[0] + 24, S0[1] + 18), (S0[0] + 34, S0[1] + 6), ah=(0.3, 1), ah2=(0.3, 1))
    S1 = shoulder_of(dict(hip=(8, -160), torso=-4))
    over = pose((8, -160), -4, (S1[0] + 2, S1[1] - 93), (S1[0] + 2, S1[1] - 112), A=(4, -20), foot=-45, ah=(1, 0), ah2=(1, 0))
    S2 = shoulder_of(dict(hip=(-30, -112), torso=52))
    slam = pose((-30, -112), 52, (S2[0] + 38, S2[1] + 62), (S2[0] + 44, -r + 0), ah=(-0.4, 1), ah2=(-0.4, 1))
    bounce = pose((-32, -106), 56, (S2[0] + 40, S2[1] + 52), (S2[0] + 62, -118), ah=(-0.4, 1), ah2=(-0.4, 1))
    catch = pose((-26, -108), 46, (S2[0] + 40, S2[1] + 58), (S2[0] + 48, -64), ah=(-0.4, 1), ah2=(-0.4, 1))
    keys = [chest, over, dict(over), slam, bounce, catch]
    return make_spec(keys, X.ball_at("hand_pt", r, (214, 120, 70)), None, hilite=hil, loop="cycle", steps=3)


# ============================================================================================ SLED PUSH
def sled_item(x0=150, x1=290):
    def fn(d, T, J, s):
        k = s * X.SS
        # runners and base
        a, b = T((x0, -14)), T((x1, -6))
        d.rounded_rectangle([a[0], a[1], b[0], b[1]], radius=3 * k, fill=X.METAL_D)
        for rx in (x0 + 4, x1 - 24):
            p = T((rx, -6))
            d.rounded_rectangle([p[0], p[1], p[0] + 26 * k, p[1] + 6 * k], radius=3 * k, fill=X.METAL)
        # plates on the pin
        for cx in (x1 - 60, x1 - 30):
            c = T((cx, -45))
            d.rounded_rectangle([c[0] - 6 * k, c[1] - 28 * k, c[0] + 6 * k, c[1] + 28 * k], radius=3 * k, fill=X.EQUIP)
        # uprights (high push handles)
        a = T((x0 + 12, -14))
        b = T((x0 + 12, -186))
        d.line([a, b], fill=X.METAL, width=int(6 * k))
        d.line([T((x0 + 12, -100)), T((x0 + 60, -52))], fill=X.METAL_D, width=int(4 * k))
    return X.Item(fn, lambda J: [(x0 - 10, -190), (x1 + 8, 0)])


@pat("sled_push", ("none", [], "quads"))
def sled_push(eq, var, hil):
    hil = hil or "quads"
    hx = 162
    def pose(back_phase, dy=0.0):
        hip = (0, -122 + dy)
        base = dict(hip=hip, torso=48, head=40, kh=(1, -0.1), kh2=(1, -0.1), foot=0, foot2=0)
        S = shoulder_of(base)
        base.update(W=(hx, -176), W2=(hx + 2, -174), ah=(0.2, 1), ah2=(0.2, 1))
        drive = (hip[0] - 88, -9)
        knee = (hip[0] + 52, hip[1] + 62)
        mid1 = (hip[0] - 36, -26)
        mid2 = (hip[0] + 6, -36)
        seq = {0: (drive, knee), 1: (mid1, mid2), 2: (knee, drive), 3: (mid2, mid1)}[back_phase]
        base["A"], base["A2"] = seq
        base["foot"] = -55 if seq[0] == drive else (-30 if seq[0] in (mid1, mid2) else 0)
        base["foot2"] = -55 if seq[1] == drive else (-30 if seq[1] in (mid1, mid2) else 0)
        return base
    keys = [pose(0), pose(1, -4), pose(2), pose(3, -4)]
    return make_spec(keys, None, sled_item(), hilite=hil, loop="cycle", steps=6, linear=True)


# ============================================================================================ BATTLE ROPES
def rope_item(anchor, other_phase, ax=290, ay=-58, amp=30, col=(70, 76, 94)):
    """Rope from the hand to a fixed anchor with a travelling wave (phase read from the hand motion)."""
    def pts(J):
        w = J[anchor]
        sn = (w[1] - J["rope_y0"]) / -J["rope_amp"] * other_phase
        cs = (w[0] - J["rope_x0"]) / J["rope_cx"] * other_phase
        out = []
        n = 36
        for i in range(n + 1):
            t = i / n
            x = w[0] + (ax - w[0]) * t
            y = w[1] + (ay - w[1]) * t
            env = amp * (1 - 0.5 * t)
            kk = 2 * math.pi * 1.5 * t
            y += env * (sn * math.cos(kk) - cs * math.sin(kk)) * (1 - t) ** 0.3 - env * sn * (1 - t) * 0
            out.append((x, y))
        return out

    def fn(d, T, J, s):
        k = s * X.SS
        d.line([T(p) for p in pts(J)], fill=col, width=int(5.2 * k), joint="curve")
        X.disc(d, T((ax, ay)), 6 * k, X.METAL_D)
    return X.Item(fn, lambda J: [(ax + 8, ay - 40), (ax + 8, ay + 40)])


@pat("battle_ropes", ("none", [], "shoulders"))
def battle_ropes(eq, var, hil):
    hil = hil or "shoulders"
    n = 8
    amp, cx = 24, 8
    hip = (-30, -106)
    base = dict(A=(0, -6), hip=hip, torso=38, head=22, kh=(1, 0), foot=0)
    S = shoulder_of(base)
    x0, y0 = S[0] + 56, S[1] + 50
    keys = []
    for i in range(n):
        ph = 2 * math.pi * i / n
        kw = dict(base)
        kw["W"] = (x0 + cx * math.cos(ph), y0 - amp * math.sin(ph))
        kw["W2"] = (x0 + cx * math.cos(ph + math.pi), y0 - amp * math.sin(ph + math.pi))
        kw["ah"], kw["ah2"] = (0, 1), (0, 1)
        kw["hip"] = (hip[0], hip[1] + 3 * math.cos(2 * ph))
        keys.append(kw)
    # rope items read the hand motion (rope_y0 / rope_x0 are constants injected through J by a wrapper)
    r1, r2 = rope_item("wrist", 1), rope_item("wrist2", -1, col=(120, 126, 150))

    def wrap(item):
        def fn(d, T, J, s):
            J2 = dict(J, rope_y0=y0, rope_amp=amp, rope_x0=x0, rope_cx=cx)
            item(d, T, J2, s)
        return X.Item(fn, item.ext)
    return make_spec(keys, wrap(r1), wrap(r2), hilite=hil, loop="cycle", steps=2, linear=True)


# ============================================================================================ PUNCHES
def bag_item(x=152, top=-300, w=44, h=118):
    def fn(d, T, J, s):
        k = s * X.SS
        reach = max(J["wrist"][0], J.get("wrist2", J["wrist"])[0])
        sw = max(0.0, reach - 112) * 0.3
        cx_, cy_ = x + sw, top + 160
        t0 = T((x, top))
        c = T((cx_, cy_))
        d.line([t0, (c[0], c[1] - h * 0.5 * k)], fill=X.METAL_D, width=int(3 * k))
        d.rounded_rectangle([c[0] - w / 2 * k, c[1] - h / 2 * k, c[0] + w / 2 * k, c[1] + h / 2 * k], radius=14 * k,
                            fill=(160, 70, 60))
        d.rounded_rectangle([c[0] - w / 2 * k, c[1] - 6 * k, c[0] + w / 2 * k, c[1] + 2 * k], radius=2 * k, fill=(120, 50, 46))
        d.rectangle([T((x - 30, top - 6))[0], T((x, top - 6))[1] - 4 * k, T((x + 30, top))[0], T((x, top))[1]], fill=X.METAL_D)
    return X.Item(fn, lambda J: [(x - 34, top - 10), (x + 40, top + 230)])


@pat("punches", ("none", [], "shoulders"), ("none", ["bag"], "triceps"))
def punches(eq, var, hil):
    hil = hil or "shoulders"
    bag = has(var, "bag") or eq == "bag"

    def pose(hipx, torso, W, W2, rear=0.0):
        hip = (hipx, -128)
        d = dict(A=(42, -6), A2=(-50 - rear, -10), hip=hip, torso=torso, head=torso * 0.5, kh=(1, 0), kh2=(1, 0),
                 foot=0, foot2=-35 - rear, W=W, W2=W2, ah=(0, 1), ah2=(0, 1))
        return d
    S0 = shoulder_of(dict(hip=(0, -128), torso=8))
    guard = pose(0, 8, (S0[0] + 38, S0[1] - 20), (S0[0] + 32, S0[1] - 8))
    S1 = shoulder_of(dict(hip=(6, -126), torso=14))
    jab = pose(6, 14, (S1[0] + 94, S1[1] - 4), (S1[0] + 30, S1[1] - 10))
    jab["ah"] = (0, 1)
    S2 = shoulder_of(dict(hip=(16, -124), torso=20))
    cross = pose(16, 20, (S2[0] + 34, S2[1] - 14), (S2[0] + 96, S2[1] - 2), rear=8)
    cross["ah2"] = (0, 1)
    keys = [guard, jab, dict(guard), cross]
    scene = bag_item() if bag else None
    return make_spec(keys, None, scene, front=gloves(), hilite=hil, loop="cycle", steps=6)


# ============================================================================================ SWIMMING
@pat("swim", ("none", ["freestyle"], "shoulders"), ("none", ["kick"], "quads"), ("none", ["side_kick"], "glutes"),
     ("none", ["bob"], "abs"), ("none", ["roll"], "obliques"), ("none", ["sprint"], "lats"))
def swim(eq, var, hil):
    """Prone swimmer in a pool (side view): freestyle arm cycle with flutter kick, kick with board, side kick, bobbing."""
    hil = hil or "shoulders"
    surf = -116
    if has(var, "bob"):
        return _bob(hil, surf)
    kick_only = has(var, "kick", "side_kick", "board")
    side = has(var, "side_kick")
    roll = has(var, "roll")
    hip = (0, -100)
    n = 12
    keys = []
    for i in range(n):
        ph = 2 * math.pi * i / n
        kv = math.sin(2 * ph * (1.0 if not kick_only else 1.5))
        kw = dict(hip=hip, torso=88, A=(-136, -100 + 15 * kv), A2=(-136, -100 - 15 * kv), kh=(0, -1), kh2=(0, -1),
                  foot=172 + 16 * kv, foot2=172 - 16 * kv)
        S = shoulder_of(kw)
        if kick_only:
            kw["head"] = 66 if not side else 66 - 22 * max(0.0, math.sin(ph))
            kw["W"] = (S[0] + 92, S[1] - 6)
            kw["ah"] = (0, -1)
            if side:
                kw["W2"] = (S[0] - 40, S[1] + 36)
                kw["ah2"] = (0, 1)
            else:
                kw["W2"] = (S[0] + 94, S[1] - 6)
                kw["ah2"] = (0, -1)
        else:
            breathe = max(0.0, math.sin(ph - 0.3)) ** 2
            kw["head"] = 90 - (50 if not roll else 120) * breathe
            for tag, th in (("W", ph), ("W2", ph + math.pi)):
                sn = math.sin(th)
                R = 88 - 22 * max(0.0, -sn)
                ry = R * (0.78 if sn > 0 else 1.0) * sn
                kw[tag] = (S[0] + R * math.cos(th), S[1] + ry)
                kw["ah" if tag == "W" else "ah2"] = (0.2, -1)
        keys.append(kw)
    equip, scene = None, water(surf)
    if kick_only:
        equip = slab("wrist", w=54, t=6, off=(6, -3))
        scene = water(surf)
    steps = 1 if has(var, "sprint") else 2
    return make_spec(keys, equip, None, front=scene, hilite=hil, loop="cycle", steps=steps, linear=True,
                     view=None)


def _bob(hil, surf):
    keys = []
    def pose(hipy, dy):
        kw = dict(hip=(0, hipy), torso=0, head=0, A=(0, hipy + 146 - 30 + dy), kh=(1, 0), kh2=(1, 0), foot=70,
                  A2=(-6, hipy + 146 - 22 - dy), foot2=70)
        kw.update(uarm=-35, farm=-8, FA=(-30, -4))
        return kw
    up = pose(-200, 4)
    dn = pose(-118, -4)
    keys = [up, dn, dict(dn), up]
    return make_spec(keys[:3], None, None, front=water(-262, -140, 140), hilite=hil, loop="cycle", steps=6,
                     view=(-120, -330, 120, 12))


# ============================================================================================ BEAR CRAWL
@pat("bear_crawl", ("none", ["walk"], "shoulders"), ("dumbbell", ["pull_through"], "abs"))
def bear_crawl(eq, var, hil):
    hil = hil or "shoulders"
    hip = (0, -112)

    def pose(hx, fx, hx2, fx2, lift=0.0, lift2=0.0, **kw):
        d = dict(hip=hip, torso=93, head=72, kh=(1, 0.3), kh2=(1, 0.3), foot=66, foot2=66, ah=(0.2, -1), ah2=(0.2, -1))
        S = shoulder_of(d)
        d["A"] = (fx, -25 - lift)
        d["A2"] = (fx2, -25 - lift2)
        d["W"] = (S[0] + hx, S[1] + 95 - 1.0 * 0 - lift * 1.0)
        d["W2"] = (S[0] + hx2, S[1] + 95 - lift2)
        d.update(kw)
        return d
    if has(var, "pull_through") or eq == "dumbbell":
        S = shoulder_of(dict(hip=hip, torso=93))
        fy = S[1] + 90

        def pt(far_x, far_lift, dbx):
            d = pose(2, -66, 2, -66)
            d["W2"] = (S[0] + far_x, fy - far_lift)
            d["ah2"] = (0.1, -1)
            d["hand"] = (S[0] + dbx - (S[0] + 2), 0)
            return d
        keys = [pt(2, 0, -30), pt(-30, 6, -30), pt(2, 6, 2), pt(30, 6, 30), pt(2, 16, 30)]

        def fn(d, T, J, s):
            k = s * X.SS
            c = T((J["hand_pt"][0], -11.5))
            d.rounded_rectangle([c[0] - 16 * k, c[1] - 2.6 * k, c[0] + 16 * k, c[1] + 2.6 * k], radius=2 * k, fill=X.METAL)
            for dx in (-15, 15):
                d.rounded_rectangle([c[0] + (dx - 4.5) * k, c[1] - 11.5 * k, c[0] + (dx + 4.5) * k, c[1] + 11.5 * k],
                                    radius=3 * k, fill=X.EQUIP)
        item = X.Item(fn, lambda J: [(J["hand_pt"][0] - 24, -24), (J["hand_pt"][0] + 24, 0)])
        return make_spec(keys, item, None, hilite=hil, hands_floor=True, steps=4)
    st = 22
    k0 = pose(st, -66 + st, -st, -66 - st)
    k1 = pose(0, -66, 0, -66, 12, 12)
    k2 = pose(-st, -66 - st, st, -66 + st)
    return make_spec([k0, k1, k2, k1], None, None, hilite=hil, hands_floor=True, loop="cycle", steps=5)


# ============================================================================================ WALL DRILL (A-march against a wall)
@pat("wall_drill", ("none", [], "quads"))
def wall_drill(eq, var, hil):
    hil = hil or "quads"
    hip = (0, -130)
    base = dict(hip=hip, torso=30, head=22, kh=(1, 0), kh2=(1, 0))
    S = shoulder_of(base)
    wx = S[0] + 92
    stand = (-82, -26)
    drive = (46, -62)

    def pose(near_up, hop=0.0):
        d = dict(base, W=(wx - 2, S[1] + 4), W2=(wx - 4, S[1] + 6), ah=(0.1, 1), ah2=(0.1, 1))
        if near_up is None:
            d.update(A=(-50, -28), A2=(-30, -34), foot=64, foot2=64, hip=(0, -134 - hop))
        elif near_up:
            d.update(A=drive, A2=stand, foot=-10, foot2=64)
        else:
            d.update(A=stand, A2=drive, foot=64, foot2=-10)
        return d
    keys = [pose(True), pose(None, 4), pose(False), pose(None, 4)]
    return make_spec(keys, None, wall(wx + 4, top=-300), hilite=hil, hands_floor=False, loop="cycle", steps=5)


# ============================================================================================ SHUTTLE RUN (bronco)
def cones(xs, h=22):
    def fn(d, T, J, s):
        k = s * X.SS
        for x in xs:
            b = T((x, 0))
            d.polygon([(b[0] - 12 * k, b[1]), (b[0] + 12 * k, b[1]), (b[0], b[1] - h * k)], fill=(240, 130, 50))
            d.rectangle([b[0] - 15 * k, b[1] - 3 * k, b[0] + 15 * k, b[1]], fill=(210, 100, 40))
        a, b2 = T((xs[0], -2)), T((xs[-1], -2))
        d.line([a, b2], fill=(255, 255, 255), width=int(2 * k))
    return X.Item(fn, lambda J: [(xs[0] - 16, -26), (xs[-1] + 16, 0)])


@pat("shuttle_run", ("none", [], "quads"))
def shuttle_run(eq, var, hil):
    from .patterns_b import _gait_pose
    hil = hil or "quads"
    keys = [_gait_pose(i / 8.0, -138, 0.4, 66, 100, 14, 42, 85, 14, hipx=0) for i in range(8)]
    return make_spec(keys, None, cones([-190, 190]), hilite=hil, loop="cycle", linear=True, steps=3)


# ============================================================================================ SNAP DOWN
@pat("snap_down", ("none", [], "quads"))
def snap_down(eq, var, hil):
    hil = hil or "quads"
    S0 = shoulder_of(dict(hip=(0, -158), torso=0))
    tall = dict(A=(4, -26), hip=(0, -158), torso=0, head=0, kh=(1, 0), foot=-55, W=(S0[0] + 2, S0[1] - 93), ah=(1, 0),
                W2=(S0[0] + 0, S0[1] - 93), ah2=(1, 0))
    hop = dict(A=(2, -52), hip=(0, -196), torso=0, head=0, kh=(1, 0), foot=-35, W=(S0[0] + 34, S0[1] - 30 - 38), ah=(1, 0.2),
               W2=(S0[0] + 34, S0[1] - 70), ah2=(1, 0.2))
    S2 = shoulder_of(dict(hip=(-34, -98), torso=46))
    land = dict(A=(0, -6), hip=(-34, -98), torso=46, head=24, kh=(1, 0), foot=0, W=(S2[0] + 66, S2[1] + 30), ah=(0.3, 1),
                W2=(S2[0] + 64, S2[1] + 32), ah2=(0.3, 1))
    return make_spec([tall, hop, land, dict(land)], None, None, hilite=hil, loop="cycle", steps=4)


# ============================================================================================ LATERAL BOUND (front view)
@pat("lateral_bound", ("none", [], "calves"))
def lateral_bound(eq, var, hil):
    hil = hil or "calves"

    def leg_y(a1, a2):
        return -6 - (76 * math.cos(math.radians(a1)) + 70 * math.cos(math.radians(a2)))

    def stance(side):  # side=-1 loaded on left foot (screen-left), +1 on the right foot
        a1, a2 = (-28 * side * -1, 0)
        a1, a2 = 28 * -side * -1, -34 * -side * -1
        a1, a2 = (30 if side < 0 else -30), (-36 if side < 0 else 36)
        hy = leg_y(a1, a2)
        lean = 12 * (-side)
        if side < 0:
            return dict(H=(-62, hy), lean=-10, head=-6, lL=(a1, a2), lR=(40, -70), aR=(-30, 20), aL=(60, 10))
        return dict(H=(62, hy), lean=10, head=6, lR=(a1, a2), lL=(-40, 70), aL=(30, -20), aR=(-60, -10))
    fly_r = dict(H=(0, -214), lean=8, head=6, lL=(-8, 40), lR=(24, 4), aR=(-50, -20), aL=(70, 10))
    fly_l = dict(H=(0, -214), lean=-8, head=-6, lR=(8, -40), lL=(-24, -4), aL=(50, 20), aR=(-70, -10))
    keys = [stance(-1), fly_r, stance(1), fly_l]
    return make_spec(keys, None, None, hilite=hil, view_kind="front", loop="cycle", steps=5)


# ============================================================================================ BUS DRIVER (plate steering, front view)
def plate_item(r=26):
    def fn(d, T, J, s):
        k = s * X.SS
        a, b = J["wL"], J["wR"]
        c = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
        cc = T(c)
        X.disc(d, cc, r * k, X.EQUIP)
        X.disc(d, cc, (r - 9) * k, (226, 230, 240))
        X.disc(d, cc, 5 * k, X.METAL_D)
        X.capsule(d, T(a), T(b), 2.4 * k, 2.4 * k, X.METAL)
        X.disc(d, T(b), 4 * k, X.ACCENT)
    return X.Item(fn, lambda J: [(J["wL"][0] - 30, J["wL"][1] - 30), (J["wR"][0] + 30, J["wR"][1] + 30)])


@pat("bus_driver", ("none", [], "shoulders"))
def bus_driver(eq, var, hil):
    hil = hil or "shoulders"
    C = (0, -262)
    R = 30
    keys = []
    for ang in (0, 55, 0, -55):
        t = math.radians(ang)
        wR = (C[0] + R * math.cos(t), C[1] + R * math.sin(t))
        wL = (C[0] - R * math.cos(t), C[1] - R * math.sin(t))
        keys.append(dict(H=(0, -152), lean=0, head=0, wR=wR, wL=wL, hR=(0.3, 1), hL=(-0.3, 1), lR=(0, 0), lL=(0, 0)))
    return make_spec(keys, plate_item(), None, hilite=hil, view_kind="front", loop="cycle", steps=6)


# ============================================================================================ RADIO TAISO (front view)
@pat("radio_taiso", ("none", [], "shoulders"))
def radio_taiso(eq, var, hil):
    hil = hil or "shoulders"
    down = dict(H=(0, -152), lean=0, head=0, aR=(8, 4), aL=(-8, -4), lR=(0, 0), lL=(0, 0))
    up = dict(H=(0, -156), lean=0, head=0, aR=(160, 172), aL=(-160, -172), lR=(0, 0), lL=(0, 0))
    right = dict(up, lean=18, head=18, H=(-4, -154))
    left = dict(up, lean=-18, head=-18, H=(4, -154))
    squat = dict(H=(0, -124), lean=0, head=0, aR=(50, 20), aL=(-50, -20), lR=(30, -40), lL=(-30, 40))
    keys = [down, up, right, up, left, up, down, squat]
    return make_spec(keys, None, None, hilite=hil, view_kind="front", loop="cycle", steps=3)


# ============================================================================================ LEG SWING (mobility, hands on a wall)
@pat("leg_swing", ("none", [], "hamstrings"))
def leg_swing(eq, var, hil):
    hil = hil or "hamstrings"
    base = dict(A=(0, -6), hip=(0, -152), torso=4, head=2, kh=(1, 0), foot=0, foot2=0)
    S = shoulder_of(base)
    wx = S[0] + 92
    base.update(W=(wx - 2, S[1] + 40), W2=(wx - 2, S[1] + 42), ah=(0.2, 1), ah2=(0.2, 1))
    back = dict(base, FL=(-30, -52), foot2=60, kh2=(1, 0))
    mid = dict(base, FL=(2, 6))
    front = dict(base, FL=(48, 46), foot2=-30)
    return make_spec([back, mid, front, mid], None, wall(wx + 4, top=-300), hilite=hil, loop="cycle", steps=5)


# ============================================================================================ HAMSTRING PULL (seated)
@pat("hamstring_pull", ("none", [], "hamstrings"))
def hamstring_pull(eq, var, hil):
    hil = hil or "hamstrings"
    hip = (0, -14)

    def pose(A, torso, kh):
        d = dict(hip=hip, torso=torso, head=torso * 0.6, A=A, kh=kh, foot=-70, A2=(146, -9), kh2=(0, -1), foot2=-80)
        J = mk(**d)
        k, h = J["knee"], J["hip"]
        dx, dy = h[0] - k[0], h[1] - k[1]
        n = math.hypot(dx, dy)
        ux, uy = dx / n, dy / n
        nx, ny = -uy, ux
        if ny < 0:
            nx, ny = -nx, -ny
        f = 0.28
        d["W"] = (k[0] + ux * n * f + nx * 8, k[1] + uy * n * f + ny * 8)
        d["ah"] = (-1, 0.3)
        d["W2"] = (d["W"][0] + 2, d["W"][1] + 1)
        d["ah2"] = (-1, 0.3)
        return d
    sit = pose((70, -6), -4, (0, -1))
    tuck = pose((30, -62), -12, (0.5, -1))
    ext = pose((96, -112), -14, (0, -1))
    return make_spec([sit, tuck, ext], None, X.mat(-120, 200, h=4), hilite=hil, lying=True, steps=5)


# ============================================================================================ FRONT LEVER / ICE CREAM MAKER
@pat("front_lever", ("bar", [], "lats"))
def front_lever(eq, var, hil):
    hil = hil or "lats"
    xb, by = 8, -362

    def pose(S, t, head):
        hip = (S[0] + math.sin(math.radians(t)) * -92 * -1, 0)
        vu = X.vup(t, 92)
        hip = (S[0] - vu[0], S[1] - vu[1])
        dirn = (-math.sin(math.radians(t)), math.cos(math.radians(t)))
        A = (hip[0] + dirn[0] * 140, hip[1] + dirn[1] * 140)
        return dict(A=A, hip=hip, torso=t, head=head, kh=(1, 0), foot=40 if t > -45 else 0, W=(xb, by), ah=(0.3, 1))
    top = pose((xb - 30, by + 6), -12, 6)
    mid = pose((xb - 20, by + 56), -48, -50)
    lever = pose((xb - 20, by + 94), -90, -90)
    return make_spec([top, mid, lever, lever], None, X.pullup_frame(xb, by), hilite=hil, steps=5, hold=(500, 700))


# ============================================================================================ SCORPION KICK
@pat("scorpion_kick", ("none", [], "glutes"))
def scorpion_kick(eq, var, hil):
    from .patterns_b import _plank_kw
    hil = hil or "glutes"
    base = _plank_kw(110, True)
    hip = base["hip"]
    ext = base["A"]
    base["kh"] = (0.4, -1)

    def pose(A, kh, foot, A2=None):
        kw = dict(base)
        kw["A"], kw["kh"], kw["foot"] = A, kh, foot
        kw["A2"], kw["kh2"], kw["foot2"] = ext, (0.4, -1), 64
        kw["E2"] = (kw["E"][0] - 6, kw["E"][1])
        kw["W2"] = (kw["W"][0] - 8, kw["W"][1])
        return kw
    plank = pose(ext, (0.4, -1), 64)
    tuck = pose((hip[0] + 24, hip[1] + 32), (0.4, -1), 70)
    scorp = pose((hip[0] + 40, hip[1] - 84), (-1, -0.2), -20)
    return make_spec([plank, tuck, scorp, tuck], None, X.mat(-140, 200, h=4), hilite=hil, hands_floor=True,
                     loop="cycle", steps=5)


# ============================================================================================ FROG BRIDGE (glute bridge, soles together, weight on hips)
def hip_weight(r=11.5):
    def fn(d, T, J, s):
        k = s * X.SS
        c = T((J["hip"][0] + 4, J["hip"][1] - 16))
        X.disc(d, c, r * k, X.EQUIP)
        X.disc(d, c, (r - 3.5) * k, X.RUBBER)
    return X.Item(fn, lambda J: [(J["hip"][0] - 18, J["hip"][1] - 30), (J["hip"][0] + 20, J["hip"][1] + 4)])


@pat("frog_bridge", ("dumbbell", [], "glutes"))
def frog_bridge(eq, var, hil):
    hil = hil or "glutes"

    def pose(hip, t):
        d = dict(hip=hip, torso=t, head=t - 6, A=(58, -6), A2=(64, -8), kh=(0, -1), kh2=(0.4, -1), foot=-80, foot2=-70)
        d["W"] = (hip[0] + 6, hip[1] - 14)
        d["ah"] = (0.4, -1)
        d["W2"] = (hip[0] + 8, hip[1] - 12)
        d["ah2"] = (0.4, -1)
        return d
    return make_spec([pose((0, -14), -90), pose((6, -80), -118)], hip_weight(), X.mat(-170, 130, h=4), hilite=hil,
                     lying=True, steps=7)
