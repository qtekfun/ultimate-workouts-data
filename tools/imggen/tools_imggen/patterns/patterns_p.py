"""Round-2 animations (agent p): quadruped, prone raises, pullovers, plank variants, rollouts, wipers, V-up, body rows, bar skills.

Same conventions as patterns_b.py (key poses -> extras_b.render_spec).  All patterns here are named p_*.
Extra mk() kwargs handled by the wrapper below (ignored by the plain mk): lf / lf2 (foreshorten near / far leg about the
hip), lsh / lsh2 ((dx, dy) shift of that leg: limb swinging towards / away from the viewer).
"""
import math
from PIL import ImageDraw
try:
    from . import extras_b as X
    from .patterns_b import make_spec, has
except ImportError:  # pragma: no cover
    import extras_b as X
    from patterns_b import make_spec, has

PATTERNS = {}
TEST_VARIANTS = {}
SS = X.SS
FLOOR_ANK = -22.0
MATG = (98, 168, 150)
WALLC = (205, 211, 224)
BAR = (206, 170, 120)
STRAP = (232, 190, 70)


def pat(name, *tests):
    def deco(fn):
        PATTERNS[name] = fn
        TEST_VARIANTS[name] = list(tests) or [("none", [], None)]
        return fn
    return deco


# ------------------------------------------------------------------------------------------------ mk wrapper
_mk0 = X.mk if not getattr(X.mk, "_p_wrapped", False) else X.mk._orig


def _leg_from_v(J, hip, v, tag, foot, sh_extra=(0.0, 0.0)):
    n = math.sqrt(v[0] ** 2 + v[1] ** 2 + v[2] ** 2) or 1
    vx, vy, vz = v[0] / n, v[1] / n, v[2] / n
    pl = math.hypot(vx, vy) or 1e-6
    ux, uy = vx / pl, vy / pl
    sh = (vz * 146 * 0.30 + sh_extra[0], vz * 146 * 0.13 + sh_extra[1])
    J["knee" + tag] = (hip[0] + ux * 76 * pl + sh[0] * 0.52, hip[1] + uy * 76 * pl + sh[1] * 0.52)
    J["ankle" + tag] = (hip[0] + ux * 146 * pl + sh[0], hip[1] + uy * 146 * pl + sh[1])
    fr = math.radians(foot)
    f = 24 if tag == "" else 20.4
    a = J["ankle" + tag]
    J["toe" + tag] = (a[0] + math.cos(fr) * f, a[1] + math.sin(fr) * f)


def _mk_p(**kw):
    J = _mk0(**kw)
    if kw.get("v3") is not None:
        _leg_from_v(J, J["hip"], kw["v3"], "", kw.get("foot", 0.0))
        J["miss"] = 0.0
    if kw.get("v3b") is not None:
        _leg_from_v(J, J["hip"], kw["v3b"], "2", kw.get("foot2", 0.0), (-5.0, -2.0))
    for tag, f_, s_ in (("", "lf", "lsh"), ("2", "lf2", "lsh2")):
        f, sh = kw.get(f_), kw.get(s_)
        kn, an, to = "knee" + tag, "ankle" + tag, "toe" + tag
        if (f is None and sh is None) or an not in J:
            continue
        f = 1.0 if f is None else f
        sh = sh or (0.0, 0.0)
        h = J["hip"]
        for key, k in ((kn, 0.52), (an, 1.0), (to, 1.0)):
            if key in J:
                p = J[key]
                J[key] = (h[0] + (p[0] - h[0]) * f + sh[0] * k, h[1] + (p[1] - h[1]) * f + sh[1] * k)
    k, h, a = J["knee"], J["hip"], J["ankle"]
    u1 = (h[0] - k[0], h[1] - k[1])
    u2 = (a[0] - k[0], a[1] - k[1])
    n1, n2 = math.hypot(*u1) or 1, math.hypot(*u2) or 1
    v = (u1[0] / n1 + u2[0] / n2, u1[1] / n1 + u2[1] / n2)
    nv = math.hypot(*v) or 1
    J["crease"] = (k[0] + v[0] / nv * 10, k[1] + v[1] / nv * 10)
    return J


if not getattr(X.mk, "_p_wrapped", False):
    _mk_p._p_wrapped = True
    _mk_p._orig = _mk0
    X.mk = _mk_p


# ------------------------------------------------------------------------------------------------ timeline helper
def ease(t):
    return t * t * (3 - 2 * t)


def timeline(keys, loop="pingpong", steps=8, hold=5):
    """Pre-interpolated key list (one frame each) with explicit holds, for loop='cycle', steps=1.
    hold: int, or a list with one hold length per key (pingpong: the end keys use theirs, middle keys 1)."""
    keys = X.normalize_keys(keys)
    n = len(keys)
    hl = hold if isinstance(hold, (list, tuple)) else [hold] * n
    out = []
    path = list(range(n)) + (list(range(n - 2, 0, -1)) if loop == "pingpong" else [])
    m = len(path)
    for qi, i in enumerate(path):
        j = path[(qi + 1) % m]
        out += [dict(keys[i]) for _ in range(hl[i] if (loop == "cycle" or i in (0, n - 1)) else 1)]
        for s in range(1, steps):
            out.append(X.lerp_kw(keys[i], keys[j], ease(s / steps)))
    return out


def spec_tl(keys, equip=None, scene=None, front=None, hilite=None, loop="pingpong", steps=8, hold=5, frame_ms=95,
            **kw):
    seq = timeline(keys, loop, steps, hold)
    return make_spec(seq, equip, scene, front=front, hilite=hilite, loop="cycle", steps=1, frame_ms=frame_ms, **kw)


def vup(a, n=1.0):
    return X.vup(a, n)


# ------------------------------------------------------------------------------------------------ small items
def wheel(anchor="wrist", r=11.0, col=(60, 66, 84), hub=(150, 158, 178)):
    def fn(d, T, J, s):
        k = s * SS
        x, y = T(J[anchor])
        X.disc(d, (x, y), r * k, col)
        X.disc(d, (x, y), r * 0.55 * k, (96, 104, 128))
        X.disc(d, (x, y), 3.2 * k, hub)
    return X.Item(fn, lambda J: [X.add(J[anchor], (-r - 3, -r - 3)), X.add(J[anchor], (r + 3, r + 3))])


def mat3d(x0, x1, depth=20, h=4):
    """Mat with some depth (floor plane seen obliquely): far edge raised so that the far foot is grounded too."""
    def fn(d, T, J, s):
        k = s * SS
        pts = [T((x0, 1)), T((x1, 1)), T((x1 - 12, -depth)), T((x0 - 12, -depth))]
        d.polygon(pts, fill=(130, 190, 172))
        a, b = T((x0, 0)), T((x1, 5))
        d.rounded_rectangle([a[0], a[1], b[0], b[1]], radius=2 * k, fill=MATG)
    return X.Item(fn, lambda J: [(x0, -depth), (x1, 5)])


