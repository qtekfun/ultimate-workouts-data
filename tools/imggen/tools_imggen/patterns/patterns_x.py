"""Calisthenics holds, levers, inversions, hangs and a few floor / grip items (keys specs, extras_b engine).

Patterns: l_sit, planche, lever, handstand, hang, hollow, support_hold, static_hold, floor_core, power_clean.
Conventions are those of extras_b.py (world x right, y down, floor top y = 0, standing ankle (0, -6)).
Inverted figures keep the engine rule: the torso "front normal" turns with the torso angle, so a figure that is
upside down faces -x (hands on the floor at x = 0, feet up / towards the left).
"""
import math
from PIL import ImageDraw  # noqa: F401
try:
    from . import extras_b as X
except ImportError:  # pragma: no cover
    import extras_b as X

mk = X.mk
PATTERNS = {}
TEST_VARIANTS = {}
SS = X.SS
LEG, TOR, UA, FA = 146.0, 92.0, 50.0, 46.0
ARM = UA + FA
HAND_Y = -6.5


def pat(name, *tests):
    def deco(fn):
        PATTERNS[name] = fn
        TEST_VARIANTS[name] = list(tests) or [("none", [], None)]
        return fn
    return deco


def has(var, *names):
    return any(n in var for n in names)


def spec(keys, equipment=None, scene=None, front=None, hilite=None, **kw):
    d = dict(keys=keys, rotation=0.0, equipment=equipment, scene=scene, front=front, hilite=hilite)
    d.update(kw)
    return d


# ------------------------------------------------------------------------------------------------ geometry
def rad(a):
    return math.radians(a)


def vup(a, n=1.0):
    return (math.sin(rad(a)) * n, -math.cos(rad(a)) * n)


def padd(p, q):
    return (p[0] + q[0], p[1] + q[1])


def psub(p, q):
    return (p[0] - q[0], p[1] - q[1])


def pmul(p, k):
    return (p[0] * k, p[1] * k)


def pdist(p, q):
    return math.hypot(p[0] - q[0], p[1] - q[1])


def ang_up(p, q):
    return math.degrees(math.atan2(q[0] - p[0], -(q[1] - p[1])))


def hip_between(A, S, r1=LEG, r2=TOR, up=True):
    """Hip position with |hip - A| = r1 (legs) and |hip - S| = r2 (torso); `up` picks the intersection with the smaller y."""
    d = pdist(A, S)
    if d >= r1 + r2 - 0.6:
        k = r1 / (r1 + r2)
        return (A[0] + (S[0] - A[0]) * k, A[1] + (S[1] - A[1]) * k)
    a = (r1 * r1 - r2 * r2 + d * d) / (2 * d)
    h = math.sqrt(max(r1 * r1 - a * a, 0.0))
    ux, uy = (S[0] - A[0]) / d, (S[1] - A[1]) / d
    bx, by = A[0] + ux * a, A[1] + uy * a
    c1 = (bx - uy * h, by + ux * h)
    c2 = (bx + uy * h, by - ux * h)
    pick = min if up else max
    return pick((c1, c2), key=lambda c: c[1])


def line_body(S, t, leg_bend=0.0):
    """Hip and ankle of a straight body whose torso has up-angle t and whose shoulder is S."""
    hip = psub(S, vup(t, TOR))
    A = psub(hip, vup(t, LEG - leg_bend))
    return hip, A


def foot_along(hip, A):
    """Screen angle of a pointed foot continuing the leg direction."""
    return math.degrees(math.atan2(A[1] - hip[1], A[0] - hip[0]))


def lerp(a, b, t):
    return a + (b - a) * t


def leg_fk(hip, thigh_deg, shin_deg, shin_len=70.0, thigh_len=76.0):
    """Ankle and knee hint for a leg given by screen directions (degrees, 0 = +x, 90 = down) of thigh and shin."""
    u = (math.cos(rad(thigh_deg)), math.sin(rad(thigh_deg)))
    v = (math.cos(rad(shin_deg)), math.sin(rad(shin_deg)))
    K = (hip[0] + u[0] * thigh_len, hip[1] + u[1] * thigh_len)
    A = (K[0] + v[0] * shin_len, K[1] + v[1] * shin_len)
    mid = ((A[0] + hip[0]) / 2, (A[1] + hip[1]) / 2)
    return A, (K[0] - mid[0], K[1] - mid[1]), K


# ------------------------------------------------------------------------------------------------ items
def _rect(d, T, s, x0, y0, x1, y1, col, r=2.0):
    a, b = T((x0, y0)), T((x1, y1))
    d.rounded_rectangle([a[0], a[1], b[0], b[1]], radius=r * s * SS, fill=col)


WALLC = (206, 212, 226)
WALLD = (186, 193, 210)
WOOD = (206, 170, 120)
WOODD = (178, 142, 96)


def blocks(xs, h, w=22, col=X.METAL_D):
    """Parallettes seen from the side: a short bar at height h on two legs with feet."""
    def fn(d, T, J, s):
        k = s * SS
        for x in xs:
            _rect(d, T, s, x - w / 2 - 4, -h - 3, x + w / 2 + 4, -h + 3, col, 3)
            for lx in (x - w / 2, x + w / 2):
                _rect(d, T, s, lx - 2.5, -h, lx + 2.5, 0, col, 1.5)
                _rect(d, T, s, lx - 8, -3, lx + 8, 0, X.EQUIP, 1.5)
    return X.Item(fn, lambda J: [(min(xs) - w, -h - 4), (max(xs) + w, 0)])


def wall(x, side=-1, top=-420, w=18):
    """Vertical wall; `side` -1 = wall to the left of x."""
    x0, x1 = (x - w, x) if side < 0 else (x, x + w)

    def fn(d, T, J, s):
        _rect(d, T, s, x0, top, x1, 0, WALLC, 2)
    return X.Item(fn, lambda J: [(x0, top), (x1, 0)])


