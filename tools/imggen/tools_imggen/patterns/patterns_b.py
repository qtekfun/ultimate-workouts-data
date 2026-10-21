"""Pull / core / full-body-cardio / mobility movement patterns.

PATTERNS = {pattern_id: fn(equipment, variants, hilite) -> spec}.  See extras_b.py for the pose conventions.
spec keys: keys (list of key poses = mk() kwargs; first = start pose), pose_a / pose_b (engine-style angle poses derived
from the first two distinct key poses), rotation (always 0: poses are absolute), equipment (mid layer), scene (back
layer), front (front layer), hilite, lying, hands_floor, loop ('pingpong' | 'cycle'), linear, hold.
Render with extras_b.render_spec(spec).
"""
import math
try:
    from . import extras_b as X
except ImportError:  # pragma: no cover
    import extras_b as X

mk = X.mk
PATTERNS = {}
TEST_VARIANTS = {}  # pattern -> [(equipment, variants, hilite)] rows rendered by run_b.py


def pat(name, *tests):
    def deco(fn):
        PATTERNS[name] = fn
        TEST_VARIANTS[name] = list(tests) or [("none", [], None)]
        return fn
    return deco


def make_spec(keys, equipment=None, scene=None, front=None, hilite=None, lying=False, hands_floor=False, **kw):
    if kw.get("view_kind") == "front":
        A = B = None  # front-view figure: not expressible as an engine (side-view) pose
    else:
        A = X.to_engine_pose(mk(**keys[0]))
        B = X.to_engine_pose(mk(**keys[1 if len(keys) == 2 else len(keys) // 2]))
    s = dict(keys=keys, pose_a=A, pose_b=B, rotation=0.0, equipment=equipment, scene=scene, front=front,
             hilite=hilite, lying=lying, hands_floor=hands_floor)
    s.update(kw)
    return s


def shoulder_of(kw):
    return mk(**kw)["shoulder"]


def hip_of(kw):
    return mk(**kw)["hip"]


def hip_from_shoulder(S, torso):
    return (S[0] - math.sin(math.radians(torso)) * 92, S[1] + math.cos(math.radians(torso)) * 92)


def pt_on_torso(kw, frac, off):
    J = mk(**kw)
    h, s = J["hip"], J["shoulder"]
    n = (math.cos(math.radians(kw.get("torso", 0))), math.sin(math.radians(kw.get("torso", 0))))
    return (h[0] + (s[0] - h[0]) * frac + n[0] * off, h[1] + (s[1] - h[1]) * frac + n[1] * off)


def torso_frame(kw):
    t = math.radians(kw.get("torso", 0))
    return (math.sin(t), -math.cos(t)), (math.cos(t), math.sin(t))


def cross_arms(kw, kw_extra=None):
    """Arms folded on the chest (foreshortened, drawn on the near side)."""
    S = shoulder_of(kw)
    d, n = torso_frame(kw)
    kw = dict(kw)
    kw["E"] = (S[0] - d[0] * 34 + n[0] * 14, S[1] - d[1] * 34 + n[1] * 14)
    kw["W"] = (S[0] - d[0] * 10 + n[0] * 14, S[1] - d[1] * 10 + n[1] * 14)
    return kw


def has(var, *tags):
    return any(t in var for t in tags)


def hand_item(eq, var, anchor="wrist", grip="side"):
    """Held-equipment drawing for free weights.  grip: 'side' (lengthwise dumbbell) | 'end' (end-on dumbbell)."""
    if eq == "dumbbell":
        return X.dumbbell_end(anchor) if grip == "end" else X.dumbbell(anchor)
    if eq == "kettlebell":
        return X.kettlebell(anchor, "down")
    if eq == "sz_bar":
        return X.barbell(anchor, half=44, plate=15)
    return X.barbell(anchor)


# =================================================================================================== BENT ROW
@pat("bent_row", ("barbell", [], "back"), ("dumbbell", ["single_arm"], "lats"), ("cable", [], "back"),
     ("band", [], "back"), ("machine", [], "back"), ("barbell", ["reverse"], "lats"), ("barbell", ["wide"], "back"))
def bent_row(eq, var, hil):
    hil = hil or "back"
    if eq == "dumbbell" and has(var, "single_arm"):
        return _one_arm_row(eq, var, hil)
    base = dict(A=(0, -6), shin=12, thigh=-30, torso=65, head=50)
    S = shoulder_of(base)
    frac, off = (0.45, 19) if has(var, "reverse", "narrow") else (0.82, 20) if has(var, "wide") else (0.58, 19)
    end_w = pt_on_torso(base, frac, off)
    ah = (-0.25, -1) if has(var, "wide") else (-1, -0.25)
    a = dict(base, W=(S[0] + 2, S[1] + 93), ah=(-1, 0.3))
    b = dict(base, W=end_w, ah=ah)
    scene, equip = None, None
    if eq == "cable":
        pul = (190, -52)
        scene = X.cable_tower(190 + 14, -52, side=1, w=26)
        scene = X.many(scene, X.cable_line(pul, handle="bar" if not has(var, "single_arm") else "d"))
        equip = None
        scene, equip = X.cable_tower(190 + 14, -52, side=1, w=26), X.cable_line(pul, handle="bar")
    elif eq == "band":
        equip = X.band_line((4, -3), post=False)
    elif eq == "machine":  # T-bar row: bar pivots on the floor behind the lifter, plates at the pivot end
        scene = X.tbar_scene(pivot=(-120, -9))
        equip = X.tbar_handle(pivot=(-120, -9))
    else:
        equip = hand_item(eq, var)
    return make_spec([a, b], equip, scene, hilite=hil)


def _one_arm_row(eq, var, hil):
    top = 60
    hip = (-25, -130)
    base = dict(A=(-5, -6), hip=hip, torso=75, head=62, W2=None, FL=(-36.6, -90), foot2=-80, kh=(1, 0))
    S = mk(**base)["shoulder"]
    base["W2"] = (S[0] + 2, -top - 6.5)
    base["ah2"] = (0.3, 1)
    a = dict(base, W=(S[0] + 3, S[1] + 93), ah=(-1, 0.3))
    endw = pt_on_torso(base, 0.55, 20)
    b = dict(base, W=endw, ah=(-1, -0.4))
    scene = X.bench(-150, 92, top, thick=12, legs=(0.1, 0.9))
    return make_spec([a, b], X.dumbbell("wrist"), scene, hilite=hil)


# =================================================================================================== SEATED ROW
@pat("seated_row", ("cable", [], "back"), ("machine", [], "back"), ("band", [], "back"),
     ("cable", ["wide"], "back"), ("cable", ["reverse", "narrow"], "lats"))
def seated_row(eq, var, hil):
    hil = hil or "back"
    handle = "vbar" if has(var, "wide") else "bar" if has(var, "reverse") else "d" if has(var, "single_arm") else "vgrip"
    if eq == "band":
        return _band_row_floor(var, hil)
    seat_top = 46
    hip = (0, -seat_top - 12)
    ank = (128, -34)
    base = dict(A=ank, hip=hip, foot=-72, kh=(0, -1))
    a = dict(base, torso=10, head=8)
    b = dict(base, torso=-8, head=-4)
    Sa, Sb = shoulder_of(a), shoulder_of(b)
    a["W"] = (Sa[0] + 90, Sa[1] + 30)
    a["ah"] = (0, 1)
    b["W"] = (Sb[0] + 28, Sb[1] + 40)
    b["ah"] = (-1, 0.2)
    pul = (172, -112)
    seat = X.many(X.box(-22, -seat_top, 30, -seat_top + 12, X.BENCHC, 5), X.post_rect(-4, -seat_top + 12, 4, 0),
                  X.box(140, -64, 152, -4, X.BENCHC, 3))
    if eq == "machine":
        pivot = (118, -150)
        scene = X.many(seat, X.pad((30, -150), (30, -106), r=8))
        equip = X.lever_arm(pivot, handle="bar")
        return make_spec([a, b], equip, scene, hilite=hil)
    scene = X.many(seat, X.cable_tower(186, -112, side=1, w=26))
    equip = X.cable_line(pul, handle=handle)
    return make_spec([a, b], equip, scene, hilite=hil)


def _band_row_floor(var, hil):
    hip = (0, -14)
    ank = (150, -22)
    base = dict(A=ank, hip=hip, foot=-88, kh=(0, -1))
    a = dict(base, torso=12, head=10)
    b = dict(base, torso=-6, head=-3)
    Sa, Sb = shoulder_of(a), shoulder_of(b)
    a["W"] = (Sa[0] + 90, Sa[1] + 40)
    a["ah"] = (0, 1)
    b["W"] = (Sb[0] + 28, Sb[1] + 42)
    b["ah"] = (-1, 0.2)
    equip = X.band_line(lambda J: (J["toe"][0] - 2, J["toe"][1] - 6), post=False)
    return make_spec([a, b], equip, X.mat(-60, 190), hilite=hil)


# =================================================================================================== PULLDOWN
@pat("pulldown", ("cable", [], "lats"), ("cable", ["narrow"], "lats"), ("machine", ["reverse"], "lats"),
     ("band", [], "lats"))
def pulldown(eq, var, hil):
    hil = hil or "lats"
    seat_top = 46
    hip = (0, -seat_top - 12)
    base = dict(A=(70, -6), hip=hip, foot=0, kh=(1, 0))
    a = dict(base, torso=-4, head=0)
    b = dict(base, torso=-16, head=-6)
    Sa, Sb = shoulder_of(a), shoulder_of(b)
    a["W"] = (Sa[0] + 10, Sa[1] - 92)
    a["ah"] = (1, 0)
    b["W"] = (Sb[0] + 30, Sb[1] + 10)
    b["ah"] = (-0.5, 1)
    handle = "vgrip" if has(var, "narrow") else "bar" if has(var, "reverse") else "vbar"
    pul = (Sa[0] + 10, -300)
    thigh_pad = X.thigh_pad()
    seat = X.many(X.box(-24, -seat_top, 30, -seat_top + 12, X.BENCHC, 5), X.post_rect(-4, -seat_top + 12, 4, 0))
    if eq == "band":
        eqp = X.band_line((Sa[0] + 10, -312), post=True)
        return make_spec([a, b], eqp, seat, thigh_pad, hilite=hil)
    scene = X.many(seat, X.cable_tower(120, -300, side=1, w=26, beam_to=pul[0]))
    eqp = X.cable_line(pul, handle=handle)
    return make_spec([a, b], eqp, scene, thigh_pad, hilite=hil)


# =================================================================================================== PULL-UP
@pat("pullup", ("bar", [], "lats"), ("bar", ["reverse"], "biceps"), ("machine", [], "lats"), ("band", [], "lats"))
def pullup(eq, var, hil):
    hil = hil or "lats"
    bar_y = -362
    xb = 8
    legs = (-45, 108)
    # hanging
    Sa = (xb - 2, bar_y + 96)
    Sb = (xb - 30, bar_y + 6)
    ta, tb = 0, -12
    def body(S, t, head, kneeraise):
        hip = hip_from_shoulder(S, t)
        lx = -42 - kneeraise * 0
        return dict(A=(hip[0] + lx, hip[1] + 112), hip=hip, torso=t, head=head, kh=(1, 0), foot=40,
                    W=(xb, bar_y), ah=(0.3, 1))
    a = body(Sa, ta, 6, 0)
    b = body(Sb, tb, 16, 0)
    if eq == "machine":  # assisted: knees on the pad, counterweight platform
        pass
    scene = X.pullup_frame(xb, bar_y)
    equip = None
    if eq == "band":
        equip = X.band_line((xb + 6, bar_y), to="ankle", post=False)
    return make_spec([a, b], equip, scene, hilite=hil)


# =================================================================================================== UPRIGHT ROW
@pat("upright_row", ("barbell", [], "shoulders"), ("dumbbell", [], "traps"), ("cable", [], "shoulders"),
     ("band", [], "shoulders"), ("sz_bar", [], "shoulders"))
def upright_row(eq, var, hil):
    hil = hil or "shoulders"
    base = dict(A=(0, -6), torso=0, head=0)
    S = shoulder_of(base)
    a = dict(base, E=(S[0] + 10, S[1] + 48), W=(S[0] + 20, S[1] + 93))
    b = dict(base, E=(S[0] + 20, S[1] - 4), W=(S[0] + 26, S[1] + 36))
    scene, equip = None, None
    if eq == "cable":
        scene = X.cable_tower(150, -22, side=1, w=26, stack_h=70)
        equip = X.cable_line((150, -22), handle="bar")
    elif eq == "band":
        equip = X.band_line((4, -3), post=False)
    else:
        equip = hand_item(eq, var)
    return make_spec([a, b], equip, scene, hilite=hil)


# =================================================================================================== SHRUG
@pat("shrug", ("dumbbell", [], "traps"), ("barbell", [], "traps"), ("cable", [], "traps"), ("band", [], "traps"))
def shrug(eq, var, hil):
    hil = hil or "traps"
    base = dict(A=(0, -6), torso=0, head=0)
    S = shoulder_of(base)
    front = eq in ("barbell", "cable", "sz_bar", "machine")
    dx = 17 if front else 4
    ua = 10 if front else 3
    a = dict(base, sh_up=0, uarm=ua, farm=ua)
    b = dict(base, sh_up=15, uarm=ua, farm=ua)
    scene, equip = None, None
    if eq == "cable":
        scene = X.cable_tower(150, -22, side=1, w=26, stack_h=70)
        equip = X.cable_line((150, -22), handle="bar")
    elif eq == "band":
        equip = X.band_line((4, -3), post=False)
    elif eq == "dumbbell":
        equip = X.dumbbell("wrist")
    else:
        equip = hand_item(eq, var)
    return make_spec([a, b], equip, scene, hilite=hil)


# =================================================================================================== CURLS
def _curl(eq, var, hil, hammer):
    hil = hil or "biceps"
    end_f = 140 if hammer else 155
    seated = has(var, "seated")
    incline = has(var, "incline")
    preacher = eq == "machine" or has(var, "preacher")
    scene, equip = None, None
    if preacher:
        hip = (0, -58)
        base = dict(A=(66, -6), hip=hip, torso=8, head=14, kh=(1, 0))
        S = shoulder_of(base)
        ua = 42
        E = X.add(S, X.vdown(ua, 50))
        a = dict(base, uarm=ua, farm=22)
        b = dict(base, uarm=ua, farm=end_f - 8)
        n = (-math.cos(math.radians(ua - 90)) * 0 + (-math.cos(math.radians(ua))), math.sin(math.radians(ua)))
        d_ = X.vdown(ua)
        perp = (-d_[1], d_[0])
        if perp[1] < 0:
            perp = (-perp[0], -perp[1])
        off = (perp[0] * 15, perp[1] * 15)
        p0 = (S[0] + off[0] - d_[0] * 6, S[1] + off[1] - d_[1] * 6)
        p1 = (E[0] + off[0] + d_[0] * 14, E[1] + off[1] + d_[1] * 14)
        scene = X.many(X.box(-24, -46, 30, -34, X.BENCHC, 5), X.post_rect(-4, -34, 4, 0), X.pad(p0, p1, r=7),
                       X.post_rect(p1[0] - 3, p1[1] + 6, p1[0] + 3, 0))
        equip = X.dumbbell("wrist") if eq in ("dumbbell",) else (X.barbell("wrist", half=44, plate=15)
                                                                 if eq in ("barbell", "sz_bar", "machine") else X.dumbbell("wrist"))
        if hammer:
            equip = X.dumbbell("wrist")
        return make_spec([a, b], equip, scene, hilite=hil)
    if incline:
        hip = (0, -58)
        base = dict(A=(66, -6), hip=hip, torso=-38, head=-30, kh=(1, 0))
        a = dict(base, uarm=2, farm=0)
        b = dict(base, uarm=2, farm=end_f)
        tor = -38
        dirv = (math.sin(math.radians(tor)), -math.cos(math.radians(tor)))
        nb = (-math.cos(math.radians(tor)), -math.sin(math.radians(tor)))  # behind the back
        p0 = (hip[0] + nb[0] * 21 - dirv[0] * 6, hip[1] + nb[1] * 21 - dirv[1] * 6)
        p1 = (hip[0] + nb[0] * 21 + dirv[0] * 110, hip[1] + nb[1] * 21 + dirv[1] * 110)
        scene = X.many(X.box(-24, -46, 30, -34, X.BENCHC, 5), X.post_rect(-4, -34, 4, 0), X.pad(p0, p1, r=8),
                       X.post_rect(p0[0] - 3, p0[1] + 6, p0[0] + 3, 0, ), X.post_rect(p1[0] - 12, p1[1], p1[0] - 6, 0))
    elif seated:
        base = dict(A=(66, -6), hip=(0, -58), torso=0, head=0, kh=(1, 0))
        a = dict(base, uarm=3, farm=0)
        b = dict(base, uarm=3, farm=end_f)
        scene = X.many(X.box(-24, -46, 30, -34, X.BENCHC, 5), X.post_rect(-4, -34, 4, 0),
                       X.post_rect(-18, -34, -10, 0))
    else:
        base = dict(A=(0, -6), torso=0, head=0)
        a = dict(base, uarm=4, farm=0)
        b = dict(base, uarm=4, farm=end_f)
    if eq == "cable":
        px = 150
        scene = X.many(scene, X.cable_tower(px, -22, side=1, w=26, stack_h=70)) if scene else X.cable_tower(px, -22, side=1, w=26, stack_h=70)
        equip = X.cable_line((px, -22), handle="rope" if hammer else "bar")
    elif eq == "band":
        equip = X.band_line((4, -3) if not (seated or incline) else (60, -3), post=False)
    elif eq in ("barbell", "sz_bar"):
        equip = X.barbell("wrist", half=44, plate=15) if eq == "sz_bar" else X.barbell("wrist")
        if has(var, "reverse"):
            equip = X.barbell("wrist", half=44, plate=15)
    elif eq == "kettlebell":
        equip = X.kettlebell("wrist", "down")
    else:
        equip = X.dumbbell("wrist") if hammer else X.dumbbell_end("wrist")
    return make_spec([a, b], equip, scene, hilite=hil)


@pat("curl", ("dumbbell", [], "biceps"), ("barbell", [], "biceps"), ("sz_bar", ["reverse"], "forearms"),
     ("cable", [], "biceps"), ("band", [], "biceps"), ("dumbbell", ["incline"], "biceps"),
     ("machine", [], "biceps"), ("dumbbell", ["seated"], "biceps"))
def curl(eq, var, hil):
    return _curl(eq, var, hil, False)


@pat("hammer_curl", ("dumbbell", [], "biceps"), ("cable", [], "forearms"), ("dumbbell", ["seated"], "biceps"),
     ("band", [], "biceps"))
def hammer_curl(eq, var, hil):
    return _curl(eq, var, hil, True)


# =================================================================================================== FACE PULL
@pat("face_pull", ("cable", [], "shoulders"), ("band", [], "shoulders"), ("cable", ["seated"], "traps"))
def face_pull(eq, var, hil):
    hil = hil or "shoulders"
    seated = has(var, "seated")
    if seated:
        base = dict(A=(70, -6), hip=(0, -58), torso=0, head=0, kh=(1, 0))
        pul_y = -190
        seat = X.many(X.box(-24, -46, 30, -34, X.BENCHC, 5), X.post_rect(-4, -34, 4, 0))
    else:
        base = dict(A=(0, -6), torso=-4, head=-4)
        pul_y = -268
        seat = None
    S = shoulder_of(base)
    H = mk(**base)["head"]
    px = 170
    a = dict(base, E=(S[0] + 48, S[1] + 4), W=(S[0] + 92, S[1] + (pul_y - S[1]) * 0.15))
    b = dict(base, E=(S[0] + 10, S[1] - 4), W=(S[0] + 30, S[1] - 34))
    pul = (px, pul_y)
    if eq == "band":
        equip = X.band_line(pul, post=True)
        scene = seat
    else:
        scene = X.cable_tower(px + 12, pul_y, side=1, w=26)
        if seat:
            scene = X.many(seat, scene)
        equip = X.cable_line(pul, handle="rope")
    return make_spec([a, b], equip, scene, hilite=hil)


# =================================================================================================== WRIST CURL
@pat("wrist_curl", ("dumbbell", [], "forearms"), ("barbell", [], "forearms"), ("dumbbell", ["reverse"], "forearms"))
def wrist_curl(eq, var, hil):
    hil = hil or "forearms"
    hip = (0, -58)
    base = dict(A=(70, -6), hip=hip, torso=45, head=34, kh=(1, 0))
    J = mk(**base)
    h, k = J["hip"], J["knee"]
    dx, dy = k[0] - h[0], k[1] - h[1]
    n = math.hypot(dx, dy)
    ux, uy = dx / n, dy / n
    nx, ny = uy, -ux
    if ny > 0:
        nx, ny = -nx, -ny
    top = lambda f: (h[0] + dx * f + nx * (12 - 2.5 * f + 6.4), h[1] + dy * f + ny * (12 - 2.5 * f + 6.4))
    Eb = top(0.5)
    Wb = top(1.0)
    Wb = (Wb[0] + 6, Wb[1] - 2)
    kw = dict(base, E=Eb, W=Wb)
    if has(var, "reverse"):
        a = dict(kw, hand=(12, 10))
        b = dict(kw, hand=(8, -18))
    else:
        a = dict(kw, hand=(7, 17))
        b = dict(kw, hand=(15, -15))
    scene = X.many(X.box(-24, -46, 30, -34, X.BENCHC, 5), X.post_rect(-4, -34, 4, 0))
    heavy = X.barbell("hand_pt", half=40, plate=14) if eq in ("barbell", "sz_bar") else X.dumbbell_end("hand_pt")
    equip = X.many(X.fist(), heavy)
    return make_spec([a, b], equip, scene, hilite=hil)


# =================================================================================================== BACK EXTENSION
@pat("back_extension", ("machine", [], "back"), ("none", [], "back"), ("swiss_ball", [], "back"),
     ("dumbbell", [], "back"))
def back_extension(eq, var, hil):
    hil = hil or "back"
    if eq in ("none", "mat", "bodyweight") or has(var, "lying"):
        return _superman(var, hil)
    if eq == "swiss_ball":
        return _ball_extension(var, hil)
    hip = (0, -118)
    ank = (-100, -16)
    base = dict(A=ank, hip=hip, foot=0, kh=(1, 0))
    t_up, t_dn = 44, 118
    def chest_hand(t, hd):
        return cross_arms(dict(base, torso=t, head=hd))
    a = chest_hand(t_dn, t_dn - 8)
    b = chest_hand(t_up, t_up - 4)
    lx = math.cos(math.radians(45))
    # roman chair: pad under the pelvis, foot plate behind the heels
    p0 = (hip[0] + 4 + 8, hip[1] + 22)
    p1 = (hip[0] - 40, hip[1] + 58)
    scene = X.many(X.pad((hip[0] + 14, hip[1] + 18), (hip[0] - 18, hip[1] + 50), r=9),
                   X.pad((ank[0] - 12, ank[1] - 14), (ank[0] - 12 - 18, ank[1] + 14), r=6),
                   X.post_rect(hip[0] - 24, hip[1] + 40, hip[0] - 16, 0), X.post_rect(ank[0] - 36, ank[1] + 14, ank[0] - 28, 0),
                   X.post_rect(ank[0] - 40, -8, hip[0] - 16, 0, ))
    equip = X.dumbbell("wrist") if eq == "dumbbell" else None
    return make_spec([a, b], equip, scene, hilite=hil)


def _superman(var, hil):
    # prone on the mat, arms forward: lift chest, arms and legs
    base_h = (-4, -13)
    def pose(lift):
        t = 90 - lift  # torso direction: forward, rising
        hip = (0, -13 - lift * 0.15)
        leg_end = (-146 * math.cos(math.radians(lift * 0.5)), hip[1] + 146 * math.sin(math.radians(lift * 0.5)) * -1 + 0)
        kw = dict(A=(-143 + 0, -9 - lift * 0.9), hip=hip, torso=t, head=t - 6, foot=-100 if lift < 1 else -105, kh=(0, -1))
        S = shoulder_of(kw)
        kw["W"] = (S[0] + 94 * math.cos(math.radians(lift * 0.9)), S[1] - 94 * math.sin(math.radians(lift * 0.9)) * 0.9)
        kw["ah"] = (0, 1)
        return kw
    a = pose(0)
    b = pose(22)
    return make_spec([a, b], None, X.mat(-190, 130), hilite=hil, lying=True)


def _ball_extension(var, hil):
    r = 32
    cx, cy = 0, -r
    hip = (0, -2 * r + 6 - 12)
    ank = (-138, -24)
    base = dict(A=ank, hip=hip, foot=90, kh=(0, -1))
    a = dict(base, torso=118, head=112)
    b = dict(base, torso=70, head=64)
    a, b = cross_arms(a), cross_arms(b)
    ball = X.ball(cx, cy, r)
    return make_spec([a, b], None, ball, hilite=hil)


# =================================================================================================== helpers for core
def hands_head(kw):
    """Fingertips behind the head, elbows out (foreshortened)."""
    J = mk(**kw)
    H = J["head"]
    d, n = torso_frame(dict(kw, torso=kw.get("head", kw.get("torso", 0))))
    kw = dict(kw)
    kw["W"] = (H[0] - n[0] * 8 - d[0] * 4, H[1] - n[1] * 8 - d[1] * 4)
    kw["E"] = (H[0] - d[0] * 14 + n[0] * 16, H[1] - d[1] * 14 + n[1] * 16)
    return kw


def lying_base(hipx=0.0, raise_=0.0):
    return dict(hip=(hipx, -14 - raise_))


# =================================================================================================== CRUNCH
@pat("crunch", ("none", [], "abs"), ("swiss_ball", [], "abs"), ("none", ["decline"], "abs"), ("cable", [], "abs"),
     ("machine", [], "abs"), ("dumbbell", [], "abs"))
def crunch(eq, var, hil):
    hil = hil or "abs"
    if eq == "cable" or has(var, "kneeling"):
        return _cable_crunch(var, hil)
    if eq == "machine":
        return _machine_crunch(var, hil)
    ball = eq == "swiss_ball"
    decline = has(var, "decline")
    if ball:
        r = 30
        hip = (6, -74)
        base = dict(A=(88, -6), hip=hip, foot=0, kh=(0, -1))
        t0, t1 = -112, -62
    else:
        base = dict(A=(84, -6), hip=(0, -14), foot=0, kh=(0, -1))
        t0, t1 = -90, -64
    a = dict(base, torso=t0, head=t0 + 4)
    b = dict(base, torso=t1, head=t1 + 14)
    if eq == "dumbbell":
        a, b = cross_arms(a), cross_arms(b)
        for kw in (a, b):
            kw["hold"] = True
    else:
        a, b = hands_head(a), hands_head(b)
    scene = None
    if decline:
        th, pv = -22, (-170, 0)
        a, b = X.rotate_kw(a, th, pv), X.rotate_kw(b, th, pv)
        p0, p1 = X.rot_pt((-175, 8), th, pv), X.rot_pt((115, 8), th, pv)
        q0, q1 = X.rot_pt((-130, 12), th, pv), X.rot_pt((95, 12), th, pv)
        foot_roll = (X.rot_pt((70, -26), th, pv), X.rot_pt((92, -26), th, pv))
        scene = X.many(X.pad(p0, p1, r=8, col=X.BENCHC), X.post_rect(q0[0] - 3, q0[1], q0[0] + 3, 0),
                       X.post_rect(q1[0] - 3, q1[1], q1[0] + 3, 0), X.pad(foot_roll[0], foot_roll[1], r=6))
    elif ball:
        scene = X.ball(6, -30, 30)
    else:
        scene = X.mat(-200, 130)
    equip = X.dumbbell("wrist") if eq == "dumbbell" else None
    return make_spec([a, b], equip, scene, hilite=hil, lying=True)


def _cable_crunch(var, hil):
    base = dict(A=(-72, -8), shin=90, thigh=0, foot=180)
    a = dict(base, torso=2, head=2)
    b = dict(base, torso=62, head=72)
    for kw in (a, b):
        H = mk(**kw)["head"]
        kw["W"] = (H[0] + 14, H[1] - 6)
        kw["ah"] = (0, 1)
    scene = X.many(X.mat(-110, 60), X.cable_tower(170, -270, side=1, w=26, beam_to=130))
    equip = X.cable_line((130, -270), handle="rope")
    return make_spec([a, b], equip, scene, hilite=hil)


def _machine_crunch(var, hil):
    base = dict(A=(66, -6), hip=(0, -58), foot=0, kh=(1, 0))
    a = cross_arms(dict(base, torso=-4, head=-4))
    b = cross_arms(dict(base, torso=38, head=44))
    seat = X.many(X.box(-24, -46, 30, -34, X.BENCHC, 5), X.post_rect(-4, -34, 4, 0),
                  X.pad((-26, -66), (-28, -150), r=7), X.post_rect(-34, -150, -28, 0))
    return make_spec([a, b], X.torso_pad(0.55, 0.95, 21, r=8), seat, hilite=hil)


# =================================================================================================== LEG RAISE
@pat("leg_raise", ("none", [], "abs"), ("bench", [], "abs"), ("none", ["reverse"], "abs"), ("none", ["decline"], "abs"))
def leg_raise(eq, var, hil):
    hil = hil or "abs"
    top = 46 if eq == "bench" else 0
    hip = (0, -14 - top)
    S0 = (hip[0] - 92, hip[1])
    def pose(phi, torso=-90):
        ank = (hip[0] + 145.5 * math.cos(math.radians(phi)), hip[1] - 145.5 * math.sin(math.radians(phi)))
        kw = dict(A=ank, hip=hip, torso=torso, head=torso - 4, foot=-phi - 70)
        kw["E"] = (S0[0] + 48, S0[1] + 7 - top * 0 + (0 if not top else 0))
        kw["W"] = (S0[0] + 94, S0[1] + 7)
        kw["behind"] = True
        return kw
    if has(var, "reverse"):
        base = dict(hip=hip, torso=-90, head=-92, kh=(-1, -0.3), foot=-60)
        a = dict(base, A=(hip[0] + 72, hip[1] - 78))
        b = dict(base, hip=(hip[0] + 4, hip[1] - 20), A=(hip[0] + 50, hip[1] - 120), torso=-85, foot=-30)
        for kw in (a, b):
            S = X.add(kw["hip"], X.vup(kw["torso"], 92))
            kw["E"] = (S[0] + 48, S[1] + 7)
            kw["W"] = (S[0] + 94, S[1] + 7)
            kw["behind"] = True
        scene = X.mat(-200, 120)
        return make_spec([a, b], None, scene, hilite=hil, lying=True)
    a, b = pose(10), pose(88)
    if has(var, "decline"):
        th, pv = -18, (-170, 0)
        a, b = X.rotate_kw(a, th, pv), X.rotate_kw(b, th, pv)
        p0, p1 = X.rot_pt((-175, 8), th, pv), X.rot_pt((60, 8), th, pv)
        q0 = X.rot_pt((-130, 12), th, pv)
        q1 = X.rot_pt((40, 12), th, pv)
        scene = X.many(X.pad(p0, p1, r=8, col=X.BENCHC), X.post_rect(q0[0] - 3, q0[1], q0[0] + 3, 0),
                       X.post_rect(q1[0] - 3, q1[1], q1[0] + 3, 0))
        return make_spec([a, b], None, scene, hilite=hil, lying=True)
    if top:
        scene = X.bench(-220, 40, top, thick=12, legs=(0.1, 0.9))
    else:
        scene = X.mat(-200, 170)
    return make_spec([a, b], None, scene, hilite=hil, lying=True)


# =================================================================================================== HANGING KNEE RAISE
@pat("hanging_knee_raise", ("bar", [], "abs"), ("machine", [], "abs"), ("bar", ["straight"], "abs"))
def hanging_knee_raise(eq, var, hil):
    hil = hil or "abs"
    if eq == "machine":
        return _captain_chair(var, hil)
    bar_y, xb = -362, 8
    S = (xb - 2, bar_y + 96)
    def pose(t, ank_rel, kh=(1, 0)):
        hip = hip_from_shoulder(S, t)
        return dict(A=(hip[0] + ank_rel[0], hip[1] + ank_rel[1]), hip=hip, torso=t, head=t * 0.4, kh=kh,
                    W=(xb, bar_y), ah=(0.3, 1), foot=70)
    a = pose(0, (-6, 144.5))
    if has(var, "straight"):
        b = pose(-14, (92, -36), kh=(0.3, 1))
        b["foot"] = 20
    else:
        b = pose(-14, (28, 66), kh=(1, -0.2))
        b["foot"] = 60
    scene = X.pullup_frame(xb, bar_y)
    return make_spec([a, b], None, scene, hilite=hil)


def _captain_chair(var, hil):
    S = (0, -262)
    hipy = S[1] + 92
    base = dict(torso=0, head=0)
    def pose(ank_rel, kh=(1, 0), t=0):
        hip = (0, hipy)
        return dict(A=(hip[0] + ank_rel[0], hip[1] + ank_rel[1]), hip=hip, torso=t, head=t, kh=kh, foot=70,
                    E=(S[0] + 4, S[1] + 48), W=(S[0] + 50, S[1] + 52))
    a = pose((-4, 144.5))
    b = pose((30, 62), kh=(1, -0.2), t=-6)
    scene = X.many(X.pad((-22, -120), (-22, -285), r=7, col=(70, 78, 100)), X.post_rect(-34, -300, -26, 0),
                   X.box(-6, S[1] + 56, 36, S[1] + 70, (70, 78, 100), 5), X.post_rect(14, S[1] + 70, 22, 0),
                   X.box(-44, -6, 60, 0, X.EQUIP, 2))
    return make_spec([a, b], None, scene, hilite=hil)


# =================================================================================================== PLANK
def _plank_kw(sx, high, th_extra=0.0, ank_y=-22.0, rock=0.0, sy=None):
    Sy = sy if sy is not None else (-102.0 if high else -54.4)
    S = (sx + rock, Sy)
    sin_t = max(-0.9, min(0.9, (ank_y - Sy) / 237.0))
    th = math.degrees(math.asin(sin_t))
    u = (math.cos(math.radians(th)), -math.sin(math.radians(th)))
    hip = (S[0] - u[0] * 92, S[1] - u[1] * 92)
    A = (hip[0] - u[0] * 145, hip[1] - u[1] * 145)
    kw = dict(A=A, hip=hip, torso=90 - th, head=90 - th + 6, foot=64, kh=(0, -1))
    if high:
        kw["E"], kw["W"] = (S[0] + 3, S[1] + 48), (S[0], -6.5)
    else:
        kw["E"], kw["W"] = (S[0], -6.4), (S[0] + 46, -6.4)
    return kw


@pat("plank", ("none", [], "abs"), ("none", ["hands"], "abs"), ("none", ["reverse"], "glutes"),
     ("swiss_ball", [], "abs"))
def plank(eq, var, hil):
    hil = hil or "abs"
    if has(var, "reverse"):
        return _reverse_plank(hil)
    high = has(var, "hands", "pushup", "high", "straight_arm") or eq == "bench"
    a = _plank_kw(110, high)
    b = _plank_kw(110, high, rock=7)
    scene = X.mat(-140, 200, h=4)
    if eq == "swiss_ball":
        a = _plank_kw(110, False, sy=-112)
        b = _plank_kw(110, False, sy=-112, rock=7)
        for kw in (a, b):
            sx = kw["E"][0]
            kw["E"], kw["W"] = (sx, -66.4), (sx + 40, -64.4)
        scene = X.many(X.mat(-140, 200, h=4), X.ball(130, -32, 32))
    return make_spec([a, b], None, scene, hilite=hil, hands_floor=True)


def _reverse_plank(hil):
    # face up: head to the left, heels on the floor, straight arms behind
    def kw(dip):
        S = (-110.0, -100.0)
        ank_y = -9.0
        sin_t = (ank_y - S[1]) / 237.0
        th = math.degrees(math.asin(sin_t))
        u = (-math.cos(math.radians(th)), -math.sin(math.radians(th)))  # towards the head (left, up)
        hip = (S[0] - u[0] * 92, S[1] - u[1] * 92)
        A = (hip[0] - u[0] * 145, hip[1] - u[1] * 145)
        hip = (hip[0], hip[1] + dip)
        t = math.degrees(math.atan2(S[0] - hip[0], -(S[1] - hip[1])))
        return dict(A=A, hip=hip, torso=t, head=t - 14, foot=-70, kh=(0, -1),
                    E=(S[0] - 3, S[1] + 48), W=(S[0], -6.5))
    return make_spec([kw(0), kw(26)], None, X.mat(-200, 180, h=4), hilite=hil, hands_floor=True)


# =================================================================================================== SIDE PLANK (front view)
@pat("side_plank", ("none", [], "obliques"), ("none", ["forearm"], "obliques"))
def side_plank(eq, var, hil):
    hil = hil or "obliques"
    piv = (9, -6)
    def f(rot, lean):
        return dict(H=(0, -152), lean=lean, head=lean, rot=rot, pivot=piv, off=(-110, 0),
                    wR=lambda J: (J["SR"][0], -6.5), wL=lambda J: (J["SL"][0] + 2, J["SL"][1] - 92),
                    hR=(0, 1), hL=(0, -1), lR=(0, 0), lL=(0, 0))
    a = f(80, -32)    # hips dropped
    b = f(66, 0)      # straight line
    return make_spec([a, b], None, X.mat(-200, 200, h=4), hilite=hil, view_kind="front")


# =================================================================================================== RUSSIAN TWIST
@pat("russian_twist", ("none", [], "obliques"), ("dumbbell", [], "obliques"), ("kettlebell", [], "obliques"))
def russian_twist(eq, var, hil):
    hil = hil or "obliques"
    hip = (0, -14)
    legs = dict(A=(hip[0] + 140 * math.cos(math.radians(32)), hip[1] - 140 * math.sin(math.radians(32))),
                hip=hip, torso=-40, head=-38, foot=-70, kh=(0, -1))
    S = X.add(hip, X.vup(-40, 92))
    def pose(W, behind=False, hint=(0, 1)):
        return dict(legs, W=W, W2=(W[0] - 3, W[1] + 2), ah=hint, ah2=hint, behind=behind)
    near = pose((S[0] + 62, S[1] + 62), False, (-0.3, 1))
    center = pose((S[0] + 78, S[1] + 36), False)
    far = pose((S[0] + 62, S[1] + 58), True, (-0.3, 1))
    scene, equip = X.mat(-120, 150), None
    if eq in ("dumbbell", "kettlebell"):
        back, fr = X.held_pair("wrist", eq)
        scene = X.many(scene, back)
        equip = fr
    return make_spec([near, center, far, center], equip, scene, hilite=hil, lying=True, loop="cycle",
                     linear=False, steps=6)


# =================================================================================================== SIDE BEND (front view)
@pat("side_bend", ("dumbbell", [], "obliques"), ("none", [], "obliques"), ("cable", [], "obliques"))
def side_bend(eq, var, hil):
    hil = hil or "obliques"
    base = dict(H=(0, -152), lR=(0, 0), lL=(0, 0), aL=(-140, 30))
    a = dict(base, lean=0, aR=(1, 1))
    b = dict(base, lean=26, head=24, aR=(1, 1))
    if eq == "none":
        a["aR"] = b["aR"] = (140, -30)
        a["aL"] = b["aL"] = (-140, 30)
    equip, scene = None, None
    if eq == "dumbbell":
        equip = X.fx_dumbbell("wR", 0.9)
    elif eq == "cable":
        scene = X.cable_tower(170, -26, side=1, w=24, stack_h=70)
        equip = X.many(X.cable_line((170, -26), anchor="wR", handle="d"))
    return make_spec([a, b], equip, scene, hilite=hil, view_kind="front")


# =================================================================================================== MOUNTAIN CLIMBER
@pat("mountain_climber", ("none", [], "abs"))
def mountain_climber(eq, var, hil):
    hil = hil or "abs"
    base = _plank_kw(110, True)
    base["kh"] = (0.4, -1)
    hip = base["hip"]
    ext = base["A"]
    drive = (hip[0] + 22, hip[1] + 34)
    def pose(near_drive):
        kw = dict(base)
        if near_drive:
            kw["A"] = drive
            kw["kh"] = (0.4, -1)
            kw["foot"] = 70
            kw["A2"] = ext
            kw["kh2"] = (0.4, -1)
            kw["foot2"] = 64
        else:
            kw["A"] = ext
            kw["A2"] = drive
            kw["kh2"] = (0.4, -1)
            kw["foot2"] = 70
        kw["E2"] = (kw["E"][0] - 6, kw["E"][1])
        kw["W2"] = (kw["W"][0] - 8, kw["W"][1])
        return kw
    return make_spec([pose(False), pose(True)], None, X.mat(-140, 200, h=4), hilite=hil, hands_floor=True,
                     steps=6)


# =================================================================================================== BICYCLE CRUNCH
@pat("bicycle_crunch", ("none", [], "obliques"))
def bicycle_crunch(eq, var, hil):
    hil = hil or "obliques"
    hip = (0, -14)
    base = dict(hip=hip, torso=-62, head=-48, foot=-60, kh=(0, -1), kh2=(0, -1))
    ext = (hip[0] + 144 * math.cos(math.radians(16)), hip[1] - 144 * math.sin(math.radians(16)))
    tuck = (hip[0] + 58, hip[1] - 72)
    def pose(near_ext):
        kw = dict(base)
        if near_ext:
            kw["A"], kw["A2"] = ext, tuck
            kw["kh"], kw["kh2"] = (0, -1), (-1, -0.6)
        else:
            kw["A"], kw["A2"] = tuck, ext
            kw["kh"], kw["kh2"] = (-1, -0.6), (0, -1)
        kw["foot"], kw["foot2"] = -50, -50
        return hands_head(kw)
    return make_spec([pose(True), pose(False)], None, X.mat(-200, 190), hilite=hil, lying=True, steps=8)


# =================================================================================================== DEAD BUG
@pat("dead_bug", ("none", [], "abs"))
def dead_bug(eq, var, hil):
    hil = hil or "abs"
    hip = (0, -14)
    S = X.add(hip, X.vup(-90, 92))
    table = (hip[0] + 68, hip[1] - 76)
    table2 = (table[0] + 8, table[1] + 2)
    ext = (hip[0] + 145 * math.cos(math.radians(10)), hip[1] - 145 * math.sin(math.radians(10)))
    up1 = (S[0] + 4, S[1] - 95)
    up2 = (S[0] - 4, S[1] - 95)
    over = (S[0] - 94, S[1] - 6)
    base = dict(hip=hip, torso=-90, head=-92, foot=-60, foot2=-60, kh=(-1, -0.3), kh2=(-1, -0.3), ah=(1, 0), ah2=(1, 0))
    def pose(arm1, arm2, leg1, leg2):
        kw = dict(base, W=arm1, W2=arm2, A=leg1, A2=leg2)
        return kw
    A_ = pose(up1, up2, table, table2)
    B_ = pose(over, up2, table, ext)      # near arm back + far leg out
    C_ = pose(up1, over, ext, table2)     # far arm back + near leg out
    return make_spec([A_, B_, A_, C_], None, X.mat(-200, 190), hilite=hil, lying=True, loop="cycle", steps=5)


# =================================================================================================== KETTLEBELL SWING
@pat("kettlebell_swing", ("kettlebell", [], "glutes"), ("dumbbell", [], "hamstrings"), ("kettlebell", ["single_arm"], "glutes"))
def kettlebell_swing(eq, var, hil):
    hil = hil or "glutes"
    single = has(var, "single_arm")
    def pose(hip, torso, head, wrist_rel=None, wrist=None, hint=(0, 1)):
        kw = dict(A=(0, -6), hip=hip, torso=torso, head=head, kh=(1, 0), foot=0)
        S = X.add(hip, X.vup(torso, 92))
        W = wrist if wrist is not None else (S[0] + wrist_rel[0], S[1] + wrist_rel[1])
        kw.update(W=W, ah=hint)
        if not single:
            kw.update(W2=(W[0] - 3, W[1] + 2), ah2=hint)
        return kw
    bottom = pose((-40, -118), 64, 52, wrist=(-6, -96), hint=(-0.2, 1))
    mid = pose((-16, -134), 40, 32, wrist_rel=(64, 52))
    top = pose((12, -150), -4, -4, wrist_rel=(92, -2))
    mid2 = pose((-8, -140), 24, 16, wrist_rel=(80, 30))
    equip = X.kettlebell("wrist", "farm") if eq == "kettlebell" else X.dumbbell("wrist")
    if eq == "dumbbell":
        equip = X.dumbbell("wrist")
    return make_spec([bottom, mid, top, mid2], equip, None, hilite=hil, loop="cycle", linear=True, steps=5)


# =================================================================================================== BURPEE
@pat("burpee", ("none", [], "quads"), ("none", ["pushup"], "chest"))
def burpee(eq, var, hil):
    hil = hil or "quads"
    stand = dict(A=(0, -6), hip=(0, -152), torso=0, head=0, W=(6, -149), ah=(0, 1), foot=0, kh=(0.3, -1))
    squat = dict(A=(0, -6), hip=(-26, -62), torso=70, head=60, kh=(0.3, -1), W=(66, -6.5), ah=(-0.3, -1), foot=0)
    plank = _plank_kw(66, True)
    plank["kh"] = (0.3, -1)
    plank.pop("E")
    plank["ah"] = (-0.3, -1)
    jump_hip = (0, -206)
    jump = dict(A=(0, -60), hip=jump_hip, torso=0, head=-6, foot=75, kh=(0.3, -1),
                W=(10, -392), ah=(1, 0))
    keys = [stand, squat, plank, dict(squat), jump]
    if has(var, "pushup"):
        low = _plank_kw(66, False, sy=-52)
        low.pop("E")
        low["W"] = (66, -6.5)
        low["ah"] = (-1, 0.2)
        low["kh"] = (0.3, -1)
        keys = [stand, squat, plank, low, plank, dict(squat), jump]
    return make_spec(keys, None, None, hilite=hil, loop="cycle", steps=4 if len(keys) == 5 else 3, hands_floor=True)


# =================================================================================================== JUMPING JACK (front view)
@pat("jumping_jack", ("none", [], "shoulders"))
def jumping_jack(eq, var, hil):
    hil = hil or "shoulders"
    a = dict(H=(0, -152), aR=(6, 4), aL=(-6, -4), lR=(0, 0), lL=(0, 0))
    b = dict(H=(0, -151), aR=(158, 172), aL=(-158, -172), lR=(18, 18), lL=(-18, -18))
    mid = dict(H=(0, -158), aR=(100, 130), aL=(-100, -130), lR=(9, 9), lL=(-9, -9))
    return make_spec([a, b], None, None, hilite=hil, view_kind="front", steps=8)


# =================================================================================================== RUN / WALK gait
def _gait_pose(u, hip_y, stance, lift, stride, torso, arm_amp, arm_bend, hop, hipx=0.0, straight_arms=False,
               foot_down=40.0):
    """Parametric gait: two legs half a cycle apart.  Returns mk() kwargs."""
    floor_a = -6.0

    def foot(phase):
        phase %= 1.0
        if phase < stance:
            t = phase / stance
            return (stride * (0.5 - t), floor_a), 0.0, False
        t = (phase - stance) / (1 - stance)
        x = stride * (-0.5 + t)
        y = floor_a - lift * math.sin(math.pi * t) ** 1.2
        return (x, y), foot_down * math.sin(math.pi * min(1, t * 1.15)) if t < 0.87 else 0.0, True
    f1, ang1, sw1 = foot(u)
    f2, ang2, sw2 = foot(u + 0.5)
    flight = sw1 and sw2
    hy = hip_y - (hop if flight else 0) - (hop * 0.5 if (sw1 or sw2) else 0)
    hip = (hipx, hy)
    A = (hip[0] + f1[0], f1[1])
    A2 = (hip[0] + f2[0], f2[1])
    c = math.cos(2 * math.pi * u)
    ua = -arm_amp * c
    if straight_arms:
        kw = dict(uarm=ua * 0.6, farm=ua * 0.6, FA=(-ua * 0.6, -ua * 0.6))
    else:
        kw = dict(uarm=ua, farm=ua + arm_bend, FA=(-ua, -ua + arm_bend))
    kw.update(A=A, A2=A2, hip=hip, torso=torso, head=torso * 0.6, kh=(1, 0.2), kh2=(1, 0.2), foot=ang1, foot2=ang2)
    return kw


@pat("run", ("none", [], "quads"))
def run(eq, var, hil):
    hil = hil or "quads"
    keys = [_gait_pose(i / 8.0, -140, 0.42, 62, 96, 10, 38, 80, 12, hipx=0) for i in range(8)]
    return make_spec(keys, None, None, hilite=hil, loop="cycle", linear=True, steps=3)


@pat("farmer_walk", ("dumbbell", [], "forearms"), ("kettlebell", [], "forearms"), ("barbell", [], "traps"))
def farmer_walk(eq, var, hil):
    hil = hil or "forearms"
    keys = [_gait_pose(i / 8.0, -146, 0.62, 18, 62, 1, 12, 0, 3, straight_arms=True, foot_down=15) for i in range(8)]
    for k in keys:
        k["uarm"] = k["farm"] = 3 + k["uarm"] * 0.0
        k["FA"] = (-2, -2)
        k.pop("farm2", None)
    if eq == "kettlebell":
        equip = X.kettlebell("wrist", "down")
        scene = X.kettlebell("wrist2", "down")
    elif eq == "barbell":
        equip, scene = X.barbell("wrist", half=40, plate=17), None
    else:
        equip, scene = X.dumbbell("wrist"), X.dumbbell("wrist2")
    return make_spec(keys, equip, scene, hilite=hil, loop="cycle", linear=True, steps=3)


@pat("high_knees", ("none", [], "quads"))
def high_knees(eq, var, hil):
    hil = hil or "quads"
    hip = (0, -152)
    drive = (hip[0] + 38, hip[1] + 64)
    down = (0, -6)
    def pose(near_up, hop=0.0):
        hp = (0, -152 - hop)
        kw = dict(hip=hp, torso=2, head=0, foot=0, foot2=0, kh=(1, 0.3), kh2=(1, 0.3))
        d_ = (hp[0] + 38, hp[1] + 66)
        if near_up is None:
            kw["A"], kw["A2"] = (0, -18), (4, -20)
            kw.update(uarm=-10, farm=70, FA=(10, 80))
        elif near_up:
            kw["A"], kw["A2"] = d_, (-3, -6)
            kw["foot"] = 35
            kw.update(uarm=-38, farm=30, FA=(38, 120))
        else:
            kw["A"], kw["A2"] = (0, -6), (d_[0] + 4, d_[1])
            kw["foot2"] = 35
            kw.update(uarm=38, farm=125, FA=(-38, 30))
        return kw
    return make_spec([pose(True), pose(None, 10), pose(False), pose(None, 10)], None, None, hilite=hil,
                     loop="cycle", linear=False, steps=5)


# =================================================================================================== CYCLING
@pat("cycling", ("machine", [], "quads"), ("none", [], "quads"))
def cycling(eq, var, hil):
    hil = hil or "quads"
    C = (0, -40)
    R = 34
    hip = (-48, -149)
    S = X.add(hip, X.vup(46, 92))
    keys = []
    n = 12
    for i in range(n):
        al = math.radians(90 - 360.0 * i / n)  # screen angle of the near pedal (clockwise on screen when i grows? see sign)
        al = math.radians(30 * i)
        p1 = (C[0] + R * math.cos(al), C[1] + R * math.sin(al))
        p2 = (C[0] - R * math.cos(al), C[1] - R * math.sin(al))
        ank1 = (p1[0] - 12, p1[1] - 8)
        ank2 = (p2[0] - 12, p2[1] - 8)
        keys.append(dict(A=ank1, A2=ank2, hip=hip, torso=46, head=24, kh=(1, -0.2), kh2=(1, -0.2), foot=-6, foot2=-6,
                         W=(64, -164), ah=(0.2, 1)))
    scene_i, front_i = X.bike_items(C, R)
    return make_spec(keys, front_i, scene_i, hilite=hil, loop="cycle", linear=True, steps=2)


# =================================================================================================== ROWING MACHINE
@pat("rowing_machine", ("machine", [], "back"), ("none", [], "quads"))
def rowing_machine(eq, var, hil):
    hil = hil or "back"
    ank = (92, -34)
    scene_i, seat_i, chain_i = X.rower_items(foot_x=105, rail_y=-40, front_x=205)
    def pose(hipx, torso, head, arms):
        hip = (hipx, -60)
        kw = dict(A=ank, hip=hip, torso=torso, head=head, kh=(0, -1), foot=-78)
        S = X.add(hip, X.vup(torso, 92))
        if arms == "out":
            kw["W"] = (S[0] + 76, S[1] + 40)
            kw["ah"] = (0, 1)
        else:
            kw["W"] = pt_on_torso(kw, 0.70, 17)
            kw["ah"] = (-1, 0.1)
        return kw
    catch = pose(36, 34, 30, "out")
    drive = pose(-34, 8, 4, "out")
    finish = pose(-34, -22, -20, "in")
    equip = X.many(seat_i, chain_i)
    return make_spec([catch, drive, finish], equip, scene_i, hilite=hil, steps=5)


# =================================================================================================== JUMP ROPE (front view)
@pat("jump_rope", ("none", [], "calves"))
def jump_rope(eq, var, hil):
    hil = hil or "calves"
    def f(hy, ry):
        return dict(H=(0, hy), lR=(1, 1), lL=(-1, -1), wR=lambda J: (J["H"][0] + 44, J["H"][1] - 4),
                    wL=lambda J: (J["H"][0] - 44, J["H"][1] - 4), hR=(0.7, 1), hL=(-0.7, 1), ry=ry)
    a = f(-152, -300)
    b = f(-162, 95)
    return make_spec([a, b], X.rope_front(), None, hilite=hil, view_kind="front", steps=8)


# =================================================================================================== STRETCHES
def _stand_kw(**kw):
    base = dict(A=(0, -6), torso=0, head=0, foot=0)
    base.update(kw)
    return base


@pat("stretch_standing", ("none", [], "quads"), ("none", [], "hamstrings"), ("none", [], "calves"),
     ("none", [], "chest"), ("none", [], "triceps"), ("none", [], "shoulders"), ("none", [], "lats"))
def stretch_standing(eq, var, hil):
    hil = hil or "hamstrings"
    S0 = (0, -244)
    rest = _stand_kw(hip=(0, -152), W=(5, -149), ah=(0, 1), kh=(1, 0))
    if hil in ("lats", "obliques", "back", "abs"):
        a = dict(H=(0, -152), lean=0, aR=(165, 175), aL=(-165, -175))
        b = dict(H=(0, -152), lean=22, head=22, aR=(168, 176), aL=(-168, -176))
        return make_spec([a, b], None, None, hilite=hil, view_kind="front")
    if hil == "quads":
        # stand on the far leg, near heel to the buttock, hand holds the ankle
        b = dict(rest, A=(-10, -150), kh=(0, 1), A2=(0, -6), kh2=(1, 0), foot=-100, foot2=0, W=(-8, -154), ah=(-0.6, 0.6))
        a = dict(rest, A=(2, -6), kh=(1, 0), A2=(0, -6), kh2=(1, 0), foot2=0)
        return make_spec([a, b], None, None, hilite=hil)
    if hil == "calves":
        wallx = 122
        hip = (16, -134)
        S = X.add(hip, X.vup(30, 92))
        b = dict(A=(-55, -6), hip=hip, torso=30, head=22, kh=(1, 0), foot=0, A2=(60, -6), kh2=(1, 0), foot2=0,
                 W=(wallx - 10, S[1] + 10), ah=(0, 1))
        a = dict(rest, A=(0, -6), A2=(4, -6), kh2=(1, 0))
        scene = X.box(wallx, -310, wallx + 14, 0, X.BENCHC, 2)
        return make_spec([a, b], None, scene, hilite=hil)
    if hil == "chest":
        a = _stand_kw(hip=(0, -152), kh=(1, 0), uarm=3, farm=3, FA=(3, 3))
        b = _stand_kw(hip=(0, -152), kh=(1, 0), torso=-4, head=-4, uarm=-68, farm=-58, FA=(-64, -54))
        return make_spec([a, b], None, None, hilite=hil)
    if hil == "triceps":
        a = _stand_kw(hip=(0, -152), kh=(1, 0), uarm=3, farm=3, FA=(3, 3))
        b = _stand_kw(hip=(0, -152), kh=(1, 0), uarm=170, farm=-22, front2=True)
        Jb = mk(**b)
        b["FA"] = (0, 0)
        b["W2"] = Jb["elbow"]
        b["E2"] = (Jb["shoulder"][0] + 12, Jb["shoulder"][1] - 12 + 30)
        b["E2"] = (Jb["elbow"][0] + 8, Jb["elbow"][1] + 40)
        return make_spec([a, b], None, None, hilite=hil)
    if hil == "shoulders":
        a = _stand_kw(hip=(0, -152), kh=(1, 0), uarm=3, farm=3, FA=(3, 3))
        S = mk(**a)["shoulder"]
        E1, W1 = (S[0] + 40, S[1] + 14), (S[0] + 10, S[1] + 24)
        b = _stand_kw(hip=(0, -152), kh=(1, 0), E=E1, W=W1, E2=(S[0] + 30, S[1] + 40), W2=E1, front2=True)
        return make_spec([a, b], None, None, hilite=hil)
    # hamstrings: standing forward fold
    a = dict(rest)
    hip = (-10, -150)
    b = _stand_kw(hip=hip, torso=148, head=150, kh=(1, 0), W=(34, -12), ah=(0.5, -1))
    b["A"] = (0, -6)
    return make_spec([a, b], None, None, hilite=hil)


@pat("stretch_seated", ("none", [], "hamstrings"), ("none", [], "glutes"), ("none", [], "back"))
def stretch_seated(eq, var, hil):
    hil = hil or "hamstrings"
    hip = (0, -14)
    mat = X.mat(-120, 220)
    if hil == "glutes":
        # seated knee hug: near foot pulled in towards the buttock, hands around the shin, far leg flat
        base = dict(hip=hip, A2=(146, -9), kh2=(0, -1), foot2=-80, foot=0, kh=(0, -1))
        a = dict(base, A=(72, -6), torso=2, head=2)
        b = dict(base, A=(30, -34), torso=-6, head=0)
        for kw, wr in ((a, (66, -66)), (b, (50, -80))):
            kw.update(W=wr, ah=(-0.5, 0.6))
        return make_spec([a, b], None, mat, hilite=hil)
    toe = (146, -9)
    a = dict(A=toe, hip=hip, torso=0, head=0, foot=-80, kh=(0, -1), W=(30, -10), ah=(0, 1))
    b = dict(A=toe, hip=hip, torso=76, head=80, foot=-80, kh=(0, -1))
    S1 = X.add(hip, X.vup(76, 92))
    b.update(W=(toe[0] + 6, toe[1] - 10), ah=(-0.3, -1))
    S0 = X.add(hip, X.vup(0, 92))
    a["W"] = (S0[0] + 40, -12)
    a["ah"] = (-0.3, -1)
    return make_spec([a, b], None, mat, hilite=hil, lying=True)


@pat("stretch_lying", ("none", [], "hamstrings"), ("none", [], "glutes"), ("none", [], "abs"), ("band", [], "hamstrings"))
def stretch_lying(eq, var, hil):
    hil = hil or "glutes"
    hip = (0, -14)
    mat = X.mat(-200, 190)
    S_flat = X.add(hip, X.vup(-90, 92))
    flat_far = (145, -8)
    arms_side = dict(E=(S_flat[0] + 48, S_flat[1] + 7), W=(S_flat[0] + 94, S_flat[1] + 7), behind=True)
    if hil == "abs":
        # cobra: prone, press the chest up
        legs = dict(hip=(0, -12), A=(-145, -8), foot=180, kh=(0, -1))
        a = dict(legs, torso=88, head=84, W=(92, -6.5), E=(60, -6.5))
        b = dict(legs, torso=52, head=34)
        S1 = X.add((0, -12), X.vup(52, 92))
        b.update(W=(S1[0] + 6, -6.5), ah=(-1, 0))
        a.pop("E")
        a["W"] = (88, -6.5)
        a["ah"] = (-1, 0)
        return make_spec([a, b], None, mat, hilite=hil, lying=True)
    if hil == "hamstrings":
        up = (hip[0] + 145.5 * math.cos(math.radians(80)), hip[1] - 145.5 * math.sin(math.radians(80)))
        a = dict(hip=hip, torso=-90, head=-92, A=flat_far, A2=(flat_far[0] + 2, -8), foot=-80, foot2=-80, kh=(0, -1), **arms_side)
        if eq in ("band", "strap"):
            b = dict(a, A=up, torso=-72, head=-62, foot=-150, behind=False)
            S1 = X.add(hip, X.vup(-72, 92))
            b.update(W=(S1[0] + 76, S1[1] - 52), E=None, ah=(0.3, -1))
            b.pop("E")
            a.update(ah=(0.3, -1))
            a.pop("E")
            a["W"] = (S_flat[0] + 94, S_flat[1] + 7)
            a["W"] = (S_flat[0] + 90, S_flat[1] + 7)
            equip = X.band_line(lambda J: J["ankle"], to="wrist", post=False)
            return make_spec([a, b], equip, mat, hilite=hil, lying=True)
        b = dict(a, A=up, torso=-60, head=-52, foot=-150, behind=False)
        S1 = X.add(hip, X.vup(-60, 92))
        knee_back = (hip[0] + 0.6 * (up[0] - hip[0]) - 6, hip[1] + 0.6 * (up[1] - hip[1]))
        b.update(W=knee_back, ah=(0, -1))
        b.pop("E")
        return make_spec([a, b], None, mat, hilite=hil, lying=True)
    # knee to chest (default)
    flat = dict(hip=hip, torso=-90, head=-92, A=(84, -6), kh=(0, -1), foot=0, A2=(86, -6), foot2=0, **arms_side)
    a = dict(flat)
    knee = (hip[0] - 30, hip[1] - 78)
    b = dict(flat, A=(hip[0] + 8, hip[1] - 16), kh=(-1, -0.4), torso=-76, head=-62, foot=-30, behind=False)
    S1 = X.add(hip, X.vup(-76, 92))
    b.pop("E")
    b.update(W=(knee[0] + 4, knee[1] + 24), ah=(0, -1))
    return make_spec([a, b], None, mat, hilite=hil, lying=True)


@pat("stretch_kneeling", ("none", [], "quads"), ("none", [], "back"))
def stretch_kneeling(eq, var, hil):
    hil = hil or "quads"
    mat = X.mat(-170, 130)
    if hil in ("back", "lats", "shoulders", "abs", "obliques"):
        legs = dict(A=(-72, -8), shin=90, thigh=-60, foot=180)
        a = dict(legs, torso=6, head=6, uarm=3, farm=3)
        b = dict(legs, torso=88, head=92, W=(112, -6.5), ah=(0, -1))
        a = dict(legs, torso=6, head=6, W=(18, -164), ah=(0, 1))
        J0 = mk(**a)
        a["W"] = (J0["shoulder"][0] + 5, J0["shoulder"][1] + 94)
        return make_spec([a, b], None, mat, hilite=hil)
    front = (70, -6)
    def pose(hip, torso, arms_up):
        kw = dict(A=front, hip=hip, torso=torso, head=torso, kh=(1, 0), foot=0, A2=(-112, -8), kh2=(0, 1), foot2=180)
        S = X.add(hip, X.vup(torso, 92))
        if arms_up:
            kw.update(W=(S[0] + 12, S[1] - 92), ah=(1, 0))
        else:
            kw.update(W=(hip[0] + 40, hip[1] - 4), ah=(-0.3, 1))
        return kw
    a = pose((-12, -78), 4, False)
    b = pose((16, -70), -6, True)
    return make_spec([a, b], None, mat, hilite=hil)