def far_item(anchor, kind="db", r=11.0, col=(50, 56, 74)):
    """Back-layer dumbbell disc (far hand) so that the body covers it."""
    def fn(d, T, J, s):
        k = s * SS
        x, y = T(J[anchor])
        X.disc(d, (x, y), r * k, col)
        X.disc(d, (x, y), (r - 4) * k, (62, 68, 88))
    return X.Item(fn, lambda J: [X.add(J[anchor], (-r, -r)), X.add(J[anchor], (r, r))])


def pose_plank(sx, sy, ank_y=FLOOR_ANK, hand=None, ah=(-1, 0.2), far=0.0, th_extra=0.0, head_add=6, ank_x_extra=0.0):
    """Plank-type pose from the shoulder (sx, sy): straight body down to the toes, hands at `hand` (default under S)."""
    sin_t = max(-0.95, min(0.95, (ank_y - sy) / 237.0))
    th = math.degrees(math.asin(sin_t))
    u = (math.cos(math.radians(th)), -math.sin(math.radians(th)))
    S = (sx, sy)
    hip = (S[0] - u[0] * 92, S[1] - u[1] * 92)
    A = (hip[0] - u[0] * 145 + ank_x_extra, hip[1] - u[1] * 145)
    hand = hand or (sx, -6.5)
    kw = dict(A=A, hip=hip, torso=90 - th, head=90 - th + head_add, foot=64, kh=(0, -1), W=hand, ah=ah,
              A2=(A[0] - 4, A[1] - 1.5), kh2=(0, -1), foot2=64, W2=(hand[0] + 5, hand[1]), ah2=ah)
    return kw


# ================================================================================================== QUADRUPED
def _quad_base():
    hip = (0.0, -84.0)
    kw = dict(hip=hip, torso=79, head=94, kh=(1, 1), foot=170, kh2=(1, 1), foot2=170, A=(-70, -8), A2=(-70, -8.5))
    S = X.add(hip, vup(79, 92))
    kw["W"] = (S[0], -6.5)
    kw["W2"] = (S[0] + 4, -6.5)
    kw["ah"] = kw["ah2"] = (-1, 0.4)
    return kw, S


def _crease_db(r=10.5):
    def fn(d, T, J, s):
        k = s * SS
        c = T(J["crease"])
        X.disc(d, c, r * k, X.METAL)
        X.disc(d, c, r * 0.62 * k, (84, 92, 114))
        X.disc(d, c, 2.6 * k, X.METAL)
    return X.Item(fn, lambda J: [X.add(J["crease"], (-r, -r)), X.add(J["crease"], (r, r))])


@pat("p_quad", ("none", ["bird_dog"], "abs"), ("none", ["donkey"], "glutes"), ("dumbbell", ["donkey"], "glutes"),
     ("none", ["kickback"], "glutes"))
def p_quad(eq, var, hil):
    hil = hil or "glutes"
    base, S = _quad_base()
    hipp = base["hip"]
    scene = X.mat(-160, 190, h=4)
    equip = None
    if has(var, "donkey", "kickback"):
        # near leg works, arms and far knee stay put
        if has(var, "donkey"):
            end = dict(base, A=(-78, -160), kh=(-1, 0.5), foot=-100)
            mid = dict(base, A=(-60, -70), kh=(0.2, 1), foot=140)
        else:
            end = dict(base, A=(hipp[0] - 140, hipp[1] - 30), kh=(0, 1), foot=150)
            mid = dict(base, A=(-90, -40), kh=(0.6, 1), foot=160)
        end["torso"], end["head"] = 82, 98
        if eq == "dumbbell":
            equip = _crease_db()
        keys = [base, mid, end]
        return spec_tl(keys, equip, scene, hilite=hil, hold=6, steps=6, hands_floor=True)
    # opposite arm + leg (bird dog / quadruped raise / kneeling superman)
    far_leg_out = dict(A2=(hipp[0] - 143, hipp[1] - 12), kh2=(0, 1), foot2=150)
    near_leg_out = dict(A=(hipp[0] - 143, hipp[1] - 12), kh=(0, 1), foot=150)
    near_arm = dict(W=(S[0] + 93, S[1] - 8), ah=(0, 1))
    far_arm = dict(W2=(S[0] + 97, S[1] - 8), ah2=(0, 1))
    a = dict(base, **far_leg_out)
    a.update(near_arm)
    a["head"] = 80
    b = dict(base, **near_leg_out)
    b.update(far_arm)
    b["head"] = 80
    c = dict(base)
    keys = [c, a, c, b]
    return spec_tl(keys, None, scene, hilite=hil, loop="cycle", hold=4, steps=5, hands_floor=True)


# ================================================================================================== PRONE RAISES
def _prone(lift, dump=0.0):
    hip = (0.0, -13.0 - lift * 0.15)
    t = 90 - lift
    kw = dict(A=(-143.0, -9.0), hip=hip, torso=t, head=t - 6, foot=-100, kh=(0, -1), kh2=(0, -1),
              A2=(-141.0, -11.0), foot2=-100)
    S = X.add(hip, vup(t, 92))
    return kw, S


def _arms(tok, S, lift=0.0, inc=False):
    """Both arms for the prone positions (side view; limbs going sideways are foreshortened and drawn towards the viewer
    for the near arm, away (up-left) for the far arm).  inc=True: hanging from a chest-supported torso."""
    x, y = S

    def mk_(e, w, e2, w2, ah=(0, 1)):
        return dict(E=(x + e[0], y + e[1]), W=(x + w[0], y + w[1]), E2=(x + e2[0], y + e2[1]), W2=(x + w2[0], y + w2[1]),
                    ah=ah, ah2=ah)
    if inc:
        if tok == "R":
            return mk_((2, 48), (3, 94), (6, 48), (9, 93), (-1, 0))
        if tok == "Y":
            return mk_((38, -6), (80, -34), (42, -16), (88, -48))
        if tok == "T":
            return mk_((12, 8), (24, 16), (-10, -6), (-20, -12))
        if tok == "W":
            return mk_((-24, 16), (16, -12), (-22, 8), (20, -24), (-0.3, 1))
        if tok == "L":
            return mk_((12, 12), (56, 14), (-8, -4), (40, -8))
    if tok == "I":
        return mk_((46, -2 - lift * 0.1), (93, -6 - lift * 0.3), (46, -6), (95, -10))
    if tok == "Y":
        return mk_((32, 3), (62, -4), (40, -12), (78, -30))
    if tok == "T":
        return mk_((12, 6), (26, 12), (-10, -8), (-22, -16))
    if tok == "W":
        return mk_((-26, 8), (14, -2), (-24, -2), (18, -14), (-0.3, 1))
    if tok == "L":
        return mk_((12, 6), (58, 0), (-8, -8), (40, -20))
    if tok == "S":
        return mk_((-46, 6), (-92, 8), (-46, -2), (-92, 0))
    return {}