def rig(xb, bar_y, side=1, post_dx=80, h_arm=True):
    """Bar seen end-on at (xb, bar_y), arm to a post standing on the floor `post_dx` away (side = +1 right, -1 left)."""
    def fn(d, T, J, s):
        k = s * SS
        px = xb + side * post_dx
        x0, x1 = sorted((xb, px + side * 8))
        _rect(d, T, s, x0, bar_y - 4, x1, bar_y + 4, X.BENCHC, 3)
        a, b = T((px - 7 + (side * 1), bar_y - 4)), T((px + 7 + (side * 1), 0))
        d.rectangle([a[0], a[1], b[0], b[1]], fill=X.BENCHC)
        f0, f1 = T((px - 32, -5)), T((px + 32, 0))
        d.rounded_rectangle([f0[0], f0[1], f1[0], f1[1]], radius=2 * k, fill=X.EQUIP)
        c = T((xb, bar_y))
        X.disc(d, c, 5.2 * k, X.METAL)
        X.disc(d, c, 2.2 * k, X.METAL_D)
    return X.Item(fn, lambda J: [(xb - 30, bar_y - 14), (xb + side * (post_dx + 34), 0)])


def pulse(anchor, rmax=22.0, base=None):
    """Orange tension ring around a point; its radius follows J['hand_pt'] - J['wrist'] (x component, 0..1)."""
    def fn(d, T, J, s):
        p = J["hand_pt"][0] - J["wrist"][0] if "hand_pt" in J else 0.0
        c = anchor(J) if callable(anchor) else J[anchor]
        k = s * SS
        r = (rmax * (0.55 + 0.45 * p)) * k
        x, y = T(c)
        d.ellipse([x - r, y - r, x + r, y + r], outline=(255, 120, 20, int(80 + 120 * p)), width=int(2.4 * k))
        r2 = r * 0.62
        d.ellipse([x - r2, y - r2, x + r2, y + r2], fill=(255, 120, 20, int(40 + 70 * p)))
    return X.Item(fn, lambda J: [padd(anchor(J) if callable(anchor) else J[anchor], (-rmax - 2, -rmax - 2)),
                                padd(anchor(J) if callable(anchor) else J[anchor], (rmax + 2, rmax + 2))])


def fist_on(anchor="hand_pt"):
    return X.fist(anchor)


def top_view_inset(anchor, spread, label_legs=True):
    """Tiny top-down icon (head, shoulders, legs in a V) placed relative to a joint, to show leg spread."""
    def pt(J):
        return padd(J[anchor], (120, -92))

    def fn(d, T, J, s):
        k = s * SS
        c = pt(J)
        x, y = T(c)
        w = 36 * k
        d.rounded_rectangle([x - w, y - w, x + w, y + w], radius=6 * k, fill=(255, 255, 255, 200), outline=(170, 178, 198), width=int(1.4 * k))
        # body (circle) at the bottom, legs spread forward (up in the icon)
        bx, by = x, y + 14 * k
        ang = rad(spread)
        for sg in (-1, 1):
            ex, ey = bx + sg * math.sin(ang) * 26 * k, by - math.cos(ang) * 26 * k
            d.line([(bx, by), (ex, ey)], fill=X.SHORTS, width=int(5 * k))
            X.disc(d, (ex, ey), 3.2 * k, X.SHOE)
        X.disc(d, (bx, by), 8 * k, X.SHIRT)
        X.disc(d, (bx, by + 8 * k), 4.5 * k, X.SKIN)
        for sg in (-1, 1):
            d.line([(bx + sg * 6 * k, by - 2 * k), (bx + sg * 17 * k, by + 4 * k)], fill=X.SKIN, width=int(3.4 * k))
    return X.Item(fn, lambda J: [padd(pt(J), (-38, -38)), padd(pt(J), (38, 38))])


# ================================================================================================= HANG
BAR_Y = -362.0


def _hang_kw(xb, sh_up, t, lb=0.0, grip_y=BAR_Y, head=None, ah=(0.3, 1), foot=70, wx=0.0):
    ay = grip_y + ARM
    S = (xb - 2, ay + sh_up)
    hip = psub(S, vup(t, TOR))
    A = (hip[0] - lb, hip[1] + math.sqrt(144.0 ** 2 - lb ** 2))
    return dict(A=A, hip=hip, torso=t, head=t if head is None else head, kh=(1, 0), foot=foot,
                W=(xb + wx, grip_y), ah=ah, sh_up=sh_up)


def _hang_scene(kind, xb):
    if kind == "bar":
        return X.pullup_frame(xb, BAR_Y)
    gy = BAR_Y
    wx = xb + 60

    def fn(d, T, J, s):
        k = s * SS
        _rect(d, T, s, wx, gy - 46, wx + 20, 0, WALLC, 2)                          # wall
        _rect(d, T, s, xb + 4, gy, wx, gy + 16, WOODD, 3)                           # board
        if kind == "fingerboard":
            _rect(d, T, s, xb + 4, gy - 5, xb + 12, gy + 1, WOOD, 1.5)             # 20 mm edge
        else:
            c = T((xb + 16, gy + 1))
            r = 15 * k                                                                  # sloper dome
            d.pieslice([c[0] - r, c[1] - r, c[0] + r, c[1] + r], 180, 360, fill=WOOD)
        f0, f1 = T((wx - 20, -5)), T((wx + 32, 0))
        d.rounded_rectangle([f0[0], f0[1], f1[0], f1[1]], radius=2 * k, fill=X.EQUIP)
        _rect(d, T, s, wx + 12, gy - 46, wx + 20, 0, X.BENCHC, 1)
    return X.Item(fn, lambda J: [(xb - 30, gy - 50), (wx + 34, 0)])


@pat("hang", ("bar", ["dead"], "forearms"), ("bar", ["arch"], "lats"), ("none", ["fingerboard"], "forearms"),
     ("none", ["sloper"], "forearms"))