PV = (-92, -112, 178, 20)


@pat("p_prone", ("none", ["Y", "T", "W"], "shoulders"), ("dumbbell", ["incline", "Y", "T", "W", "L"], "shoulders"),
     ("none", ["snow"], "traps"), ("none", ["retract"], "traps"))
def p_prone(eq, var, hil):
    hil = hil or "shoulders"
    toks = [t for t in ("I", "Y", "T", "W", "L") if t in var]
    order = [v for v in var if v in ("I", "Y", "T", "W", "L")]
    toks = order or ["Y"]
    if has(var, "incline", "bench"):
        return _prone_incline(eq, var, hil, toks)
    # floor
    if has(var, "snow"):
        r0, S = _prone(0)
        r1, S1 = _prone(12)
        a = dict(r1, **_arms("S", S1, 12))
        b = dict(r1, **_arms("T", S1, 12))
        c = dict(r1, **_arms("I", S1, 12))
        keys = [a, b, c]
        return spec_tl(keys, None, X.mat(-190, 160), hilite=hil, hold=6, steps=8, lying=True, view=PV)
    if has(var, "retract"):
        r0, S0 = _prone(0)
        r1, S1 = _prone(9)
        a = dict(r0, **_arms("S", S0, 0))
        b = dict(r1, **_arms("S", S1, 9))
        b.update(E=(S1[0] - 50, S1[1] - 6), W=(S1[0] - 92, S1[1] - 14), E2=(S1[0] - 50, S1[1] - 12), W2=(S1[0] - 92, S1[1] - 20))
        return spec_tl([a, b], None, X.mat(-190, 160), hilite=hil, hold=7, steps=8, lying=True, view=PV)
    r0, S0 = _prone(0)
    r1, S1 = _prone(13)
    rest = dict(r0, **_arms("I", S0, 0))
    keys = [rest] + [dict(r1, **_arms(t, S1, 13)) for t in toks]
    eq_item = None
    if eq == "dumbbell":
        eq_item = X.dumbbell_end("wrist", r=8)
    return spec_tl(keys, eq_item, X.mat(-190, 160), hilite=hil, loop="cycle" if len(toks) > 1 else "pingpong",
                   hold=4 if len(toks) > 1 else 6, steps=5 if len(toks) > 1 else 8, lying=True, view=PV)


def _prone_incline(eq, var, hil, toks):
    ang = 45
    hip = (0.0, -126.0)
    base = dict(A=(-26, -6), hip=hip, torso=ang, head=ang + 12, kh=(1, 0), foot=0, A2=(-18, -6), kh2=(1, 0), foot2=0)
    S = X.add(hip, vup(ang, 92))
    u = vup(ang)
    n = (math.cos(math.radians(ang)), math.sin(math.radians(ang)))
    p0 = (hip[0] + n[0] * 22 + u[0] * 6, hip[1] + n[1] * 22 + u[1] * 6)
    p1 = (S[0] + n[0] * 22 + u[0] * 14, S[1] + n[1] * 22 + u[1] * 14)
    scene = X.many(X.pad(p0, p1, r=8, col=X.BENCHC),
                   X.post_rect(p0[0] + 6, p0[1], p0[0] + 12, 0), X.post_rect(p1[0] - 4, p1[1], p1[0] + 2, 0),
                   X.post_rect(p0[0] - 6, -6, p1[0] + 16, 0))
    rest = dict(base, **_arms("R", S, 0, True))
    keys = [rest]
    for t in toks:
        k = dict(base, **_arms(t, S, 0, True))
        k["head"] = ang + 2
        keys.append(k)
    equip = X.dumbbell_end("wrist", r=8.5) if eq == "dumbbell" else None
    if eq == "dumbbell":
        scene = X.many(scene, far_item("wrist2", r=8.5))
    return spec_tl(keys, equip, scene, hilite=hil, loop="cycle" if len(toks) > 1 else "pingpong", hold=4 if len(toks) > 1 else 6,
                   steps=5 if len(toks) > 1 else 8)


# ================================================================================================== PLANK ROW (renegade)
@pat("p_plankrow", ("dumbbell", [], "lats"), ("kettlebell", ["single_arm"], "lats"))
def p_plankrow(eq, var, hil):
    hil = hil or "lats"
    kb = eq == "kettlebell"
    hy = -26.0 if kb else -12.0
    sy = -104.0
    b = pose_plank(110, sy, hand=(110, hy))
    b["A2"] = (b["A"][0] - 14, b["A"][1] - 2)
    S = X.add(b["hip"], vup(b["torso"], 92))
    b["W2"] = (S[0] + 8, -12.0)
    b["ah2"] = (-1, 0)
    down = dict(b)

    def row(near):
        k = dict(b)
        e = (S[0] - 36, S[1] - 14)
        w = (S[0] - 14, S[1] + 28)
        if near:
            k["E"], k["W"] = e, w
            k["hide2"] = False
        else:
            k["E2"], k["W2"] = (e[0] + 6, e[1] - 2), (w[0] + 8, w[1] - 2)
        return k
    if kb:
        keys = [down, row(True), down]
        items = X.kettlebell("wrist", "down", r=11)
        sc = X.mat(-170, 220, h=4)
        return spec_tl(keys, items, sc, hilite=hil, hold=5, steps=7, hands_floor=True, loop="pingpong")
    keys = [down, row(True), down, row(False)]
    eqp = X.dumbbell_end("wrist", r=11.5)
    sc = X.many(X.mat(-170, 220, h=4), far_item("wrist2"))
    return spec_tl(keys, eqp, sc, hilite=hil, loop="cycle", hold=4, steps=7, hands_floor=True)


# ================================================================================================== PLANK JACK
@pat("p_jack", ("none", [], "abs"))
def p_jack(eq, var, hil):
    hil = hil or "abs"
    b = pose_plank(110, -102.0)
    b["W2"] = (b["W"][0] + 6, b["W"][1] - 2)
    A0 = b["A"]
    closed = dict(b, A=(A0[0], A0[1] + 2), A2=(A0[0] - 3, A0[1] - 12), lf=1.0, lf2=1.0, lsh=(0, 0), lsh2=(0, 0))
    opened = dict(closed, lf=0.8, lf2=0.8, lsh=(24, 15), lsh2=(-22, -2))
    hop = dict(closed, lf=0.92, lf2=0.92, lsh=(5, -4), lsh2=(-5, -8))
    keys = [closed, hop, opened, hop]
    for k in keys:
        k["foot"] = 64
    sc = mat3d(-150, 220)
    return spec_tl(keys, None, sc, hilite=hil, loop="cycle", hold=3, steps=3, frame_ms=110, hands_floor=True)