def hang(eq, var, hil):
    xb = 8
    kind = "fingerboard" if has(var, "fingerboard") else "sloper" if has(var, "sloper") else "bar"
    hil = hil or ("lats" if has(var, "arch") else "forearms")
    grip_y = BAR_Y
    wx = 0.0
    fistd = None
    if kind == "fingerboard":
        grip_y, wx, fistd = BAR_Y - 1, -1.0, (9, -4)
    elif kind == "sloper":
        grip_y, wx, fistd = BAR_Y + 4, -1.0, (13, -2)
    # step off a box: toes on the box, arms nearly straight
    ank = (-44.0, -47.0)
    hip0 = (ank[0] + 8, ank[1] - 140.0)
    start = dict(A=ank, hip=hip0, torso=4, head=2, kh=(1, 0), foot=0, W=(xb + wx, grip_y), ah=(0.4, 1), sh_up=4)
    dead = _hang_kw(xb, 10, 0, 0, grip_y, ah=(0.3, 1), wx=wx)
    if has(var, "arch"):
        act = _hang_kw(xb, -6, 9, 34, grip_y, head=-2, wx=wx)
        keys = [start, dead, act]
    else:
        act = _hang_kw(xb, 4, 0, 0, grip_y, wx=wx)
        act2 = _hang_kw(xb, 10, 3, 6, grip_y, wx=wx)
        keys = [start, dead, act2, act]
    for kk in keys:
        if fistd:
            kk["hand"] = fistd
    scene = X.many(_hang_scene(kind, xb), X.box(-76, -40, -14, 0, WOOD, 3))
    front = fist_on() if fistd else None
    return spec(keys, None, scene, front, hilite=hil, hold=(700, 900))


# ================================================================================================= LEVER
LEV_Y = -345.0


def _lever_scene(xb, bar_y, side):
    return rig(xb, bar_y, side=side, post_dx=76)


def _lev_pose(S, t, W, head_off, foot, kh, ah, bend=None):
    hip, A = line_body(S, t)
    return dict(A=A, hip=hip, torso=t, head=t + head_off, foot=foot, kh=kh, W=W, ah=ah)


@pat("lever", ("bar", ["front"], "lats"), ("bar", ["front", "tuck"], "lats"), ("bar", ["back"], "back"),
     ("none", ["elbow"], "abs"))
def lever(eq, var, hil):
    if has(var, "elbow"):
        return _elbow_lever(hil or "abs")
    bar_y = LEV_Y
    xb = 8.0
    if has(var, "back"):
        side = 1                           # post on the head side (right)
        S = (xb, bar_y + ARM)
        W = (xb, bar_y)
        hang = dict(_hang_kw(xb, 0, 0, 0, bar_y), foot=70)
        keys = [hang]
        for t in (30, 60):
            kw = _lev_pose(S, t, W, 6, foot_along(*line_body(S, t)), (0, 1), (0.3, 1))
            keys.append(kw)
        lev = _lev_pose(S, 90, W, 8, 0, (0, 1), (0.3, 1))
        lev["foot"] = foot_along(lev["hip"], lev["A"])
        lev2 = dict(lev, hip=(lev["hip"][0], lev["hip"][1] + 3), A=(lev["A"][0] - 2, lev["A"][1] + 6), head=lev["head"] + 5)
        keys += [lev, lev2]
        return spec(keys, None, _lever_scene(xb, bar_y, side), None, hilite=hil or "back", hold=(700, 1000))
    side = -1                              # post behind the head (left)
    S = (xb + 4, bar_y + ARM)
    W = (xb, bar_y)
    hang = dict(_hang_kw(xb, 0, 0, 0, bar_y), foot=70)
    keys = [hang]
    if has(var, "tuck"):
        for t in (-30, -60):
            hip, A = line_body(S, t, leg_bend=0)
            hipc = hip
            Ac, kh, K = leg_fk(hipc, 90 + (-t) * 0.2 + 40 * (-t) / 90, 90 + 20 - (-t), )
            keys.append(dict(A=Ac, hip=hipc, torso=t, head=t - 4, foot=0, kh=kh, W=W, ah=(-0.3, 1)))
        hip = line_body(S, -90)[0]
        # knees to the chest: thigh points up-left (towards the face side), shin folds back
        Ac, kh, K = leg_fk(hip, 235, 20)
        lev = dict(A=Ac, hip=hip, torso=-90, head=-96, foot=-20, kh=kh, W=W, ah=(-0.3, 1))
        lev2 = dict(lev, hip=(hip[0], hip[1] + 3), A=(Ac[0], Ac[1] + 3), head=-100)
        keys += [lev, lev2]
    else:
        for t in (-30, -60):
            keys.append(_lev_pose(S, t, W, -4, foot_along(*line_body(S, t)), (0, -1), (-0.3, 1)))
        lev = _lev_pose(S, -90, W, -6, 0, (0, -1), (-0.3, 1))
        lev["foot"] = foot_along(lev["hip"], lev["A"])
        lev2 = dict(lev, hip=(lev["hip"][0], lev["hip"][1] + 3), A=(lev["A"][0], lev["A"][1] + 6), head=lev["head"] - 4)
        keys += [lev, lev2]
    return spec(keys, None, _lever_scene(xb, bar_y, side), None, hilite=hil or "lats", hold=(700, 1000))


def _elbow_lever(hil):
    # prone, balanced on the elbows pressed into the abdomen, hands flat on the floor, head forward
    S = (92.0, -64.0)
    hip = (S[0] - TOR, S[1])
    A = (hip[0] - LEG, hip[1])
    hold = dict(A=A, hip=hip, torso=90, head=98, foot=foot_along(hip, A), kh=(0, 1),
                E=(S[0] - 40, -54.0), W=(S[0] - 28, -6.5), ah=(-1, 0))
    S0 = (92.0, -78.0)
    A0 = (-96.0, -22.0)
    hip0 = hip_between(A0, S0, up=True)
    t0 = ang_up(hip0, S0)
    setup = dict(A=A0, hip=hip0, torso=t0, head=t0 + 8, foot=64, kh=(0, -1),
                 E=(S0[0] - 38, -58.0), W=(S0[0] - 26, -6.5), ah=(-1, 0))
    hold2 = dict(hold, head=102, A=(A[0], A[1] - 3))
    return spec([setup, hold, hold2], None, X.mat(-170, 160, h=4), None, hilite=hil, hands_floor=True, hold=(700, 1000))


# ================================================================================================= PLANCHE
def _planche_straight(lean, ank_y=-22.0, foot=64):
    W = (0.0, HAND_Y)
    Sy = HAND_Y - math.sqrt(ARM ** 2 - lean ** 2) + 0.4
    S = (lean, Sy)
    dy = ank_y - Sy
    dx = math.sqrt(max((TOR + LEG - 1) ** 2 - dy * dy, 1))
    A = (S[0] - dx, ank_y)
    hip = hip_between(A, S)
    t = ang_up(hip, S)
    return dict(A=A, hip=hip, torso=t, head=t + 8, foot=foot, kh=(0, -1), W=W, ah=(1, 0))


def _planche_tuck(lean, t, thigh, shin):
    W = (0.0, HAND_Y)
    Sy = HAND_Y - math.sqrt(ARM ** 2 - lean ** 2) + 0.4
    S = (lean, Sy)
    hip = psub(S, vup(t, TOR))
    A, kh, K = leg_fk(hip, thigh, shin)
    return dict(A=A, hip=hip, torso=ang_up(hip, S), head=ang_up(hip, S) + 14, foot=-30, kh=kh, W=W, ah=(1, 0))


@pat("planche", ("none", ["lean"], "shoulders"), ("none", ["tuck"], "shoulders"), ("none", ["dynamic"], "abs"),
     ("none", ["frog"], "shoulders"))
def planche(eq, var, hil):
    hil = hil or "shoulders"
    if has(var, "frog"):
        return _frog(hil)
    mat_ = X.mat(-250, 120, h=4)
    flat = _planche_straight(8)
    lean_pose = _planche_straight(70)
    lean2 = _planche_straight(76)
    if has(var, "lean"):
        return spec([flat, lean_pose, lean2], None, mat_, None, hilite=hil, hands_floor=True, hold=(700, 1000))
    tk = _planche_tuck(30, 100, 40, 172)
    if has(var, "tuck"):
        tk2 = _planche_tuck(34, 102, 40, 172)
        return spec([flat, lean_pose, tk, tk2], None, mat_, None, hilite=hil, hands_floor=True, hold=(700, 1000))
    adv = _planche_tuck(42, 96, 26, 178)
    return spec([lean_pose, tk, adv], None, mat_, None, hilite=hil, hands_floor=True, loop="cycle", steps=7)


def _frog(hil):
    W = (0.0, HAND_Y)
    def pose(sx, sy, thigh, shin, tdel=0):
        S = (sx, sy)
        hip = (S[0] - 86.0, S[1] - 31.0)
        t = ang_up(hip, S)
        A, kh, K = leg_fk(hip, thigh, shin)
        return dict(A=A, hip=hip, torso=t, head=t - 8, foot=-20, kh=kh, W=W, ah=(-1, -0.2))
    # crouch (squat with hands down), then knees on the upper arms and the feet leave the floor
    crouch = dict(A=(-70.0, -6.0), hip=(-70.0, -62.0), torso=70, head=62, foot=0, kh=(1, 0), W=W, ah=(-1, 0.2))
    a = pose(14, -80, 38, 215)
    b = pose(22, -88, 38, 215)
    c = pose(24, -90, 38, 215)
    return spec([crouch, a, b, c], None, X.mat(-170, 100, h=4), None, hilite=hil, hands_floor=True, hold=(700, 1000))


# ================================================================================================= HANDSTAND family
def _inv(Wx, S, A, head=None, hint=(1, -0.2), foot=None, kh=(-1, 0), hy=None):
    """Inverted / piked body: hands at (Wx, floor), shoulder S above them, ankle A (legs straight)."""
    hip = hip_between(A, S, up=True)
    t = ang_up(hip, S)
    if t < 0:
        t += 360.0
    h = min(t, 176.0) if head is None else head
    return dict(A=A, hip=hip, torso=t, head=h, foot=foot_along(hip, A) if foot is None else foot, kh=kh,
                W=(Wx, HAND_Y), ah=hint, behind=True)


def _hs_line(Wx, S_y, wall_x=None, tilt=None):
    """Straight handstand line; with wall_x the feet rest on the wall (toes on it), else a vertical line."""
    S = (Wx, S_y)
    if wall_x is not None:
        dx = Wx - (wall_x + 7.0)
        A = (wall_x + 7.0, S_y - math.sqrt(max((TOR + LEG - 0.3) ** 2 - dx * dx, 1.0)))
    else:
        A = (Wx - (tilt or 0.0), S_y - (TOR + LEG - 0.3))
    return S, A


def _bent_arm_hs(Wx, S_y, wall_x, hint=(1, -0.3)):
    S, A = _hs_line(Wx, S_y, wall_x)
    return _inv(Wx, S, A, head=170, hint=hint)


@pat("handstand", ("none", [], "shoulders"), ("none", ["wall"], "shoulders"), ("none", ["wall", "pushup"], "shoulders"),
     ("box", ["pushup"], "shoulders"), ("none", ["pike"], "shoulders"))