# ================================================================================================== PUSH-UP VARIANTS
def _from_shoulder(S, t, A, W, head, ah=(-1, 0), **kw):
    hip = (S[0] - math.sin(math.radians(t)) * 92, S[1] + math.cos(math.radians(t)) * 92)
    d = dict(A=A, hip=hip, torso=t, head=head, W=W, ah=ah, kh=(1, 0.2), foot=70, A2=(A[0] - 6, A[1] - 2), kh2=(1, 0.2),
             foot2=70, W2=(W[0] + 6, W[1]), ah2=ah)
    d.update(kw)
    return d


@pat("p_pushvar", ("none", ["pike"], "shoulders"), ("none", ["hindu"], "shoulders"), ("none", ["scapular"], "serratus"),
     ("none", ["rotation"], "chest"))
def p_pushvar(eq, var, hil):
    sc = X.mat(-230, 150, h=4)
    if has(var, "hindu"):
        hil = hil or "shoulders"
        A = (-165, -8)
        W = (0, -6.5)
        pike = _from_shoulder((-32, -96), 120, A, W, 138)
        dive = _from_shoulder((17, -43), 128, A, W, 150)
        up = _from_shoulder((45, -88), 60, A, W, 18, ah=(-1, 0.2))
        up["foot"], up["foot2"] = 90, 90
        pike["kh"] = dive["kh"] = (1, -0.2)
        up["kh"] = up["kh2"] = (0, -1)
        return spec_tl([pike, dive, up], None, sc, hilite=hil, hold=4, steps=7, hands_floor=True)
    if has(var, "pike", "v"):
        hil = hil or "shoulders"
        A = (-165, -8)
        W = (0, -6.5)
        top = _from_shoulder((-32, -96), 120, A, W, 138)
        bot = _from_shoulder((6, -52), 130, A, W, 152)
        top["kh"] = bot["kh"] = (1, -0.2)
        return spec_tl([top, bot], None, sc, hilite=hil, hold=5, steps=8, hands_floor=True)
    if has(var, "scapular"):
        hil = hil or "serratus"
        up = pose_plank(110, -102.0)
        dn = pose_plank(110, -95.0)
        dn["head"] -= 4
        up["head"] += 6
        for k in (up, dn):
            k["ah"] = k["ah2"] = (-1, 0)
        sc = X.mat(-170, 220, h=4)
        return spec_tl([up, dn], None, sc, hilite=hil, hold=6, steps=7, hands_floor=True)
    # push-up with rotation
    hil = hil or "chest"
    sc = mat3d(-150, 220)
    top = pose_plank(110, -102.0)
    lo = pose_plank(116, -56.0, hand=(110, -6.5), ah=(-1, 0.3))
    rot = pose_plank(110, -102.0)
    rot["W"] = (rot["W"][0] + 4, -102.0 - 94)
    rot["ah"] = (0, 1)
    rot["twist"] = 1.0
    rot["torso"] -= 6
    rot["head"] = rot["torso"] - 8
    for k in (top, lo, rot):
        k.setdefault("twist", 0.0)
    return spec_tl([top, lo, top, rot], None, sc, hilite=hil, loop="cycle", hold=3, steps=6, hands_floor=True)


# ================================================================================================== 3D leg helper
def legs_pair(hip, v, dz=0.0):
    """near + far leg straight along the 3D vector v = (vx, vy, vz) (z towards the viewer); far leg: depth offset dz"""
    return dict(v3=v, v3b=(v[0], v[1], v[2] - dz))


def rot_x(v, deg):
    """rotate v about the horizontal x axis (frontal-plane swing of a limb): deg > 0 swings towards the viewer"""
    c, s_ = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    return (v[0], v[1] * c - v[2] * s_, v[1] * s_ + v[2] * c)


# ================================================================================================== LEG WIPERS / LEG WHEEL
def bar_frame(xb, bar_y, side=1, post_dx=78):
    """Bar seen end-on at (xb, bar_y), post on the right (side=1) or left (side=-1), grounded."""
    def fn(d, T, J, s):
        k = s * SS
        px = xb + side * post_dx
        x0, x1 = sorted((xb, px + side * 8))
        a, b = T((x0, bar_y - 4)), T((x1, bar_y + 4))
        d.rounded_rectangle([a[0], a[1], b[0], b[1]], radius=3 * k, fill=X.BENCHC)
        p, q = T((px - 6, bar_y - 4)), T((px + 6, 0))
        d.rectangle([p[0], p[1], q[0], q[1]], fill=X.BENCHC)
        f0, f1 = T((px - 30, -5)), T((px + 30, 0))
        d.rounded_rectangle([f0[0], f0[1], f1[0], f1[1]], radius=2 * k, fill=X.EQUIP)
        c = T((xb, bar_y))
        X.disc(d, c, 5.2 * k, X.METAL)
        X.disc(d, c, 2.2 * k, X.METAL_D)
    return X.Item(fn, lambda J: [(min(xb, xb + side * post_dx) - 34, bar_y - 14), (max(xb, xb + side * post_dx) + 34, 0)])