def handstand(eq, var, hil):
    hil = hil or "shoulders"
    top_y = HAND_Y - 95.0
    mat_ = X.mat(-300, 120, h=4)
    if has(var, "pike") and not has(var, "pushup"):
        plank = _planche_straight(0)
        A = (-132.0, -6.0)
        pike = _inv(0.0, (0.0, top_y), A, head=168, foot=0)
        pike2 = _inv(0.0, (-4.0, top_y), (A[0] + 4, A[1]), head=172, foot=0)
        return spec([plank, pike, pike2], None, mat_, None, hilite=hil, hands_floor=True, hold=(700, 1000))
    if eq == "box" or has(var, "box"):
        box_top = 52.0
        bx0, bx1 = -214.0, -128.0
        A0 = (-150.0, -box_top - 7.0)
        topk = _inv(0.0, (0.0, top_y), A0, head=170, foot=0)
        bot = _inv(0.0, (8.0, HAND_Y - 46.0), A0, head=175, hint=(1, -0.1), foot=0)
        bot["ah"] = (1, -0.2)
        scene = X.many(mat_, X.box(bx0, -box_top, bx1, 0, WOOD, 4))
        return spec([topk, bot], None, scene, None, hilite=hil, hands_floor=True, hold=(500, 500))
    if has(var, "wall"):
        wx = -66.0
        wl = wall(wx, side=-1, top=-360)
        scene = X.many(mat_, wl)
        if has(var, "pushup"):
            Wx = wx + 52.0
            topk = _bent_arm_hs(Wx, top_y, wx)
            bot = _bent_arm_hs(Wx, HAND_Y - 48.0, wx)
            return spec([topk, bot], None, scene, None, hilite=hil, hands_floor=True, hold=(500, 500))
        # walk up the wall (chest to the wall): plank at the wall base -> hands walk in -> handstand
        k0 = _planche_straight(0)
        A0 = (wx + 8.0, -22.0)
        S0 = (0.0, top_y)
        dx = math.sqrt((TOR + LEG - 0.3) ** 2 - (A0[1] - S0[1]) ** 2)
        Wx0 = wx + 8.0 + dx
        k0 = dict(_inv(Wx0, (Wx0, top_y), A0, head=120, foot=64, kh=(0, -1)))
        k0["torso"] = ang_up(k0["hip"], (Wx0, top_y))
        k0["head"] = k0["torso"] + 10
        keys = [k0]
        for Wx, ay in ((wx + 170, -60.0), (wx + 120, -150.0), (wx + 82, -250.0)):
            S = (Wx, top_y)
            A = (wx + 8.0, ay)
            keys.append(_inv(Wx, S, A, head=150, foot=-80))
        S, A = _hs_line(wx + 52.0, top_y, wx)
        h1 = _inv(wx + 52.0, S, A, head=170)
        S2, A2 = _hs_line(wx + 50.0, top_y, wx)
        h2 = _inv(wx + 50.0, S2, A2, head=172)
        keys += [h1, h2]
        return spec(keys, None, scene, None, hilite=hil, hands_floor=True, hold=(700, 1100))
    # free handstand: pike -> kick up -> balance
    A0 = (-132.0, -6.0)
    keys = [_inv(0.0, (0.0, top_y), A0, head=168, foot=0)]
    pk = keys[0]
    hs = _inv(0.0, (0.0, top_y), (0.0, top_y - (TOR + LEG - 0.3)), head=178)
    for u in (0.25, 0.5, 0.75):
        hipk = (lerp(pk["hip"][0], hs["hip"][0], u), lerp(pk["hip"][1], hs["hip"][1], u))
        phi = lerp(math.degrees(math.atan2(A0[1] - pk["hip"][1], A0[0] - pk["hip"][0])), 270.0, u)
        A = (hipk[0] + (LEG - 1) * math.cos(rad(phi)), hipk[1] + (LEG - 1) * math.sin(rad(phi)))
        keys.append(_inv(0.0, (0.0, top_y), A, head=lerp(168, 178, u), foot=phi))
    keys.append(hs)
    hs2 = _inv(0.0, (-2.0, top_y), (-9.0, top_y - (TOR + LEG - 0.3)), head=178)
    keys.append(hs2)
    return spec(keys, None, mat_, None, hilite=hil, hands_floor=True, hold=(700, 1000))


# ================================================================================================= L-SIT
def _parallettes(h, xs=(0.0,)):
    return blocks(list(xs), h, w=34)


@pat("l_sit", ("none", [], "abs"), ("none", ["tuck"], "abs"), ("none", ["straddle"], "abs"), ("none", ["foot"], "abs"),
     ("bench", ["tuck"], "abs"))
def l_sit(eq, var, hil):
    hil = hil or "abs"
    bench = eq == "bench"
    h = 46.0 if bench else 26.0
    wy = -h - 6.5
    Sy = wy - 95.0
    hip_y = Sy + TOR
    W = (6.0, wy)
    seat_hip = (0.0, -14.0)
    start = dict(A=(144.0, -9.0), hip=seat_hip, torso=-2, head=0, foot=-70, kh=(0, -1), W=W, ah=(-1, 0.3))
    if bench:
        start["ah"] = (-1, 0.5)
    hip = (0.0, hip_y)
    if has(var, "tuck"):
        A, kh, K = leg_fk(hip, 305, 115)
        start = dict(A=(120.0, -9.0), hip=seat_hip, torso=-2, head=0, foot=-70, kh=(0, -1), W=W, ah=(-1, 0.4))
        key = dict(A=A, hip=hip, torso=2, head=4, foot=40, kh=kh, W=W, ah=(-1, 0.2))
    elif has(var, "foot"):
        A = (math.sqrt(144.0 ** 2 - (hip_y + 9.0) ** 2), -9.0)
        start = dict(A=A, hip=seat_hip, torso=-2, head=0, foot=-70, kh=(0, -1), W=W, ah=(-1, 0.3))
        key = dict(A=A, hip=hip, torso=4, head=6, foot=-70, kh=(0, -1), W=W, ah=(-1, 0.2))
    else:
        A = (144.0, hip_y - 2.0)
        key = dict(A=A, hip=hip, torso=0, head=2, foot=-25, kh=(0, -1), W=W, ah=(-1, 0.2))
        if has(var, "straddle"):
            key["A2"] = (140.0, hip_y - 22.0)
            key["kh2"] = (0, -1)
            key["foot2"] = -25
            start["A2"] = (138.0, -12.0)
            start["kh2"] = (0, -1)
            start["foot2"] = -70
    key2 = dict(key, hip=(0.0, hip_y - 3), torso=-3, head=-1)
    if "A" in key and not has(var, "foot"):
        key2["A"] = (key["A"][0], key["A"][1] - 3)
    if has(var, "tuck"):
        key2["A"] = (key["A"][0], key["A"][1] - 3)
    scene = _parallettes(h)
    front = None
    if has(var, "straddle"):
        front = top_view_inset("hip", 38)
    if bench:
        scene = X.box(-26, -h, 26, 0, X.BENCHC, 4)
    return spec([start, key, key2], None, scene, front, hilite=hil, hold=(700, 1100))


# ================================================================================================= HOLLOW / DRAGON FLAG
@pat("hollow", ("mat", ["hollow"], "abs"), ("bench", ["dragon"], "abs"))
def hollow(eq, var, hil):
    hil = hil or "abs"
    if has(var, "dragon"):
        return _dragon(hil)
    hipp = (0.0, -14.0)

    def pose(t, leg_deg, arm=True):
        S = padd(hipp, vup(t, TOR))
        A = (hipp[0] + (LEG - 2) * math.cos(rad(leg_deg)), hipp[1] - (LEG - 2) * math.sin(rad(leg_deg)))
        u = (math.sin(rad(t)), -math.cos(rad(t)))
        W = (S[0] + u[0] * 94, S[1] + u[1] * 94)
        return dict(A=A, hip=hipp, torso=t, head=t - 2, foot=-10 - leg_deg, kh=(0, -1), W=W, ah=(0, -1))
    flat = pose(-90, 2)
    k1 = pose(-76, 18)
    k2 = pose(-70, 26)
    k3 = pose(-71, 24)
    return spec([flat, k1, k2, k3], None, X.mat(-230, 190, h=4), None, hilite=hil, lying=True, hold=(700, 1100))


def _dragon(hil):
    top = 40.0
    S = (0.0, -top - 14.0)

    def pose(e):
        u = (math.cos(rad(e)), -math.sin(rad(e)))
        hip = (S[0] + 92 * u[0], S[1] + 92 * u[1])
        A = (hip[0] + 144 * u[0], hip[1] + 144 * u[1])
        t = ang_up(hip, S)
        return dict(A=A, hip=hip, torso=t, head=-100, foot=foot_along(hip, A), kh=(0, -1),
                    W=(-60.0, -top - 8.0), ah=(0.2, -1))
    keys = [pose(84), pose(60), pose(36), pose(20)]
    keys.append(dict(pose(18), hip=(pose(18)["hip"][0], pose(18)["hip"][1] + 1.5)))
    scene = X.bench(-70.0, 100.0, top, thick=12, legs=(0.08, 0.5))
    return spec(keys, None, scene, None, hilite=hil, lying=True, hold=(600, 1000))


# ================================================================================================= SUPPORT HOLD (bars / rings)
def _bars(hand_y, x0=-70.0, x1=70.0):
    def fn(d, T, J, s):
        k = s * SS
        _rect(d, T, s, x0, hand_y, x1, hand_y + 8, X.METAL_D, 3)
        for x in (x0 + 6, x1 - 6):
            _rect(d, T, s, x - 4, hand_y + 6, x + 4, 0, X.METAL_D, 1.5)
            _rect(d, T, s, x - 20, -5, x + 20, 0, X.EQUIP, 2)
    return X.Item(fn, lambda J: [(x0 - 22, hand_y - 4), (x1 + 22, 0)])


def _rings(hand_y, top_y=-382.0):
    def back(d, T, J, s):
        k = s * SS
        _rect(d, T, s, -60, top_y - 4, 112, top_y + 5, X.BENCHC, 3)
        _rect(d, T, s, 96, top_y - 4, 108, 0, X.BENCHC, 1)
        _rect(d, T, s, 70, -5, 134, 0, X.EQUIP, 2)
        a, b = T((0, top_y)), T((0, hand_y))
        d.line([a, b], fill=(206, 170, 120), width=int(3.4 * k))
    return X.Item(back, lambda J: [(-62, top_y - 6), (136, 0)])


def _ring_front(hand_y):
    def fn(d, T, J, s):
        k = s * SS
        c = T((0, hand_y + 1))
        r = 9.5 * k
        d.ellipse([c[0] - r, c[1] - r, c[0] + r, c[1] + r], outline=X.METAL, width=int(2.6 * k))
    return X.Item(fn)


@pat("support_hold", ("none", ["bars"], "triceps"), ("none", ["rings"], "chest"))
def support_hold(eq, var, hil):
    rings = has(var, "rings")
    hil = hil or ("chest" if rings else "triceps")
    hy = -176.0
    wy = hy - 6.5 if not rings else hy - 1.0
    W = (0.0, wy)
    Sy = wy - 95.0
    hip = (0.0, Sy + TOR)
    stand = dict(A=(2.0, -6.0), hip=(2.0, -152.0), torso=0, head=0, foot=0, kh=(1, 0), W=W, ah=(-1, 0.4))
    A1, kh1, K1 = leg_fk((0.0, hip[1] + 6), 55, 140)
    tuckd = dict(A=A1, hip=(0.0, hip[1] + 6), torso=2, head=2, foot=30, kh=kh1, W=W, ah=(-1, 0.3))
    hold = dict(A=(22.0, hip[1] + 142.0), hip=hip, torso=-2, head=0, foot=45, kh=(1, 0), W=W, ah=(-1, 0.3))
    hold2 = dict(hold, hip=(0.0, hip[1] - 3), A=(24.0, hold["A"][1] - 3), torso=-4)
    scene = _rings(hy) if rings else _bars(hy)
    front = _ring_front(hy) if rings else None
    return spec([stand, tuckd, hold, hold2], None, scene, front, hilite=hil, hold=(700, 1100))


# ================================================================================================= STATIC HOLDS (grip / arm / landing)
STAND = dict(A=(0.0, -6.0), hip=(0.0, -151.0), torso=0, head=0, foot=0, kh=(1, 0))


def _plate_item(r=20.0):
    def fn(d, T, J, s):
        k = s * SS
        w = J["wrist"]
        c = T((w[0] + 2, w[1] + r + 1))
        rr = r * k
        d.ellipse([c[0] - rr, c[1] - rr, c[0] + rr, c[1] + rr], fill=X.RUBBER)
        r2 = rr * 0.62
        d.ellipse([c[0] - r2, c[1] - r2, c[0] + r2, c[1] + r2], fill=(84, 92, 114))
        r3 = rr * 0.16
        d.ellipse([c[0] - r3, c[1] - r3, c[0] + r3, c[1] + r3], fill=X.METAL)
    return X.Item(fn, lambda J: [(J["wrist"][0] - r - 4, J["wrist"][1] - 4), (J["wrist"][0] + r + 4, J["wrist"][1] + 2 * r + 6)])


def _gripper_item():
    def fn(d, T, J, s):
        k = s * SS
        w = J["wrist"]
        p = J["hand_pt"][0] - w[0] if "hand_pt" in J else 0.0
        piv = (w[0] + 1, w[1] + 18)
        spread = rad(8 + 30 * (1 - p))
        for sg in (-1, 1):
            tip = (piv[0] + sg * math.sin(spread) * 40, piv[1] - math.cos(spread) * 40)
            X.capsule(d, T(piv), T(tip), 4.4 * k, 4.4 * k, X.EQUIP if sg > 0 else X.METAL_D)
            X.capsule(d, T(padd(piv, (0, -0.0))), T((piv[0] + sg * math.sin(spread) * 22, piv[1] - math.cos(spread) * 22)), 5.4 * k, 5.4 * k, X.RUBBER)
        X.disc(d, T(piv), 6 * k, X.METAL)
    return X.Item(fn, lambda J: [padd(J["wrist"], (-30, -8)), padd(J["wrist"], (30, 30))])