@pat("p_wiper", ("bar", ["hanging"], "obliques"), ("none", ["wheel"], "abs"), ("none", ["isometric"], "obliques"))
def p_wiper(eq, var, hil):
    if has(var, "hanging"):
        hil = hil or "obliques"
        bar_y = -280.0
        H = (0.0, bar_y + 192)
        base = dict(H=H, lean=0, head=0, wR=(19, bar_y), wL=(-19, bar_y), hR=(0.7, 1), hL=(-0.7, 1))
        keys = []
        for ang in (0, 48, 0, -48):
            k = dict(base)
            k["lR"] = k["lL"] = (180 + ang, 180 + ang)
            k["hw"] = 9
            keys.append(k)

        def scene(d, T, J, s):
            k = s * SS
            a, b = T((-64, bar_y - 4)), T((64, bar_y + 4))
            d.rounded_rectangle([a[0], a[1], b[0], b[1]], radius=3 * k, fill=X.BENCHC)
            for sx in (-64, 64):
                p, q = T((sx - 4, bar_y)), T((sx + 4, 0))
                d.rectangle([p[0], p[1], q[0], q[1]], fill=X.BENCHC)
                f0, f1 = T((sx - 22, -5)), T((sx + 22, 0))
                d.rounded_rectangle([f0[0], f0[1], f1[0], f1[1]], radius=2 * k, fill=X.EQUIP)

        def legs_front(d, T, J, s):
            k = s * SS
            for t in ("L", "R"):
                hp = J["H" + t]
                X.capsule(d, T(hp), T(J["k" + t]), 11 * k, 9 * k, X.SHORTS)
                X.capsule(d, T(J["k" + t]), T(J["a" + t]), 8 * k, 6.2 * k, X.SKIN)
                kn, an = J["k" + t], J["a" + t]
                ux, uy = an[0] - kn[0], an[1] - kn[1]
                n = math.hypot(ux, uy) or 1
                X.capsule(d, T(an), T((an[0] + ux / n * 20, an[1] + uy / n * 20)), 6.4 * k, 5.4 * k, X.SHOE)
        sc = X.Item(scene, lambda J: [(-98, bar_y - 14), (98, 0)])
        fr = X.Item(legs_front)
        return make_spec(timeline(keys, "cycle", 6, 3), None, sc, front=fr, hilite=hil, view_kind="front", loop="cycle",
                         steps=1, frame_ms=100)
    hil = hil or "abs"
    hip = (0.0, -14.0)
    S = (hip[0] - 92, hip[1])
    base = dict(hip=hip, torso=-90, head=-95, E=(S[0] + 46, -12.0), W=(S[0] + 90, -12.0), E2=(S[0] + 46, -14.0),
                W2=(S[0] + 92, -14.0), foot=-70, foot2=-70)
    mat = X.mat(-190, 175)
    if has(var, "isometric"):
        upv = (0.12, -1.0, 0.0)
        k0 = dict(base, **legs_pair(hip, upv))
        keys = []
        for i in range(6):
            u = i / 5.0
            v = rot_x((0.05, -1.0, 0.0), -70 * u)
            k = dict(base, **legs_pair(hip, v, dz=0.0))
            k["foot"] = k["foot2"] = -75 + 20 * u
            keys.append(k)
        return spec_tl(keys, None, mat, hilite=hil, hold=[4] + [1] * 4 + [12], steps=3, lying=True)
    keys = []
    beta = 40
    for g in range(0, 360, 30):
        gr = math.radians(g)
        v = (math.sin(math.radians(beta)) * math.cos(gr) + 0.12, -math.cos(math.radians(beta)),
             math.sin(math.radians(beta)) * math.sin(gr))
        k = dict(base, **legs_pair(hip, v))
        k["foot"] = k["foot2"] = -75
        keys.append(k)
    return spec_tl(keys, None, mat, hilite=hil, loop="cycle", hold=1, steps=2, frame_ms=100, lying=True)


# ================================================================================================== V-UP
@pat("p_vup", ("none", [], "abs"))
def p_vup(eq, var, hil):
    hil = hil or "abs"

    def pose(t, leg_deg, hy, reach):
        hip = (0.0, hy)
        S = X.add(hip, vup(t, 92))
        r = math.radians(leg_deg)
        A = (hip[0] + 145.9 * math.cos(r), hip[1] - 145.9 * math.sin(r))
        k = dict(A=A, hip=hip, torso=t, head=t + 8 if reach > 0.5 else t - 5, foot=-leg_deg - 80, kh=(0, -1),
                 A2=(A[0] - 3, A[1] - 2), kh2=(0, -1), foot2=-leg_deg - 80)
        rest = (S[0] - 92, S[1] - 2)
        tgt = (A[0] - 14, A[1] + 10)
        dd = math.hypot(tgt[0] - S[0], tgt[1] - S[1])
        f = min(1.0, 92 / dd)
        tgt = (S[0] + (tgt[0] - S[0]) * f, S[1] + (tgt[1] - S[1]) * f)
        for key, off in (("W", (0, 0)), ("W2", (3, -4))):
            k[key] = (rest[0] + (tgt[0] - rest[0]) * reach + off[0], rest[1] + (tgt[1] - rest[1]) * reach + off[1])
        k["ah"] = k["ah2"] = (0, -1)
        return k
    lo = pose(-90, 14, -14, 0.0)
    mid = pose(-60, 38, -17, 0.35)
    hi = pose(-24, 58, -20, 1.0)
    return spec_tl([lo, mid, hi], None, X.mat(-190, 175), hilite=hil, hold=[6, 1, 6], steps=7, lying=True)


# ================================================================================================== PULLOVERS
def _arm_arc(S, th, r=88.0, ah=(0, -1)):
    """near + far arm straight along the sagittal angle th (0 = up, negative = behind the head)"""
    w = (S[0] + r * math.sin(math.radians(th)), S[1] - r * math.cos(math.radians(th)))
    return dict(W=w, W2=(w[0] + 3, w[1] - 3), ah=ah, ah2=ah)


def _db_pair(r=11.0):
    """dumbbell held in both hands, seen end-on (disc behind the near fist)"""
    return X.dumbbell_end("wrist", r=r)


@pat("p_pullover", ("dumbbell", [], "lats"), ("dumbbell", ["cross"], "chest"), ("cable", ["cable", "incline"], "lats"),
     ("machine", ["machine"], "lats"))
def p_pullover(eq, var, hil):
    hil = hil or "lats"
    if has(var, "machine") or eq == "machine":
        return _pullover_machine(hil)
    if has(var, "cable") or eq == "cable":
        return _pullover_cable(hil)
    cross = has(var, "cross")
    if cross:
        hip = (4.0, -48.0)
        t = -76
        S = X.add(hip, vup(t, 92))
        base = dict(hip=hip, torso=t, head=t - 6, A=(96, -6), kh=(0, -1), foot=-10, A2=(104, -6), kh2=(0, -1), foot2=-10)
        top = 50
        scene = X.many(X.box(S[0] - 32, -top, S[0] + 6, -top + 12, X.BENCHC, 4), X.post_rect(S[0] - 14, -top + 12, S[0] - 8, 0),
                       X.box(S[0] - 34, -5, S[0] + 12, 0, X.EQUIP, 2))
        scene = X.many(X.mat(-200, 180, h=2), scene)
    else:
        hip = (0.0, -60.0)
        t = -90
        S = X.add(hip, vup(t, 92))
        base = dict(hip=hip, torso=t, head=t - 6, A=(78, -6), kh=(0, -1), foot=-10, A2=(86, -6), kh2=(0, -1), foot2=-10)
        scene = X.bench(-128, 80, 46, thick=12, legs=(0.12, 0.88))
    keys = []
    for th in (-4, -34, -68, -100, -132):
        k = dict(base)
        k.update(_arm_arc(S, th))
        keys.append(k)
    keys.reverse()
    return spec_tl(keys, _db_pair(), scene, hilite=hil, hold=[6, 1, 1, 1, 6], steps=3, lying=True)