def _axe_item():
    def fn(d, T, J, s):
        k = s * SS
        e, w = J["elbow"], J["wrist"]
        n = pdist(e, w) or 1
        u = ((w[0] - e[0]) / n, (w[1] - e[1]) / n)
        nx = (-u[1], u[0])
        a = padd(w, pmul(u, -3))
        b = padd(w, pmul(u, 40))
        X.capsule(d, T(a), T(b), 2.4 * k, 2.4 * k, X.METAL)
        for off, col in ((5, X.EQUIP), (38, X.EQUIP)):
            c = padd(w, pmul(u, off))
            X.capsule(d, T(padd(c, pmul(nx, -10))), T(padd(c, pmul(nx, 10))), 4.6 * k, 4.6 * k, col)
    return X.Item(fn, lambda J: [padd(J["wrist"], (-26, -26)), padd(J["wrist"], (48, 48))])


def _pulse_p(J):
    return J["hand_pt"][0] - J["wrist"][0] if "hand_pt" in J else 0.0


@pat("static_hold", ("none", ["plate"], "forearms"), ("none", ["gripper"], "forearms"), ("dumbbell", ["axe"], "forearms"),
     ("cable", ["pillars"], "chest"), ("none", ["landing"], "quads"))
def static_hold(eq, var, hil):
    if has(var, "pillars"):
        return _pillars(hil or "chest")
    if has(var, "landing"):
        return _landing(hil or "quads")
    if has(var, "axe"):
        hil = hil or "forearms"
        d0 = dict(STAND, W=(6.0, -150.0), ah=(0.2, 1))
        d1 = dict(STAND, W=(50.0, -199.0), ah=(0.1, 1))
        d2 = dict(d1, hand=(1.0, 0.0), W=(51.0, -200.0))
        d0["hand"] = (0.0, 0.0)
        d1["hand"] = (0.4, 0.0)
        return spec([d0, d1, d2], _axe_item(), None, pulse(lambda J: J["wrist"], 18), hilite=hil, hold=(600, 1200))
    if has(var, "gripper"):
        hil = hil or "forearms"
        o = dict(STAND, W=(50.0, -196.0), ah=(0, 1), hand=(0.0, 0.0))
        c = dict(o, hand=(1.0, 0.0))
        return spec([o, c, dict(c)], _gripper_item(), None, pulse(lambda J: J["wrist"], 18), hilite=hil, hold=(500, 1000))
    # plate pinch: lift a plate from the floor by pinching its edge, then stand and hold
    hil = hil or "forearms"
    pick = dict(A=(0.0, -6.0), hip=(-56.0, -96.0), torso=72, head=60, foot=0, kh=(1, 0), W=(35.0, -42.0), ah=(0.3, 1),
                hand=(0.0, 0.0))
    mid = dict(A=(0.0, -6.0), hip=(-32.0, -128.0), torso=40, head=30, foot=0, kh=(1, 0), W=(22.0, -86.0), ah=(0.3, 1),
               hand=(0.3, 0.0))
    stand = dict(STAND, W=(4.0, -150.0), ah=(0.2, 1), hand=(0.6, 0.0))
    stand2 = dict(stand, hand=(1.0, 0.0), W=(5.0, -151.0))
    return spec([pick, mid, stand, stand2], _plate_item(), None, pulse(lambda J: J["wrist"], 17), hilite=hil, hold=(700, 1200))


def _pillars(hil):
    towers = X.many(X.cable_tower(165, -300, side=1, w=24, stack_h=96), X.cable_tower(-165, -300, side=-1, w=24, stack_h=96))
    cables = X.many(X.cable_line((165, -300), anchor="wR", handle="d"), X.cable_line((-165, -300), anchor="wL", handle="d"))
    base = dict(H=(0, -152), lR=(0, 0), lL=(0, 0))
    k0 = dict(base, aR=(18, 8), aL=(-18, -8))
    k1 = dict(base, aR=(58, 40), aL=(-58, -40), lean=3, head=3)
    k2 = dict(base, aR=(84, 80), aL=(-84, -80), lean=4, head=2)
    k3 = dict(base, aR=(88, 86), aL=(-88, -86), lean=5, head=2)
    return spec([k0, k1, k2, k3], cables, towers, None, hilite=hil, view_kind="front", hold=(600, 1200))


def _landing(hil):
    far = dict(kh2=(1, 0.2), foot2=-20)
    stand = dict(STAND, A2=(-52.0, -92.0), W=(8.0, -150.0), ah=(0.1, 1), **far)
    air = dict(STAND, A=(0.0, -36.0), hip=(0.0, -181.0), A2=(-58.0, -118.0), W=(18.0, -214.0), ah=(0.1, 1), **far)
    land = dict(A=(0.0, -6.0), hip=(-16.0, -118.0), torso=20, head=8, foot=0, kh=(1, 0), A2=(-64.0, -66.0), kh2=(1, 0.2),
                foot2=-20, W=(72.0, -186.0), ah=(0.2, 1))
    land2 = dict(land, hip=(-17.0, -113.0), torso=22)
    return spec([stand, air, land, land2], None, None, None, hilite=hil, hold=(600, 1200))


# ================================================================================================= FLOOR CORE
def _pad_item():
    def fn(d, T, J, s):
        k = s * SS
        t = J["toe"]
        _rect(d, T, s, t[0] - 11, -4, t[0] + 11, 0, X.ACCENT, 2)
    return X.Item(fn, lambda J: [(J["toe"][0] - 12, -5), (J["toe"][0] + 12, 0)])


def _pelvic_pulse():
    return pulse(lambda J: padd(J["hip"], (4, -2)), 20)


@pat("floor_core", ("none", ["toe_tap"], "abs"), ("none", ["rollover"], "abs"), ("none", ["sit_out"], "obliques"),
     ("none", ["knee_slide"], "obliques"), ("none", ["pelvic"], "glutes"))
def floor_core(eq, var, hil):
    mat_ = X.mat(-230, 190, h=4)
    if has(var, "pelvic"):
        hil = hil or "glutes"
        hip = (0.0, -14.0)

        def pose(lift, p, t=-90):
            h = (0.0, -14.0 - lift)
            S = padd(h, vup(t, TOR))
            return dict(A=(76.0, -9.0), hip=h, torso=t, head=t - 3, foot=-70, kh=(0, -1), W=(S[0] + 92, -8.0), ah=(0, -1),
                        hand=(p, 0.0))
        return spec([pose(0, 0.0), pose(4, 0.7, -89), pose(6, 1.0, -88), pose(5, 0.6, -88)], None, mat_, _pelvic_pulse(),
                    hilite=hil, lying=True, hold=(700, 1300))
    if has(var, "toe_tap"):
        hil = hil or "abs"
        hip = (0.0, -14.0)
        t = -82
        S = padd(hip, vup(t, TOR))
        up = leg_fk(hip, 270, 0)[0]
        tap = (116.0, -9.0)
        base = dict(hip=hip, torso=t, head=-76, W=(S[0] + 88, -8.0), ah=(0, -1), kh=(0, -1), kh2=(0, -1), foot=-80, foot2=-80)
        both = dict(base, A=up, A2=(up[0] - 1, up[1] - 1))
        n_tap = dict(base, A=tap, A2=both["A2"], foot=-70)
        f_tap = dict(base, A=both["A"], A2=(tap[0] - 3, tap[1]), foot2=-70)
        return spec([both, n_tap, both, f_tap], None, mat_, None, hilite=hil, lying=True, loop="cycle", steps=5)
    if has(var, "rollover"):
        hil = hil or "abs"
        hip = (0.0, -14.0)
        # V-sit
        tV = -30
        SV = padd(hip, vup(tV, TOR))
        AV = (hip[0] + (LEG - 2) * math.cos(rad(42)), hip[1] - (LEG - 2) * math.sin(rad(42)))
        uV = (math.cos(rad(42)), -math.sin(rad(42)))
        vs = dict(A=AV, hip=hip, torso=tV, head=-26, foot=-30, kh=(0, -1), W=(SV[0] + uV[0] * 90, SV[1] + uV[1] * 90), ah=(0, -1))
        # lying with the legs vertical
        tL = -90
        SL = padd(hip, vup(tL, TOR))
        lg = dict(A=(0.0, hip[1] - (LEG - 2)), hip=hip, torso=tL, head=-92, foot=-90, kh=(1, 0), W=(SL[0] + 88, -8.0), ah=(0, -1))
        # plough: hips up, feet past the head
        S3 = (-30.0, -20.0)
        hip3 = (S3[0] + 22.0, S3[1] - 88.0)
        t3 = ang_up(hip3, S3)
        A3 = (hip3[0] - 104.0, -9.0)
        pl = dict(A=A3, hip=hip3, torso=t3, head=-100, foot=-30, kh=(0, -1), W=(S3[0] + 84, -8.0), ah=(0, -1))
        return spec([vs, lg, pl], None, mat_, None, hilite=hil, lying=True, hold=(700, 800))
    if has(var, "sit_out"):
        hil = hil or "obliques"
        # high bear position
        S0 = (0.0, -101.0)
        hip0 = psub(S0, vup(84, TOR))
        A0, kh0, K0 = leg_fk(hip0, 92, 176)
        bear = dict(A=A0, hip=hip0, torso=84, head=96, foot=60, kh=kh0, W=(0.0, HAND_Y), ah=(-1, 0))
        S1 = (22.0, -103.0)
        hip1 = psub(S1, vup(62, TOR))
        hip1 = (-52.0, -66.0)
        S1 = padd(hip1, vup(58, TOR))
        mid = dict(A=(60.0, -12.0), hip=hip1, torso=58, head=66, foot=-70, kh=(0, -1), W=(0.0, HAND_Y), ah=(-1, 0),
                   A2=(-80.0, -12.0), kh2=(0.2, -1), foot2=40)
        hip2 = (-24.0, -14.0)
        S2 = padd(hip2, vup(-24, TOR))
        sit = dict(A=(122.0, -9.0), hip=hip2, torso=-24, head=-18, foot=-70, kh=(0, -1), W=(S2[0] - 22, HAND_Y), ah=(-1, 0.2),
                   A2=(30.0, -9.0), kh2=(0.2, -1), foot2=-70, W2=(S2[0] + 64, S2[1] + 8), ah2=(0, 1))
        sit["W"] = (hip2[0] - 40, HAND_Y)
        bear["A2"], bear["kh2"], bear["foot2"] = (A0[0] - 6, A0[1]), kh0, 60
        mid["W2"], mid["ah2"] = (S1[0] + 40, S1[1] + 60), (0, 1)
        bear["W2"], bear["ah2"] = (0.0, HAND_Y), (-1, 0)
        return spec([bear, mid, sit], None, mat_, None, hilite=hil, hands_floor=True, hold=(600, 1000))
    # knee slide (plank on sliders, knee drives towards the chest)
    from .patterns_b import _plank_kw
    hil = hil or "obliques"
    plank = _plank_kw(110, True)
    plank["A"] = (plank["A"][0], -25.0)
    hip = plank["hip"]
    tuck = dict(plank, A=(hip[0] + 6.0, -25.0), kh=(1, -0.5))
    tuck["foot"] = 60
    pad_ = X.many(mat_, _pad_item())
    return spec([plank, tuck], None, pad_, None, hilite=hil, hands_floor=True, hold=(500, 700))


# ================================================================================================= DUMBBELL HANG POWER CLEAN
@pat("power_clean", ("dumbbell", [], "glutes"))
def power_clean(eq, var, hil):
    hil = hil or "glutes"
    hang = dict(A=(0.0, -6.0), hip=(-52.0, -112.0), torso=62, head=52, foot=0, kh=(1, 0), W=(31.0, -64.0), ah=(0.3, 1))
    pull = dict(A=(3.0, -24.0), hip=(0.0, -168.0), torso=0, head=-2, foot=60, kh=(1, 0), W=(16.0, -234.0), ah=(0.6, -1))
    catch = dict(A=(0.0, -6.0), hip=(-14.0, -126.0), torso=10, head=6, foot=0, kh=(1, 0), W=(28.0, -218.0), ah=(0.5, 1))
    return spec([hang, pull, catch], X.dumbbell_end("wrist", 10), None, None, hilite=hil, loop="cycle", steps=7)