def _pullover_cable(hil):
    t = -52
    hip = (0.0, -64.0)
    S = X.add(hip, vup(t, 92))
    base = dict(hip=hip, torso=t, head=t - 6, A=(84, -6), kh=(0, -1), foot=-10, A2=(92, -6), kh2=(0, -1), foot2=-10)
    n = (math.cos(math.radians(t)), math.sin(math.radians(t)))
    u = vup(t)
    p0 = (hip[0] - n[0] * 22 - u[0] * 4, hip[1] - n[1] * 22 - u[1] * 4)
    p1 = (S[0] - n[0] * 22 + u[0] * 18, S[1] - n[1] * 22 + u[1] * 18)
    px = -215
    scene = X.many(X.cable_tower(px, -26, side=-1, w=24, stack_h=96),
                   X.box(hip[0] - 34, hip[1] + 24, hip[0] + 30, hip[1] + 36, X.BENCHC, 4),
                   X.post_rect(hip[0] - 4, hip[1] + 36, hip[0] + 4, 0),
                   X.pad(p0, p1, r=8, col=X.BENCHC), X.post_rect(p0[0] - 18, -6, p0[0] + 18, 0),
                   X.post_rect(p1[0] - 3, p1[1] + 6, p1[0] + 3, 0))
    keys = []
    for th in (-126, -96, -64, -32, -2):
        k = dict(base)
        k.update(_arm_arc(S, th, 90))
        keys.append(k)
    equip = X.many(X.cable_line((px, -26), "wrist", "rope"))
    return spec_tl(keys, equip, scene, hilite=hil, hold=[6, 1, 1, 1, 6], steps=3, lying=True)


def _pullover_machine(hil):
    hip = (0.0, -50.0)
    t = -8
    S = X.add(hip, vup(t, 92))
    base = dict(hip=hip, torso=t, head=t - 4, A=(72, -6), kh=(1, -0.3), foot=0, A2=(80, -6), kh2=(1, -0.3), foot2=0)
    piv = (S[0] - 34, S[1] - 6)
    sc = X.many(X.box(-62, -2, 48, 2, X.EQUIP, 2),
                X.box(-24, -52 + 0, 36, -40, X.BENCHC, 5), X.post_rect(-3, -40, 3, 0),
                X.pad((S[0] - 22, S[1] + 6), (hip[0] - 22, hip[1] + 4), r=8, col=X.BENCHC),
                X.post_rect(piv[0] - 4, piv[1] + 4, piv[0] + 4, 0), X.box(piv[0] - 16, -5, piv[0] + 16, 0, X.EQUIP, 2))

    def lever(d, T, J, s):
        k = s * SS
        e = J["elbow"]
        dx, dy = e[0] - piv[0], e[1] - piv[1]
        n = math.hypot(dx, dy) or 1
        tip = (e[0] + dx / n * 14, e[1] + dy / n * 14)
        X.capsule(d, T(piv), T(tip), 4.6 * k, 4.6 * k, X.METAL_D)
        X.disc(d, T(piv), 6 * k, X.METAL_D)
        X.capsule(d, T((e[0] - dx / n * 6, e[1] - dy / n * 6)), T((e[0] + dx / n * 12, e[1] + dy / n * 12)), 7 * k, 7 * k,
                  (70, 78, 100))
    eq = X.Item(lever, lambda J: [piv, J["elbow"]])
    keys = []
    for th in (-30, 0, 38, 82, 124):
        k = dict(base)
        k.update(_arm_arc(S, th, 90, ah=(0, 1)))
        k["W"] = (S[0] + 90 * math.sin(math.radians(th)), S[1] - 90 * math.cos(math.radians(th)))
        keys.append(k)
    return spec_tl(keys, eq, sc, hilite=hil, hold=[6, 1, 1, 1, 6], steps=3)


# ================================================================================================== BENT-OVER FACE PULL
@pat("p_bentface", ("dumbbell", [], "shoulders"))
def p_bentface(eq, var, hil):
    hil = hil or "shoulders"
    base = dict(A=(0, -6), shin=12, thigh=-30, torso=62, head=48, foot=0, A2=(8, -6), foot2=0, kh=(1, 0), kh2=(1, 0))
    J = X.mk(**base)
    S, H = J["shoulder"], J["head"]
    low = dict(base, W=(S[0] + 4, S[1] + 92), ah=(-1, 0), W2=(S[0] + 9, S[1] + 91), ah2=(-1, 0))
    mid = dict(base, W=(S[0] + 24, S[1] + 50), E=(S[0] - 14, S[1] + 40), ah=(-1, 0), W2=(S[0] + 28, S[1] + 48),
               E2=(S[0] - 10, S[1] + 38), ah2=(-1, 0))
    hi = dict(base, E=(S[0] - 26, S[1] + 6), W=(H[0] + 8, H[1] + 22), ah=(-1, -0.4),
              E2=(S[0] - 20, S[1] - 2), W2=(H[0] + 12, H[1] + 14), ah2=(-1, -0.4))
    mid["W"], mid["W2"] = (S[0] + 4, S[1] + 56), (S[0] + 9, S[1] + 54)
    return spec_tl([low, mid, hi], X.dumbbell_end("wrist", r=9), X.mat(-110, 110, h=3), hilite=hil, hold=[6, 1, 6], steps=7)


# ================================================================================================== GLUTE BRIDGE + SINGLE-ARM PRESS
@pat("p_bridgepress", ("dumbbell", [], "chest"))
def p_bridgepress(eq, var, hil):
    hil = hil or "chest"
    ank = (92.0, -6.0)

    def pose(hy, t):
        hip = (0.0, hy)
        S = X.add(hip, vup(t, 92))
        return dict(hip=hip, torso=t, head=t - 8, A=ank, kh=(0, -1), foot=-10, A2=(ank[0] + 8, ank[1]), kh2=(0, -1), foot2=-10), S
    lo, S0 = pose(-14, -90)
    hi, S1 = pose(-72, -128)

    def arm(S, up, key):
        d = dict(key)
        d["E2"], d["W2"] = (S[0] + 46, S[1] + 2), (S[0] + 90, S[1] + 4)
        d["ah2"] = (0, 1)
        if up:
            d["W"] = (S[0] + 8, S[1] - 92)
            d["ah"] = (0.4, 1)
        else:
            d["W"] = (S[0] + 12, S[1] - 40)
            d["ah"] = (0.3, 1)
        return d
    keys = [arm(S0, False, lo), arm(S1, False, hi), arm(S1, True, hi)]
    return spec_tl(keys, X.dumbbell_end("wrist", r=11), X.mat(-190, 150), hilite=hil, hold=[5, 1, 8], steps=8, lying=True)


# ================================================================================================== AB ROLLOUT
@pat("p_rollout", ("none", ["wheel"], "abs"), ("barbell", ["barbell"], "obliques"), ("none", ["trx"], "abs"))
def p_rollout(eq, var, hil):
    if has(var, "trx"):
        return _trx_rollout(hil or "abs")
    hil = hil or "abs"
    kn = (0.0, -9.0)
    A = (-70.0, -9.0)
    r = 21.0 if eq == "barbell" else 11.0
    wy = -r

    keys = []
    for a, bend, hand_dx in ((88, 20, 52), (60, 6, 100), (22, 0, 168)):
        ar = math.radians(a)
        hip = (kn[0] + math.cos(ar) * 76, kn[1] - math.sin(ar) * 76)
        t = 90 - a + bend
        S = X.add(hip, vup(t, 92))
        W = (max(S[0] + 30, kn[0] + hand_dx), wy)
        dw = math.hypot(W[0] - S[0], W[1] - S[1])
        if dw > 94:
            f = 94 / dw
            W = (S[0] + (W[0] - S[0]) * f, S[1] + (W[1] - S[1]) * f)
        keys.append(dict(A=A, hip=hip, torso=t, head=t + 4, kh=(1, 0.6), foot=170, A2=(A[0] - 2, A[1] - 0.5), kh2=(1, 0.6),
                         foot2=170, W=W, ah=(0, -1), W2=(W[0] + 3, W[1]), ah2=(0, -1)))
    equip = wheel("wrist", r=r, col=(60, 66, 84)) if eq != "barbell" else wheel("wrist", r=r, col=(70, 76, 94))
    return spec_tl(keys, equip, X.mat(-150, 330, h=4), hilite=hil, hold=[6, 1, 6], steps=7, hands_floor=True)


def _trx_rollout(hil):
    A = (-170.0, -22.0)
    anchor_x = 25.0
    cfg = [dict(S=(25.0, -156.0), W=(25.0, -60.0)), dict(S=(60.0, -80.0), W=(150.0, -93.0))]
    # strap anchor high enough for equal strap lengths at both ends
    W0, W1 = cfg[0]["W"], cfg[1]["W"]
    ax = W0[0]
    ay = (W0[1] ** 2 - W1[1] ** 2 - (W1[0] - ax) ** 2) / (2 * (W0[1] - W1[1]))
    anchor = (ax, ay)
    keys = []
    for c in cfg:
        k = pose_plank(c["S"][0], c["S"][1], hand=c["W"], ah=(-0.4, 0.3), ank_x_extra=0)
        k["A"] = A
        S = c["S"]
        sin_t = max(-0.95, min(0.95, (A[1] - S[1]) / 237.0))
        th = math.degrees(math.asin(sin_t))
        u = (math.cos(math.radians(th)), -math.sin(math.radians(th)))
        hip = (S[0] - u[0] * 92, S[1] - u[1] * 92)
        k["hip"] = hip
        k["A"] = (hip[0] - u[0] * 145.9, hip[1] - u[1] * 145.9)
        k["A2"] = (k["A"][0] - 3, k["A"][1] - 1)
        k["W2"] = (c["W"][0] + 4, c["W"][1])
        keys.append(k)

    def straps(d, T, J, s):
        k = s * SS
        for w, off, col in ((J["wrist2"], (0, 0), (190, 150, 50)), (J["wrist"], (0, 0), STRAP)):
            a = (anchor[0] + off[0], anchor[1])
            X.capsule(d, T(a), T(w), 1.8 * k, 1.8 * k, col)
            X.capsule(d, T((w[0] - 3, w[1] - 9)), T((w[0] + 3, w[1] + 5)), 3.0 * k, 3.0 * k, (60, 66, 84))

    def ceil(d, T, J, s):
        k = s * SS
        a, b = T((-250, anchor[1] - 14)), T((anchor[0] + 90, anchor[1] - 4))
        d.rounded_rectangle([a[0], a[1], b[0], b[1]], radius=3 * k, fill=X.BENCHC)
        p, q = T((-250, anchor[1] - 6)), T((-238, 0))
        d.rectangle([p[0], p[1], q[0], q[1]], fill=X.BENCHC)
        f0, f1 = T((-268, -5)), T((-220, 0))
        d.rounded_rectangle([f0[0], f0[1], f1[0], f1[1]], radius=2 * k, fill=X.EQUIP)
        X.disc(d, T((anchor[0], anchor[1] - 2)), 5 * k, X.METAL_D)
    sc = X.many(X.mat(-215, 200, h=4), X.Item(ceil, lambda J: [(-270, anchor[1] - 18), (anchor[0] + 95, 0)]))
    return spec_tl(keys, X.Item(straps, lambda J: [anchor]), sc, hilite=hil, hold=[6, 6], steps=10, hands_floor=True)


# ================================================================================================== BODY ROWS (inverted / ring / TRX / isometric)
def _supine_incline(A, alpha, hand, ah=(0.3, 1), head_add=-4):
    """straight body, heels at A (floor), rising to the shoulders at angle alpha above the floor (head to the left)."""
    a = math.radians(alpha)
    u = (-math.cos(a), -math.sin(a))
    hip = (A[0] + u[0] * 145.9, A[1] + u[1] * 145.9)
    t = -(90 - alpha)
    S = (hip[0] + u[0] * 92, hip[1] + u[1] * 92)
    k = dict(A=A, hip=hip, torso=t, head=t + head_add, foot=-80, kh=(0, -1), A2=(A[0] + 4, A[1] - 1), kh2=(0, -1),
             foot2=-80, W=hand, ah=ah, W2=(hand[0] + 3, hand[1] - 3), ah2=ah)
    return k, S


@pat("p_bodyrow", ("bar", ["bar"], "lats"), ("none", ["rings"], "lats"), ("none", ["trx"], "lats"),
     ("bar", ["bar", "isometric"], "lats"))
def p_bodyrow(eq, var, hil):
    hil = hil or "lats"
    A = (218.0, -9.0)
    bar_y = -178.0
    xb = 0.0
    iso = has(var, "isometric")
    a0, a1 = 20.0, 36.0
    W0 = (xb, bar_y)
    k0, S0 = _supine_incline(A, a0, W0)
    # keep the hands on the bar: shoulders start under it
    if has(var, "rings", "trx"):
        k1, S1 = _supine_incline(A, a1, (0, 0), ah=(0.3, 1))
        u = (-math.cos(math.radians(a1)), -math.sin(math.radians(a1)))
        n = (math.sin(math.radians(a1)), -math.cos(math.radians(a1)))
        W0 = (S0[0] + 4, S0[1] - 88)
        anchor = (W0[0], -272.0)
        L = W0[1] - anchor[1]
        tg = (S1[0] + 14, S1[1] - 22)
        dd = math.hypot(tg[0] - anchor[0], tg[1] - anchor[1])
        W1 = (anchor[0] + (tg[0] - anchor[0]) * L / dd, anchor[1] + (tg[1] - anchor[1]) * L / dd)
        k1["W"], k1["W2"] = W1, (W1[0] + 3, W1[1] - 3)
        k0["W"], k0["W2"] = W0, (W0[0] + 3, W0[1] - 3)
        rings = has(var, "rings")

        def straps(d, T, J, s):
            k = s * SS
            for w, col in ((J["wrist2"], (190, 150, 50)), (J["wrist"], STRAP)):
                X.capsule(d, T(anchor), T(w), 1.8 * k, 1.8 * k, col)
                if rings:
                    d.ellipse([T(w)[0] - 8 * k, T(w)[1] - 8 * k - 3 * k, T(w)[0] + 8 * k, T(w)[1] + 8 * k - 3 * k],
                              outline=(236, 224, 200), width=int(2.4 * k))
                else:
                    X.capsule(d, T((w[0] - 3, w[1] - 9)), T((w[0] + 3, w[1] + 5)), 3.0 * k, 3.0 * k, (60, 66, 84))

        def rig(d, T, J, s):
            k = s * SS
            px = -96.0
            a, b = T((px, anchor[1] - 14)), T((anchor[0] + 60, anchor[1] - 4))
            d.rounded_rectangle([a[0], a[1], b[0], b[1]], radius=3 * k, fill=X.BENCHC)
            p, q = T((px - 6, anchor[1] - 6)), T((px + 6, 0))
            d.rectangle([p[0], p[1], q[0], q[1]], fill=X.BENCHC)
            f0, f1 = T((px - 26, -5)), T((px + 26, 0))
            d.rounded_rectangle([f0[0], f0[1], f1[0], f1[1]], radius=2 * k, fill=X.EQUIP)
            X.disc(d, T((anchor[0], anchor[1] - 2)), 5 * k, X.METAL_D)
        sc = X.many(X.mat(-100, 240, h=2), X.Item(rig, lambda J: [(-124, anchor[1] - 18), (anchor[0] + 66, 0)]))
        equip = X.Item(straps, lambda J: [anchor])
        k1["head"] += 2
    else:
        k1, S1 = _supine_incline(A, a1, W0, ah=(0.3, 1))
        k1["head"] += 2
        xr = 6.0

        def rack(d, T, J, s):
            k = s * SS
            p, q = T((xr - 5, bar_y)), T((xr + 5, 0))
            d.rectangle([p[0], p[1], q[0], q[1]], fill=X.BENCHC)
            f0, f1 = T((xr - 26, -5)), T((xr + 26, 0))
            d.rounded_rectangle([f0[0], f0[1], f1[0], f1[1]], radius=2 * k, fill=X.EQUIP)
            c = T((xb, bar_y))
            X.disc(d, c, 5.2 * k, X.METAL)
            X.disc(d, c, 2.2 * k, X.METAL_D)
        sc = X.Item(rack, lambda J: [(xr - 30, bar_y - 12), (xr + 30, 0)])
        sc = X.many(X.mat(-80, 250, h=2), sc)
        equip = None
    hl = [4, 12] if iso else [6, 6]
    return spec_tl([k0, k1], equip, sc, hilite=hil, hold=hl, steps=9, lying=True)


# ================================================================================================== BAR SKILLS (muscle-up, active hang, front lever pull-up)
def _hang_body(S, t, W, legs, ah=(0.3, 1), head=None, sh_up=0.0, foot=40):
    hip = (S[0] - math.sin(math.radians(t)) * 92 * -1 * -1, S[1] + math.cos(math.radians(t)) * 92) if False else (
        S[0] - math.sin(math.radians(t)) * 92, S[1] + math.cos(math.radians(t)) * 92)
    A = (hip[0] + legs[0], hip[1] + legs[1])
    k = dict(A=A, hip=hip, torso=t, head=t * 0.4 if head is None else head, kh=(1, 0), foot=foot, W=W, ah=ah,
             A2=(A[0] + 3, A[1] - 2), kh2=(1, 0), foot2=foot, W2=(W[0] + 4, W[1]), ah2=ah, sh_up=sh_up)
    return k


@pat("p_barskill", ("bar", ["muscle_up"], "lats"), ("bar", ["active_hang"], "lats"), ("bar", ["front_lever"], "abs"))
def p_barskill(eq, var, hil):
    hil = hil or "lats"
    if has(var, "front_lever"):
        return _front_lever_pullup(hil)
    bar_y, xb = -320.0, 40.0
    W = (xb, bar_y)
    if has(var, "active_hang"):
        keys = []
        for dy, up, th in ((112, 14.0, 6), (96, 0.0, -6)):
            S = (xb - 6, bar_y + dy)
            keys.append(_hang_body(S, 2, W, (-26, 106), ah=(0.1, 1), head=th, sh_up=up, foot=60))
        return spec_tl(keys, None, X.pullup_frame(xb, bar_y), hilite=hil, hold=[6, 10], steps=7)
    # muscle-up
    k0 = _hang_body((xb - 6, bar_y + 98), 2, W, (-36, 118))
    k1 = _hang_body((xb - 30, bar_y + 26), -16, W, (-70, 100), ah=(-0.4, 1), head=-8)
    k2 = _hang_body((xb + 4, bar_y - 22), 40, W, (-52, 108), ah=(-1, -0.4), head=52)
    k3 = _hang_body((xb + 2, bar_y - 96), 8, W, (-18, 140), ah=(0, 1), head=14)
    return spec_tl([k0, k1, k2, k3], None, X.pullup_frame(xb, bar_y), hilite=hil, hold=[5, 1, 1, 6], steps=5)


def _front_lever_pullup(hil):
    bar_y, xb = -280.0, 0.0
    W = (xb, bar_y)

    def pose(sy, sx):
        S = (sx, sy)
        hip = (S[0] + 92, S[1])
        A = (hip[0] + 145.9, hip[1] + 2)
        return dict(A=A, hip=hip, torso=-90, head=-94, kh=(0, -1), foot=-10, A2=(A[0] - 2, A[1] - 1), kh2=(0, -1), foot2=-10,
                    W=W, ah=(0.2, 1), W2=(W[0] + 4, W[1]), ah2=(0.2, 1))
    k0 = pose(bar_y + 92, xb - 8)
    k1 = pose(bar_y + 38, xb + 4)
    return spec_tl([k0, k1], None, bar_frame(xb, bar_y, side=-1, post_dx=90), hilite=hil, hold=[6, 6], steps=9)
