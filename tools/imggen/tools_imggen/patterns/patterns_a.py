"""Legs / hips and push patterns.  Every pattern is fn(equipment, variants, hilite) -> engine spec.

Conventions: world x to the right (the figure faces +x), y down, floor y = FLOOR (6).  A standing figure has its
ankle at (0, 0).  Key poses are given as contact targets (hip, hand, back ankle ...) via body().
"""
import math
from ..figure import (fpose, front_dumbbells, body, vup, vdown, add, sub, mul, dist, ik2, torso_pt, L, FLOOR, E, gear, Gear, barbell, dumbbell,
                      kettlebell, band, cable_station, box, mat, swiss_ball, flat_bench, adj_bench, pad_line,
                      pullup_bar, dip_bars, lever, post, smith_rail, wcap, wcirc, wrect, wline, wpoly, wring,
                      METAL, METAL_D, PAD, PAD_L, BENCHC, RUBBER, EQUIP, ACCENT, KBC, BANDC, ang_up, ang_down, seat_pad)

PATTERNS = {}
DEMOS = {}
USED_VARIANTS = {}


def pattern(name, used=(), demos=()):
    def deco(fn):
        PATTERNS[name] = fn
        USED_VARIANTS[name] = set(used)
        DEMOS[name] = list(demos)
        return fn
    return deco


def spec(poses, equipment=None, scene=None, hilite=None, **kw):
    d = dict(poses=poses, equipment=equipment, scene=scene, hilite=hilite)
    d.update(kw)
    return d


def has(var, *names):
    return any(n in var for n in names)


def deg(r):
    return math.degrees(r)


def held(eq, var, size=1.0, plate=22):
    """Gear held in the hand (at the 'wrist' point) for the usual equipment ids."""
    if eq in ("barbell", "sz_bar", "machine_bar"):
        return barbell("wrist", plate=plate, sz=(eq == "sz_bar"))
    if eq == "dumbbell":
        return dumbbell("wrist", size=size)
    if eq == "kettlebell":
        return kettlebell("wrist", size=size)
    return None


def hang_pose(shoulder_x, shoulder_y, hip_y, rel=(4, 97), **kw):
    """Hinged body whose shoulder sits at (shoulder_x, shoulder_y): torso angle follows from the hip height."""
    c = max(-1.0, min(1.0, (hip_y - shoulder_y) / L["torso"]))
    t = math.acos(c)
    hip = (shoulder_x - L["torso"] * math.sin(t), hip_y)
    return body(ankle=(0, 0), hip=hip, torso=deg(t), hand_rel=rel, **kw)


STAND_HIP = (0, -145.5)


# ============================================================================================================ SQUAT
@pattern("squat", used=("front", "overhead", "bodyweight", "narrow", "wide", "single_arm"),
         demos=[("barbell", [], "quads"), ("barbell", ["front"], "quads"), ("dumbbell", [], "glutes"),
                ("kettlebell", [], "quads"), ("none", [], "quads"), ("machine", [], "quads"), ("band", [], "glutes")])
def squat(eq, var, hil):
    machine = eq == "machine"
    overhead = has(var, "overhead")
    ah, bh, bt = (0, -145.5), (-44, -86), 44
    if machine:
        ah, bh, bt = (-10, -144), (-54, -86), 24
    equip, scene = None, None
    if overhead:
        kw = dict(hand_rel=(6, -100), elbow_side=-1)
        bh, bt = (-44, -88), 36
        equip = held(eq if eq in ("barbell", "sz_bar", "dumbbell", "kettlebell") else "none", var, size=1.1, plate=20)
        if eq == "machine":
            equip = barbell("wrist", plate=20)
    elif eq in ("barbell", "sz_bar", "machine"):
        if has(var, "front"):
            kw = dict(hand_t=(22, 15), elbow_side=-1)
        else:
            kw = dict(hand_t=(-6, -17), elbow_side=-1)
        equip = barbell("wrist", plate=22)
        if machine:
            scene = smith_rail(-30, -300)
    elif eq in ("dumbbell", "kettlebell", "cable"):
        kw = dict(hand_t=(14, 24), elbow_side=1)
        equip = held(eq if eq != "cable" else "dumbbell", var, size=1.0)
    elif eq == "band":
        kw = dict(hand_t=(22, 15), elbow_side=-1)
        equip = band((12, FLOOR - 2), "wrist")
    else:
        kw = dict(uarm=90, farm=93)
    A = body(hip=ah, torso=2, **kw)
    B = body(hip=bh, torso=bt, **kw)
    if eq in ("box", "bench", "incline_bench", "decline_bench"):
        scene = box(-112, -22, 78) if eq == "box" else flat_bench(-118, -18, FLOOR - 78, 12)
    return spec([A, B], equip, scene, hil)


# ============================================================================================================ HINGE
@pattern("hinge", used=("reverse", "romanian", "bodyweight", "single_arm", "standing"),
         demos=[("barbell", [], "hamstrings"), ("barbell", ["reverse"], "glutes"), ("dumbbell", [], "glutes"),
                ("kettlebell", [], "glutes"), ("none", [], "glutes"), ("cable", [], "glutes"), ("band", [], "hamstrings")])
def hinge(eq, var, hil):
    rdl = has(var, "reverse", "romanian", "stiff")
    equip = None
    if eq not in ("barbell", "sz_bar", "machine", "dumbbell", "kettlebell", "band", "cable"):
        eq = "none"
    if eq in ("barbell", "sz_bar", "machine"):
        plate = 28
        bar_y = FLOOR - plate + 5
        equip = barbell("wrist", plate=plate)
    elif eq == "dumbbell":
        bar_y = FLOOR - 17
        equip = dumbbell("wrist", size=1.6)
    elif eq == "kettlebell":
        bar_y = FLOOR - 36
        equip = kettlebell("wrist")
    elif eq == "band":
        bar_y = FLOOR - 12
        equip = band((10, FLOOR - 2), "wrist")
    if eq in ("none", "cable"):
        if eq == "none":
            kwb = dict(hand_t=(14, 12), elbow_side=1)  # arms folded across the chest
            top = body(hip=(-3, -145), torso=0, **kwb)
            low = body(hip=(-64, -112), torso=74, **kwb)
            return spec([low, top], None, None, hil)
        equip = cable_station((-125, -16), "wrist", handle="rope", face=-1)
        top = body(hip=(0, -145), torso=0, hand_rel=(14, 90))
        low = body(hip=(-66, -108), torso=66, hand_rel=(8, 96))
        return spec([low, top], equip, None, hil)
    top = body(hip=(-3, -145), torso=-2, hand_rel=(5, 98))
    if rdl:
        low = hang_pose(24, -(98 + 38), hip_y=-124)  # bar at mid-shin
    else:
        low = hang_pose(12, bar_y - 98, hip_y=-82)
    return spec([low, top], equip, None, hil)


# ============================================================================================================ LUNGE
@pattern("lunge", used=("reverse", "alternating", "bodyweight", "front", "single_arm"),
         demos=[("none", [], "quads"), ("dumbbell", [], "glutes"), ("barbell", [], "quads"),
                ("kettlebell", [], "quads"), ("none", ["reverse"], "glutes"), ("dumbbell", ["reverse"], "glutes")])
def lunge(eq, var, hil):
    front_ankle = (0, 0)
    toe_x = -108
    f2 = 62
    back_ankle = (toe_x - math.cos(math.radians(f2)) * 20.4, FLOOR - 5.4 - math.sin(math.radians(f2)) * 20.4)
    equip = None
    if eq in ("barbell", "sz_bar", "machine"):
        kw = dict(hand_t=(-6, -17), elbow_side=-1)
        equip = barbell("wrist", plate=22)
    elif eq == "dumbbell":
        kw = dict(hand_rel=(3, 97))
        equip = dumbbell("wrist", size=1.15)
    elif eq == "kettlebell":
        kw = dict(hand_t=(14, 24), elbow_side=1)
        equip = kettlebell("wrist")
    else:
        kw = dict(hand_t=(80, 6), elbow_side=1)  # hands on the hips
    bottom = body(ankle=front_ankle, hip=(-58, -74), torso=2, back=back_ankle, back_side=-1, b_foot=f2, **kw)
    if has(var, "reverse"):
        start = body(ankle=front_ankle, hip=(-2, -145), torso=0, back=(-18, 0), back_side=-1, b_foot=0, **kw)
    else:
        start = body(ankle=front_ankle, hip=(-62, -126), torso=2, back=back_ankle, back_side=-1, b_foot=f2, **kw)
    return spec([start, bottom], equip, None, hil)


# ============================================================================================================ helpers for machines
def unit(v):
    n = math.hypot(v[0], v[1]) or 1.0
    return (v[0] / n, v[1] / n)


def shin_pad(side=1, frac=0.18, length=17, th=7.5, lever_from=None, front=True):
    """Roller pad on the lower leg (side=+1 front of the shin, -1 back of it) + lever to a fixed pivot."""
    def mid(d, T, P, s):
        a, k = P["ankle"], P["knee"]
        dv = unit(sub(k, a))
        nrm = (-dv[1], dv[0])  # front normal of the shin
        c = (a[0] + (k[0] - a[0]) * frac + nrm[0] * side * (6.4 + th / 2 - 0.5),
             a[1] + (k[1] - a[1]) * frac + nrm[1] * side * (6.4 + th / 2 - 0.5))
        if lever_from is not None:
            wline(d, T, s, lever_from, c, 5.0, METAL_D)
            wcirc(d, T, s, lever_from, 5.6, METAL)
        wcap(d, T, s, add(c, mul(dv, -length / 2)), add(c, mul(dv, length / 2)), th / 2, th / 2, PAD)
        wcap(d, T, s, add(c, mul(dv, -length / 2 + 1)), add(c, mul(dv, length / 2 - 1)), th / 2 - 2.2, th / 2 - 2.2, PAD_L)
    return Gear(mid=mid)


def machine_seat(hip, torso, seat_len=(-26, 44), back_len=(-22, 78), th=11, frame=True, base=(-40, 120)):
    """Seat pad under the hip + back pad along the torso + frame down to the floor."""
    t = vup(torso)
    nrm = (math.cos(math.radians(torso)), math.sin(math.radians(torso)))
    seat_top = hip[1] + 13
    p0 = add(add(hip, mul(t, -back_len[0])), mul(nrm, -(14 + th / 2)))
    p1 = add(add(hip, mul(t, back_len[1])), mul(nrm, -(14 + th / 2)))
    sx0, sx1 = hip[0] + seat_len[0], hip[0] + seat_len[1]

    def back(d, T, P, s):
        if frame:
            wrect(d, T, s, hip[0] + base[0], FLOOR - 7, hip[0] + base[1], FLOOR, 2, METAL_D)
            wrect(d, T, s, hip[0] - 4, seat_top, hip[0] + 4, FLOOR - 4, 1, METAL_D)
            wline(d, T, s, (hip[0] - 4, FLOOR - 6), add(hip, mul(t, back_len[1] * 0.7)), 5, METAL_D)
        wrect(d, T, s, sx0, seat_top, sx1, seat_top + th, 5, PAD)
        wcap(d, T, s, p0, p1, th / 2 + 1, th / 2 + 1, PAD)
        wcap(d, T, s, add(p0, mul(nrm, 2.5)), add(p1, mul(nrm, 2.5)), th / 2 - 2, th / 2 - 2, PAD_L)
    return Gear(back=back, bounds=(min(sx0, p0[0], p1[0]) - 10, min(p0[1], p1[1]) - 14, max(sx1, p0[0], p1[0]) + 10, FLOOR))


# ============================================================================================================ LEG PRESS
@pattern("leg_press", used=("seated", "single_arm"),
         demos=[("machine", [], "quads"), ("machine", ["seated"], "quads"), ("machine", [], "glutes")])
def leg_press(eq, var, hil):
    seated = has(var, "seated")
    rail_deg = 0.0 if seated else 40.0
    recline = -16.0 if seated else -50.0
    r = (math.cos(math.radians(rail_deg)), -math.sin(math.radians(rail_deg)))
    pdir = (-r[1], r[0]) if rail_deg else (0.0, 1.0)  # perpendicular, pointing down-forward
    hip = (-60, -62) if seated else (-72, -44)

    def ankle_at(dd):
        return (hip[0] + r[0] * dd, hip[1] + r[1] * dd)

    toe_dir = (-pdir[0], -pdir[1])  # toes point up the plate
    foot = math.degrees(math.atan2(toe_dir[1], toe_dir[0]))
    kw = dict(hip=hip, torso=recline, foot=foot, hand_t=(80, 20), elbow_side=1)
    A = body(ankle=ankle_at(98), **kw)
    B = body(ankle=ankle_at(138), **kw)
    PL = 6.5 + 4

    def sled(d, T, P, s):
        a = P["ankle"]
        c = add(a, mul(r, PL))
        top = add(c, mul(pdir, -46))
        bot = add(c, mul(pdir, 64))
        wcap(d, T, s, bot, top, 4.0, 4.0, (176, 182, 198))
        wcap(d, T, s, add(c, mul(pdir, -46)), add(c, mul(pdir, -46)), 4.6, 4.6, METAL)

    def rails(d, T, P, s):
        off = 64
        # rail from the floor (near the seat) up to the far end, parallel to the legs
        a1 = add(ankle_at(172), mul(pdir, off))
        if rail_deg:
            k0 = ((FLOOR - 9) - a1[1]) / (-r[1])
            a0 = (a1[0] - r[0] * k0, FLOOR - 9)
        else:
            a0 = (hip[0] + 10, a1[1])
        wline(d, T, s, a0, a1, 6.5, METAL_D)
        wrect(d, T, s, a1[0] - 3.5, a1[1], a1[0] + 3.5, FLOOR - 5, 1, METAL_D)
        wrect(d, T, s, a1[0] - 20, FLOOR - 5, a1[0] + 20, FLOOR, 2, METAL_D)
        wrect(d, T, s, hip[0] - 70, FLOOR - 6, a1[0] + 20, FLOOR, 2, METAL_D)
        if not rail_deg:
            wrect(d, T, s, a0[0] - 3, a0[1], a0[0] + 3, FLOOR - 5, 1, METAL_D)

    seat = machine_seat(hip, recline, seat_len=(-34, 36), back_len=(-30, 78), base=(-60, 20), frame=False)
    xs = [hip[0] - 80, ankle_at(168)[0] + 20]
    scene = gear(Gear(back=rails, bounds=(xs[0], ankle_at(172)[1] + 70, ankle_at(172)[0] + 40, FLOOR)), seat)
    return spec([A, B], Gear(mid=sled), scene, hil)


# ============================================================================================================ LEG EXTENSION
@pattern("leg_extension", used=("seated", "single_arm"),
         demos=[("machine", [], "quads"), ("machine", ["single_arm"], "quads")])
def leg_extension(eq, var, hil):
    hip = (-60, -83)
    torso = -9
    if eq != "machine":
        # plain seat: ankle weight / band, hands holding the seat
        kw = dict(hip=hip, thigh=-90, torso=-4, hand=(hip[0] + 16, hip[1] + 8), elbow_side=1)
        A = body(shin=-6, foot=-6, **kw)
        B = body(shin=-98, foot=-98, **kw)
        seat = flat_bench(hip[0] - 40, hip[0] + 62, hip[1] + 14.5, 11)
        equip = None
        if eq == "band":
            equip = band((hip[0] - 46, FLOOR - 2), "ankle")
        elif eq in ("dumbbell", "kettlebell", "barbell"):
            equip = Gear(front=lambda d, T, P, s: wcap(d, T, s, add(P["ankle"], (-6, 0)), add(P["ankle"], (6, 0)), 7, 7, KBC))
        return spec([A, B], equip, seat, hil)
    A = body(hip=hip, thigh=-90, shin=-6, torso=torso, foot=-6, hand_t=(76, 16), elbow_side=1)
    B = body(hip=hip, thigh=-90, shin=-98, torso=torso, foot=-98, hand_t=(76, 16), elbow_side=1)
    pivot = (hip[0] + 62, hip[1] + 26)
    pad = shin_pad(side=1, frac=0.22, lever_from=pivot)
    seat = machine_seat(hip, torso, seat_len=(-26, 66), back_len=(-26, 80), base=(-50, 100))
    return spec([A, B], pad, seat, hil)


# ============================================================================================================ LEG CURL
@pattern("leg_curl", used=("seated", "standing", "lying", "single_arm"),
         demos=[("machine", [], "hamstrings"), ("machine", ["seated"], "hamstrings"),
                ("none", ["standing"], "hamstrings"), ("cable", ["standing"], "hamstrings")])
def leg_curl(eq, var, hil):
    if has(var, "standing") and not has(var, "lying", "seated"):
        hip = (0, -145.5)
        kw = dict(hip=hip, thigh=0, torso=2, hand=(50, -150), elbow_side=1, b_thigh=0, b_shin=0, b_foot=0)
        A = body(shin=0, foot=0, **kw)
        B = body(shin=108, foot=108, **kw)
        scene = post(52, -157, FLOOR, w=6)
        equip = None
        if eq == "cable":
            equip = cable_station((70, -14), "ankle", handle="strap", face=1)
            scene = gear(scene)
        elif eq == "band":
            equip = band((70, FLOOR - 4), "ankle")
        return spec([A, B], equip, scene, hil)
    if has(var, "seated"):
        hip = (-60, -83)
        torso = -9
        kw = dict(hip=hip, thigh=-90, torso=torso, hand_t=(76, 16), elbow_side=1)
        A = body(shin=-98, foot=-98, **kw)
        B = body(shin=-2, foot=-2, **kw)
        pivot = (hip[0] + 70, hip[1] + 30)
        pad = shin_pad(side=-1, frac=0.1, lever_from=pivot)
        seat = machine_seat(hip, torso, seat_len=(-26, 66), back_len=(-26, 80), base=(-50, 100))
        thigh_pad = Gear(back=lambda d, T, P, s: wcap(d, T, s, (hip[0] + 36, hip[1] - 17), (hip[0] + 66, hip[1] - 17), 6, 6, PAD))
        return spec([A, B], pad, gear(seat, thigh_pad), hil)
    # lying (prone) machine curl, head towards +x
    pad_top = -52
    hip = (-14, pad_top - 15)
    kw = dict(hip=hip, thigh=90, torso=90, head=62, hand=(hip[0] + 112, pad_top + 8), elbow_side=1)
    A = body(shin=92, foot=182, **kw)
    B = body(shin=196, foot=286, **kw)
    pivot = (hip[0] - 98, pad_top + 12)

    def bench(d, T, P, s):
        x0, x1 = hip[0] - 94, hip[0] + 106
        for x in (x0 + 18, x1 - 18):
            wrect(d, T, s, x - 3.5, pad_top + 10, x + 3.5, FLOOR, 1, METAL_D)
            wrect(d, T, s, x - 14, FLOOR - 5, x + 14, FLOOR, 2, METAL_D)
        wrect(d, T, s, x0, pad_top, x1, pad_top + 12, 5, PAD)
        wrect(d, T, s, x0 + 2, pad_top, x1 - 2, pad_top + 5, 3, PAD_L)
        wrect(d, T, s, x1 - 34, pad_top - 20, x1 - 4, pad_top - 2, 6, PAD)  # chest pad (raised)
        wline(d, T, s, (x1 - 8, pad_top + 6), (x1 + 4, pad_top + 20), 4, METAL_D)  # handle

    pad = shin_pad(side=-1, frac=0.1, lever_from=pivot)
    return spec([A, B], pad, Gear(back=bench, bounds=(hip[0] - 110, pad_top - 30, hip[0] + 112, FLOOR)), hil)


# ============================================================================================================ CALF RAISE
@pattern("calf_raise", used=("seated", "standing", "single_arm", "bodyweight"),
         demos=[("none", [], "calves"), ("dumbbell", [], "calves"), ("barbell", [], "calves"),
                ("machine", [], "calves"), ("machine", ["seated"], "calves")])
def calf_raise(eq, var, hil):
    step_h = 12.0
    toe_y = FLOOR - step_h - 5.4
    foot_len = L["foot"]

    def ank(f, tx=26.0):
        fr = math.radians(f)
        return (tx - math.cos(fr) * foot_len, toe_y - math.sin(fr) * foot_len)

    stepbox = box(-4, 42, step_h)
    fa, fb = -14.0, 52.0
    if has(var, "seated"):
        # thighs horizontal, weight pad on the knees
        def seated(f, lift):
            a = ank(f)
            knee = (a[0], a[1] - 70)
            hip = (knee[0] - 76, knee[1])
            return body(hip=hip, thigh=-90, shin=0, torso=-4, foot=f, hand_t=(70, 18), elbow_side=1)
        A, B = seated(fa, 0), seated(fb, 1)
        hip = (A["ox"] - 76, A["oy"] - 70)
        seat_top = hip[1] + 13
        pieces = [flat_bench(hip[0] - 36, hip[0] + 40, seat_top, 11), stepbox]
        equip = None
        if eq in ("dumbbell", "kettlebell", "barbell", "sz_bar"):
            def weight(d, T, P, s):
                k = P["knee"]
                if eq == "dumbbell":
                    wcap(d, T, s, (k[0] - 14, k[1] - 17), (k[0] - 14, k[1] - 17), 9, 9, EQUIP)
                else:
                    wcirc(d, T, s, (k[0] - 14, k[1] - 22), 14, RUBBER)
            equip = Gear(mid=weight)
        elif eq == "band":
            equip = band((10, FLOOR - 3), lambda P: (P["knee"][0] - 4, P["knee"][1] - 12))
        else:
            def kneepad(d, T, P, s):
                k = P["knee"]
                wcap(d, T, s, (k[0] - 30, k[1] - 19), (k[0] + 2, k[1] - 19), 6.5, 6.5, PAD)
                wline(d, T, s, (k[0] - 14, k[1] - 22), (k[0] - 14, k[1] - 74), 5, METAL_D)
                wrect(d, T, s, k[0] - 30, k[1] - 82, k[0] + 14, k[1] - 74, 3, METAL_D)
            if eq == "machine":
                equip = Gear(mid=kneepad)
        return spec([A, B], equip, gear(*pieces), hil)
    hip_y = lambda f: ank(f)[1] - 145.0
    kwb = {}
    equip = None
    if eq in ("barbell", "sz_bar", "machine"):
        kwb = dict(hand_t=(-6, -17), elbow_side=-1)
        equip = barbell("wrist", plate=22)
    elif eq == "dumbbell":
        kwb = dict(hand_rel=(3, 99))
        equip = dumbbell("wrist", size=1.1)
    elif eq == "kettlebell":
        kwb = dict(hand_t=(14, 24), elbow_side=1)
        equip = kettlebell("wrist")
    else:
        kwb = dict(hand_t=(80, 6), elbow_side=1)  # hands on hips
    A = body(ankle=ank(fa), hip=(ank(fa)[0], ank(fa)[1] - 145), torso=0, foot=fa, **kwb)
    B = body(ankle=ank(fb), hip=(ank(fb)[0], ank(fb)[1] - 145), torso=0, foot=fb, **kwb)
    scene = stepbox
    if eq == "machine":
        # shoulder-pad machine: pads on the shoulders, column behind
        def pads(d, T, P, s):
            sh = P["shoulder"]
            wcap(d, T, s, (sh[0] - 14, sh[1] - 12), (sh[0] + 14, sh[1] - 12), 7, 7, PAD)
            wline(d, T, s, (-62, sh[1] - 12), (sh[0] - 8, sh[1] - 12), 6, METAL_D)
        col = post(-62, -300, FLOOR, w=8)
        equip = Gear(mid=pads)
        scene = gear(stepbox, col)
    return spec([A, B], equip, scene, hil)


# ============================================================================================================ HIP THRUST
@pattern("hip_thrust", used=("bodyweight", "single_arm", "lying"),
         demos=[("barbell", [], "glutes"), ("dumbbell", [], "glutes"), ("none", [], "glutes"), ("machine", [], "glutes")])
def hip_thrust(eq, var, hil):
    on_mat = eq in ("none", "mat", "band") or has(var, "bodyweight")
    sh_y = FLOOR - 4 - 15 if on_mat else -80
    ankle = (0, -4 if on_mat else 0)
    sx = -150 if not on_mat else -150

    def pose(hip, **kw):
        sh = (hip[0] - 0, hip[1])
        # torso angle so that the shoulder sits on (sx, sh_y): solve from hip
        dx, dy = sx - hip[0], sh_y - hip[1]
        t = math.degrees(math.atan2(dx, -dy))
        h2 = (sx - vup(t, L["torso"])[0], sh_y - vup(t, L["torso"])[1])
        return body(ankle=ankle, hip=h2, torso=t, head=-90 + (t + 90) * 0.0, **kw)

    equip = None
    if eq in ("barbell", "sz_bar", "machine"):
        kw = dict(hand_t=(90, 17), elbow_side=1)
        equip = barbell("wrist", plate=24)
        # bar over the hips: hand at the hip crease
    elif eq == "dumbbell":
        kw = dict(hand_t=(90, 15), elbow_side=1)
        equip = dumbbell("wrist", size=1.4)
    else:
        kw = dict(hand=(sx + 101, FLOOR - 9), elbow_side=-1) if on_mat else dict(hand_t=(88, 8), elbow_side=1)
    # hip heights: down near the floor, up so that the thigh is horizontal
    top_hip = (-76, ankle[1] - 70)
    low_hip = (-62, sh_y + 58 if not on_mat else FLOOR - 4 - 20)
    A = pose(low_hip, **kw)
    B = pose(top_hip, **kw)
    if on_mat:
        scene = mat(-250, 80, 4)
    else:
        scene = flat_bench(-250, -144, sh_y + 15, 12)
    return spec([A, B], equip, scene, hil)


# ============================================================================================================ STEP UP
@pattern("step_up", used=("alternating", "single_arm", "bodyweight"),
         demos=[("none", [], "quads"), ("dumbbell", [], "glutes"), ("barbell", [], "quads"), ("bench", [], "glutes")])
def step_up(eq, var, hil):
    h = 56.0
    top = FLOOR - h
    lead = (22, top - 6)
    equip, kw = None, {}
    if eq in ("barbell", "sz_bar", "machine"):
        kw = dict(hand_t=(-6, -17), elbow_side=-1)
        equip = barbell("wrist", plate=22)
    elif eq == "dumbbell":
        kw = dict(hand_rel=(3, 99))
        equip = dumbbell("wrist", size=1.1)
    elif eq == "kettlebell":
        kw = dict(hand_t=(14, 24), elbow_side=1)
        equip = kettlebell("wrist")
    else:
        kw = dict(hand_t=(80, 6), elbow_side=1)
    A = body(ankle=lead, hip=(lead[0] - 62, lead[1] - 66), torso=18, back=(-52, 0), back_side=-1, b_foot=0, **kw)
    B = body(ankle=lead, hip=(lead[0] - 8, lead[1] - 144), torso=2, back=(lead[0] - 26, lead[1] - 84), back_side=-1,
             b_foot=20, **kw)
    if eq == "bench":
        scene = flat_bench(-6, 90, top, 12)
    else:
        scene = box(-6, 90, h)
    return spec([A, B], equip, scene, hil)


# ============================================================================================================ bench helpers
def rack_posts(x, hook_y, top=None):
    """Squat/bench rack: upright from the floor with a J-hook at hook_y."""
    top = top if top is not None else hook_y - 26

    def back(d, T, P, s):
        wrect(d, T, s, x - 3.5, top, x + 3.5, FLOOR - 4, 1, METAL_D)
        wrect(d, T, s, x - 18, FLOOR - 5, x + 22, FLOOR, 2, METAL_D)
        wline(d, T, s, (x, hook_y), (x + 14, hook_y - 3), 4, METAL)
    return Gear(back=back, bounds=(x - 18, top, x + 22, FLOOR))


def pad_bench(hip, torso, seat=True, th=12):
    """Bench pad along the torso (centerline offset behind the back) + seat + frame down to the floor."""
    t = vup(torso)
    nrm = (math.cos(math.radians(torso)), math.sin(math.radians(torso)))
    off = 14.5 + th / 2
    p_head = add(add(add(hip, mul(t, L["torso"] + 40)), mul(nrm, -off)), (0, 0))
    p_foot = add(add(hip, mul(t, -26)), mul(nrm, -off))
    seat_top = hip[1] + 14.5
    decl = torso < -92

    def back(d, T, P, s):
        # frame legs
        def leg(x, ytop):
            wrect(d, T, s, x - 3.2, ytop, x + 3.2, FLOOR - 4, 1, METAL_D)
            wrect(d, T, s, x - 12, FLOOR - 5, x + 12, FLOOR, 2, METAL_D)
        if decl:
            leg(p_foot[0] + 8, p_foot[1] + 4)
            leg(p_head[0] + 22, p_head[1] + 6)
        elif torso < -88:
            leg(p_foot[0] + 10, p_foot[1] + 4)
            leg(p_head[0] - 10, p_head[1] + 4)
        else:
            leg(hip[0] + 18, seat_top + th - 2)
            leg(hip[0] - 20, seat_top + th - 2)
            mid_ = ((p_head[0] + p_foot[0]) / 2, (p_head[1] + p_foot[1]) / 2)
            wline(d, T, s, (hip[0] - 20, FLOOR - 8), mid_, 5, METAL_D)
        if seat and torso > -88:
            wrect(d, T, s, hip[0] - 30, seat_top, hip[0] + 34, seat_top + th, 5, BENCHC)
        wcap(d, T, s, p_foot, p_head, th / 2, th / 2, BENCHC)
        wcap(d, T, s, p_foot, p_head, th / 2 - 3.2, th / 2 - 3.2, (136, 144, 166))
    xs = [p_head[0], p_foot[0], hip[0] + 34]
    ys = [p_head[1], p_foot[1]]
    return Gear(back=back, bounds=(min(xs) - 14, min(ys) - 10, max(xs) + 14, FLOOR))


def lever_to_wrist(pivot, w=5.0, grip=True):
    def mid(d, T, P, s):
        c = P["wrist"]
        wline(d, T, s, pivot, c, w, METAL_D)
        wcirc(d, T, s, pivot, w * 0.9, METAL)

    def front(d, T, P, s):
        c = P["wrist"]
        if grip:
            wline(d, T, s, add(c, (-1.5, -0.7)), add(c, (3.0, 1.4)), 4.0, METAL)
            wcirc(d, T, s, add(c, (3.4, 1.6)), 3.6, METAL_D)
    return Gear(mid=mid, front=front)


# ============================================================================================================ BENCH PRESS
@pattern("bench_press", used=("incline", "decline", "single_arm", "seated", "standing", "lying"),
         demos=[("barbell", [], "chest"), ("barbell", ["incline"], "chest"), ("barbell", ["decline"], "chest"),
                ("dumbbell", [], "chest"), ("dumbbell", ["incline"], "chest"), ("machine", [], "chest"),
                ("cable", [], "chest"), ("band", [], "chest")])
def bench_press(eq, var, hil):
    inc, dec = has(var, "incline"), has(var, "decline")
    if eq == "machine" or has(var, "seated"):
        hip = (-82, -76)
        torso = -26 if inc else (-8 if not dec else -2)
        sh = add(hip, vup(torso, L["torso"]))
        A = body(hip=hip, torso=torso, hand_t=(26, 24), elbow_side=1)
        if inc:
            B = body(hip=hip, torso=torso, hand=(sh[0] + 78, sh[1] - 62), elbow_side=1)
        elif dec:
            B = body(hip=hip, torso=torso, hand=(sh[0] + 90, sh[1] + 46), elbow_side=1)
        else:
            B = body(hip=hip, torso=torso, hand=(sh[0] + 100, sh[1] + 20), elbow_side=1)
        pivot = (sh[0] - 56, sh[1] + 34)
        col = post(sh[0] - 56, pivot[1], FLOOR, w=8)
        seat = machine_seat(hip, torso, seat_len=(-26, 50), back_len=(-26, 84), base=(-70, 90))
        return spec([A, B], lever_to_wrist(pivot), gear(seat, col), hil)
    if eq in ("cable", "band"):
        hip = (0, -145)
        sh = (0 + 10, -145 - 90)
        kw = dict(hip=hip, torso=8, elbow_side=1)
        A = body(hand_t=(26, 20), **kw)
        sh = add(hip, vup(8, L["torso"]))
        B = body(hand=(sh[0] + 100, sh[1] + 22), **kw)
        if eq == "cable":
            equip = cable_station((-125, sh[1] + 10), "wrist", handle="d", face=-1)
        else:
            equip = band((-120, sh[1] + 10), "wrist")
        return spec([A, B], equip, None, hil)
    if inc:
        torso = -55
    elif dec:
        torso = -104
    else:
        torso = -90
    hip = (-102, -92 if dec else -76)
    sh = add(hip, vup(torso, L["torso"]))
    if eq == "dumbbell":
        low = dict(hand_t=(26, 16), elbow_side=1)
        equip = dumbbell("wrist", size=1.2)
        up = dict(hand_rel=(4, -102), elbow_side=1)
    else:
        low = dict(hand_t=(34, 18), elbow_side=1)
        equip = barbell("wrist", plate=22)
        up = dict(hand_rel=(4, -102), elbow_side=1)
    A = body(hip=hip, torso=torso, head=torso, **up)
    B = body(hip=hip, torso=torso, head=torso, **low)
    scene = pad_bench(hip, torso)
    if eq != "dumbbell":
        scene = gear(scene, rack_posts(sh[0] - 46, sh[1] - 92))
    if dec:
        def hook(d, T, P, s):
            a = P["ankle"]
            wcap(d, T, s, (a[0] + 4, a[1] - 14), (a[0] + 4, a[1] - 40), 5, 5, PAD)
        scene = gear(scene, Gear(back=hook))
    return spec([A, B], equip, scene, hil)


# ============================================================================================================ CHEST FLY
def _fly_arm(phi_deg, y=8, bend=0.0):
    """Arm swinging in the horizontal plane seen from the side: phi=0 forward, phi=90 towards the viewer."""
    c = math.cos(math.radians(phi_deg))
    return dict(elbow_rel=(L["uarm"] * c, y), hand_e=(L["farm"] * c * (1 - bend), y * 0.4))


@pattern("chest_fly", used=("seated", "standing", "incline", "lying"),
         demos=[("machine", [], "chest"), ("cable", [], "chest"), ("dumbbell", [], "chest")])
def chest_fly(eq, var, hil):
    if eq in ("machine",) or has(var, "seated"):
        hip = (-82, -76)
        torso = -8
        sh = add(hip, vup(torso, L["torso"]))
        A = body(hip=hip, torso=torso, elbow_rel=(24, 6), hand_e=(0, -46))
        B = body(hip=hip, torso=torso, elbow_rel=(54, 6), hand_e=(0, -46))
        # vertical lever shaft in front of the chest, forearm pad along the forearm
        px = sh[0] + 78

        def pads(d, T, P, s):
            e, w = P["elbow"], P["wrist"]
            wcap(d, T, s, add(e, (5, 0)), add(w, (5, 0)), 4.6, 4.6, PAD)
            wline(d, T, s, (px, sh[1] - 56), add(w, (5, 0)), 5, METAL_D)
        seat = machine_seat(hip, torso, seat_len=(-26, 50), back_len=(-26, 84), base=(-70, 120))
        col = post(px, sh[1] - 62, FLOOR, w=8)
        return spec([A, B], Gear(mid=pads), gear(seat, col), hil)
    if eq in ("dumbbell", "none", "kettlebell") or has(var, "lying", "incline"):
        return _fly_topdown(hil)
    hip = (0, -145)
    kw = dict(hip=hip, torso=8, elbow_side=1)
    sh = add(hip, vup(8, L["torso"]))
    A = body(**_fly_arm(70, 14), **kw)
    B = body(**_fly_arm(4, 14), **kw)
    if eq == "band":
        equip = band((-110, sh[1] + 10), "wrist")
    elif eq == "dumbbell":
        equip = dumbbell("wrist", size=1.1)
    else:
        equip = cable_station((-90, sh[1] - 56), "wrist", handle="d", face=-1)
    return spec([A, B], equip, None, hil)


# ============================================================================================================ PUSH-UP
@pattern("pushup", used=("incline", "decline", "kneeling", "narrow", "wide", "bodyweight"),
         demos=[("none", [], "chest"), ("none", ["incline"], "chest"), ("bench", [], "chest"),
                ("none", ["decline"], "chest"), ("none", ["kneeling"], "chest"), ("swiss_ball", [], "chest")])
def pushup(eq, var, hil):
    inc = has(var, "incline") or eq in ("bench", "box", "incline_bench")
    dec = has(var, "decline") or eq in ("swiss_ball", "decline_bench")
    knees = has(var, "kneeling", "knees", "knee")
    hand_h = 44.0 if inc else 0.0
    foot_h = 44.0 if (dec and eq != "swiss_ball") else (62.0 if eq == "swiss_ball" else 0.0)
    hand_y = FLOOR - hand_h - 5.4
    f = 62.0
    if knees:
        K = (0.0, FLOOR - 7.0)
        def make(shoulder_y):
            # body line from the knee
            sy = shoulder_y
            sin_a = max(-0.95, min(0.95, (K[1] - sy) / (L["thigh"] + L["torso"])))
            al = math.asin(sin_a)
            ang_t = 90 - math.degrees(al)
            ank = (K[0] - math.cos(math.radians(8)) * L["shin"], K[1] - math.sin(math.radians(8)) * L["shin"] * 1.0 - 1)
            sh = (K[0] + (L["thigh"] + L["torso"]) * math.cos(al), sy)
            return ank, ang_t, sh
        ank_top, t_top, sh_top = make(hand_y - 102)
        ank_bot, t_bot, sh_bot = make(hand_y - 26 - 4 - hand_h * 0)
        hx = sh_top[0]
        def pose(ank, tt, extra_sh):
            return body(ankle=ank, shin=ang_up(ank, K), thigh=tt, torso=tt, head=tt - 25, foot=95,
                        hand=(hx, hand_y), elbow_side=1)
        # thigh angle: the thigh follows the body line (knee -> hip), same angle as the torso
        A = pose(ank_top, t_top, sh_top)
        B = pose(ank_bot, t_bot, sh_bot)
    else:
        toe_y = FLOOR - foot_h - 5.4
        ank = (0.0, toe_y - math.sin(math.radians(f)) * L["foot"])
        ank = (0.0, ank[1])
        total = L["thigh"] + L["shin"] - 1.0 + L["torso"]

        def make(shoulder_y):
            sin_a = max(-0.95, min(0.95, (ank[1] - shoulder_y) / total))
            al = math.asin(sin_a)
            dirv = (math.cos(al), -math.sin(al))
            hip = (ank[0] + dirv[0] * (L["thigh"] + L["shin"] - 1.0), ank[1] + dirv[1] * (L["thigh"] + L["shin"] - 1.0))
            return hip, 90 - math.degrees(al), (hip[0] + dirv[0] * L["torso"], hip[1] + dirv[1] * L["torso"])
        hip_t, t_t, sh_t = make(hand_y - 102)
        hip_b, t_b, sh_b = make(hand_y - 25 - (hand_h * 0))
        hx = sh_t[0]
        A = body(ankle=ank, hip=hip_t, torso=t_t, head=t_t - 30, foot=f, hand=(hx, hand_y), elbow_side=1)
        B = body(ankle=ank, hip=hip_b, torso=t_b, head=t_b - 30, foot=f, hand=(hx, hand_y), elbow_side=1)
    parts = []
    if inc:
        parts.append(flat_bench(hx - 14, hx + 120, FLOOR - hand_h, 12))
    if dec and eq != "swiss_ball":
        parts.append(flat_bench(-96, 24, FLOOR - foot_h, 12))
    if eq == "swiss_ball":
        parts.append(swiss_ball(-6, 31))
    if eq == "mat":
        parts.append(mat(-120, hx + 120, 3))
    return spec([A, B], None, gear(*parts) if parts else None, hil)


# ============================================================================================================ SHOULDER PRESS
@pattern("shoulder_press", used=("seated", "standing", "single_arm", "alternating", "front", "overhead"),
         demos=[("barbell", ["standing"], "shoulders"), ("barbell", ["seated"], "shoulders"),
                ("dumbbell", ["seated"], "shoulders"), ("dumbbell", ["standing"], "shoulders"),
                ("machine", [], "shoulders"), ("kettlebell", [], "shoulders"), ("cable", [], "shoulders"),
                ("band", [], "shoulders")])
def shoulder_press(eq, var, hil):
    if eq not in ("barbell", "sz_bar", "dumbbell", "kettlebell", "machine", "cable", "band"):
        eq = "dumbbell" if eq in ("bench", "incline_bench", "box") else "none"
    seated = has(var, "seated") or eq == "machine" or (eq == "dumbbell" and not has(var, "standing"))
    low = dict(hand_t=(-6, 14), elbow_side=1)
    up = dict(hand_rel=(4, -103), elbow_side=1)
    equip, scene = None, None
    if seated:
        hip = (-78, -72)
        torso = -8
        kw = dict(hip=hip, torso=torso)
        # upright adjustable bench: back pad along the torso, seat, frame
        t = vup(torso)
        nrm = (math.cos(math.radians(torso)), math.sin(math.radians(torso)))
        pf = add(add(hip, mul(t, -22)), mul(nrm, -20.5))
        pt_ = add(add(hip, mul(t, L["torso"] + 34)), mul(nrm, -20.5))
        scene = adj_bench(pf, pt_, hip[0] - 34, hip[0] + 44, hip[1] + 14.5, th=12)
    else:
        kw = dict(hip=(0, -145), torso=0)
    if eq == "machine":
        sh = add(hip, vup(torso, L["torso"]))
        A = body(**kw, hand_t=(-4, 17), elbow_side=1)
        B = body(**kw, hand=(sh[0] + 6, sh[1] - 100), elbow_side=1)
        pivot = (sh[0] - 54, sh[1] - 112)
        col = post(sh[0] - 54, pivot[1], FLOOR, w=8)
        machine = machine_seat(hip, torso, seat_len=(-26, 50), back_len=(-26, 90), base=(-70, 90))
        return spec([A, B], lever_to_wrist(pivot), gear(machine, col), hil)
    if eq in ("barbell", "sz_bar"):
        equip = barbell("wrist", plate=22)
    elif eq == "dumbbell":
        equip = dumbbell("wrist", size=1.2)
    elif eq == "kettlebell":
        equip = kettlebell("wrist", drop=(-0.3, 0.95))
    elif eq == "cable":
        equip = cable_station((-70, -16), "wrist", handle="d", face=-1)
    elif eq == "band":
        equip = band((6, FLOOR - 2), "wrist")
    A = body(**kw, **low)
    B = body(**kw, **up)
    return spec([A, B], equip, scene, hil)


# ============================================================================================================ FRONT RAISE
@pattern("front_raise", used=("standing", "alternating", "single_arm", "seated"),
         demos=[("dumbbell", [], "shoulders"), ("barbell", [], "shoulders"), ("cable", [], "shoulders"),
                ("band", [], "shoulders"), ("none", [], "shoulders")])
def front_raise(eq, var, hil):
    kw = dict(hip=(0, -145), torso=0)
    A = body(**kw, uarm=7, farm=9)
    B = body(**kw, uarm=93, farm=96)
    equip = None
    if eq in ("barbell", "sz_bar"):
        equip = barbell("wrist", plate=16)
    elif eq in ("dumbbell",):
        equip = dumbbell("wrist", size=1.2)
    elif eq == "kettlebell":
        equip = kettlebell("wrist")
    elif eq == "cable":
        equip = cable_station((-66, -16), "wrist", handle="bar", face=-1)
    elif eq == "band":
        equip = band((8, FLOOR - 2), "wrist")
    return spec([A, B], equip, None, hil)


# ============================================================================================================ REAR DELT FLY
@pattern("rear_delt_fly", used=("seated", "standing", "lying", "incline", "bent", "single_arm"),
         demos=[("machine", [], "shoulders"), ("cable", [], "shoulders"), ("dumbbell", [], "shoulders")])
def rear_delt_fly(eq, var, hil):
    if eq == "machine" or has(var, "seated"):
        hip = (-70, -70)
        torso = 10
        sh = add(hip, vup(torso, L["torso"]))
        A = body(hip=hip, torso=torso, **_fly_arm(2, 4))
        B = body(hip=hip, torso=torso, **_fly_arm(105, 4))
        px = sh[0] + 112
        chest = Gear(back=lambda d, T, P, s: (wrect(d, T, s, sh[0] + 36, sh[1] + 30, sh[0] + 44, FLOOR - 4, 2, METAL_D),
                                              wrect(d, T, s, sh[0] + 6, FLOOR - 5, sh[0] + 70, FLOOR, 2, METAL_D),
                                              wcap(d, T, s, (sh[0] + 34, sh[1] - 12), (sh[0] + 38, sh[1] + 40), 7, 7, PAD)))

        def grips(d, T, P, s):
            c = P["wrist"]
            wcap(d, T, s, add(c, (0, -9)), add(c, (0, 9)), 3.4, 3.4, METAL)
        seat = flat_bench(hip[0] - 20, hip[0] + 44, hip[1] + 14.5, 11)
        return spec([A, B], Gear(mid=grips), gear(seat, chest), hil)
    if eq in ("cable", "band"):
        hip = (0, -145)
        kw = dict(hip=hip, torso=4)
        sh = add(hip, vup(4, L["torso"]))
        A = body(**_fly_arm(2, 4), **kw)
        B = body(**_fly_arm(105, 4), **kw)
        if eq == "cable":
            equip = cable_station((112, sh[1] - 4), "wrist", handle="rope", face=1)
        else:
            equip = band((112, sh[1] - 4), "wrist")
        return spec([A, B], equip, None, hil)
    if has(var, "lying", "incline", "prone"):
        # chest supported on an inclined pad (prone): arms hang, then rise sideways (they shrink up to the shoulder)
        hip = (-34, -140)
        torso = 50
        nrm = (math.cos(math.radians(torso)), math.sin(math.radians(torso)))
        t = vup(torso)
        sh_ = add(hip, vup(torso, L["torso"]))
        p0 = add(add(hip, mul(t, 18)), mul(nrm, 22))
        p1 = add(add(hip, mul(t, L["torso"] + 6)), mul(nrm, 22))

        def padgear(d, T, P, s):
            wline(d, T, s, (p1[0] + 10, p1[1] + 6), (p1[0] + 10, FLOOR - 4), 5.5, METAL_D)
            wline(d, T, s, (p0[0] + 8, p0[1] + 4), (p0[0] + 8, FLOOR - 4), 5.5, METAL_D)
            wrect(d, T, s, p0[0] - 14, FLOOR - 5, p1[0] + 28, FLOOR, 2, METAL_D)
            wcap(d, T, s, p0, p1, 6.5, 6.5, PAD)
        A = body(hip=hip, torso=torso, head=34, elbow_rel=(0, 53), hand_e=(2, 51))
        B = body(hip=hip, torso=torso, head=34, elbow_rel=(-2, 10), hand_e=(-4, 7))
        eq_g = dumbbell("wrist", size=1.2) if eq != "none" else None
        return spec([A, B], eq_g, Gear(back=padgear, bounds=(p0[0] - 14, p1[1] - 10, p1[0] + 30, FLOOR)), hil)
    # bent-over dumbbell: arms hang down, then rise sideways (seen from the side they shrink up to the shoulder)
    hip = (-62, -110)
    torso = 62
    A = body(hip=hip, torso=torso, elbow_rel=(0, 50), hand_e=(2, 50))
    B = body(hip=hip, torso=torso, elbow_rel=(-2, 10), hand_e=(-4, 7))
    return spec([A, B], dumbbell("wrist", size=1.2) if eq != "none" else None, None, hil)


# ============================================================================================================ TRICEPS EXTENSION
@pattern("triceps_extension", used=("lying", "seated", "standing", "overhead", "single_arm", "kickback", "incline"),
         demos=[("sz_bar", ["lying"], "triceps"), ("dumbbell", ["lying"], "triceps"), ("dumbbell", ["overhead"], "triceps"),
                ("dumbbell", ["seated"], "triceps"), ("cable", ["overhead"], "triceps"), ("dumbbell", ["kickback"], "triceps"),
                ("barbell", ["overhead"], "triceps")])
def triceps_extension(eq, var, hil):
    if eq == "machine":
        hip = (-76, -70)
        torso = -4
        sh = add(hip, vup(torso, L["torso"]))
        kw = dict(hip=hip, torso=torso, uarm=8, head=torso)
        A = body(farm=120, **kw)
        B = body(farm=10, **kw)
        pivot = (sh[0] + 66, sh[1] - 30)
        mach = machine_seat(hip, torso, seat_len=(-26, 50), back_len=(-26, 84), base=(-70, 110))
        col = post(pivot[0], pivot[1], FLOOR, w=8)
        return spec([A, B], lever_to_wrist(pivot, grip=True), gear(mach, col), hil)
    if has(var, "kickback", "bent"):
        hip = (-58, -122)
        torso = 62
        kw = dict(hip=hip, torso=torso, head=44)
        A = body(uarm=-80, farm=5, **kw)
        B = body(uarm=-90, farm=-92, **kw)
        # the free hand rests on a bench
        bench = flat_bench(-20, 90, FLOOR - 62, 12)
        return spec([A, B], dumbbell("wrist", size=1.1), None, hil)
    if eq in ("barbell", "sz_bar", "dumbbell") and has(var, "lying", "decline", "incline") or (
            has(var, "lying") and eq not in ("cable",)):
        hip = (-102, -76)
        torso = -55 if has(var, "incline") else -90
        # upper arm vertical (slightly back), forearm swings towards the head
        kw = dict(hip=hip, torso=torso, head=torso)
        A = body(uarm=188, farm=190, **kw)
        B = body(uarm=188, farm=292, **kw)
        if eq in ("barbell", "sz_bar"):
            equip = barbell("wrist", plate=16, sz=(eq == "sz_bar"))
        elif eq == "none":
            equip = None
        else:
            equip = dumbbell("wrist", size=1.2)
        return spec([A, B], equip, pad_bench(hip, torso), hil)
    seated = has(var, "seated")
    if seated:
        hip = (-76, -70)
        torso = -4
        t = vup(torso)
        nrm = (math.cos(math.radians(torso)), math.sin(math.radians(torso)))
        pf = add(add(hip, mul(t, -22)), mul(nrm, -20.5))
        pt_ = add(add(hip, mul(t, L["torso"] + 30)), mul(nrm, -20.5))
        scene = adj_bench(pf, pt_, hip[0] - 34, hip[0] + 44, hip[1] + 14.5, th=12)
        kw = dict(hip=hip, torso=torso)
    else:
        kw = dict(hip=(0, -145), torso=0)
        scene = None
    A = body(uarm=186, farm=186, **kw)
    B = body(uarm=186, farm=296, **kw)
    if eq == "cable":
        equip = cable_station((-62, -18), "wrist", handle="rope", face=-1)
    elif eq == "band":
        equip = band((-8, FLOOR - 2), "wrist")
    elif eq in ("barbell", "sz_bar"):
        equip = barbell("wrist", plate=16, sz=(eq == "sz_bar"))
    elif eq == "kettlebell":
        equip = kettlebell("wrist", drop=(0, 1))
    elif eq == "none":
        equip = None
    else:
        equip = dumbbell("wrist", size=1.2)
    return spec([A, B], equip, scene, hil)


# ============================================================================================================ TRICEPS PUSHDOWN
@pattern("triceps_pushdown", used=("reverse", "single_arm", "standing", "seated"),
         demos=[("cable", [], "triceps"), ("cable", ["reverse"], "triceps"), ("cable", ["single_arm"], "triceps"),
                ("band", [], "triceps"), ("machine", [], "triceps")])
def triceps_pushdown(eq, var, hil):
    kw = dict(hip=(0, -145), torso=7, head=2)
    A = body(uarm=6, farm=118, **kw)
    B = body(uarm=6, farm=9, **kw)
    px, py = 88, -296
    if eq == "band":
        equip = band((52, -300), "wrist")
    else:
        handle = "strap" if has(var, "single_arm") else ("bar" if has(var, "reverse") or eq != "cable" else "rope")
        if has(var, "reverse"):
            handle = "bar"
        elif not has(var, "single_arm"):
            handle = "rope"
        equip = cable_station((px, py), "wrist", handle=handle, face=1)
    return spec([A, B], equip, None, hil)


# ============================================================================================================ DIP
@pattern("dip", used=("bodyweight", "narrow", "reverse", "seated"),
         demos=[("bar", [], "triceps"), ("none", [], "chest"), ("bench", [], "triceps"), ("machine", [], "triceps")])
def dip(eq, var, hil):
    if eq in ("bench", "box", "incline_bench") or has(var, "reverse"):
        # bench dips: hands on the bench behind, feet forward on the floor
        top = FLOOR - 66
        bx = -58
        hand = (bx, top - 6)
        ank = (62, 0)
        sy_top = hand[1] - 100
        kw = dict(ankle=ank, knee_side=1, elbow_side=1)
        A = body(hip=(bx - 6 + 3, sy_top + L["torso"]), torso=-2, head=-6, hand=hand, **kw)
        sy_bot = hand[1] - 40
        B = body(hip=(bx - 8 + 14, sy_bot + L["torso"] * 0.98), torso=-6, head=-8, hand=hand, **kw)
        scene = flat_bench(bx - 40, bx + 24, top, 12)
        return spec([A, B], None, scene, hil)
    bar_mid = (0.0, -196.0)
    sy_top, sy_bot = bar_mid[1] - 98, bar_mid[1] - 40

    def mk(sy, lean):
        sh = (bar_mid[0] - 2 + lean * 0.4, sy)
        hip = (sh[0] - vup(lean, L["torso"])[0], sh[1] - vup(lean, L["torso"])[1])
        return body(hip=hip, torso=lean, head=lean - 12, thigh=-6, shin=62, foot=84, hand=bar_mid, elbow_side=1)
    A = mk(sy_top, 10)
    B = mk(sy_bot, 26)
    return spec([A, B], None, dip_bars(bar_mid), hil)


# ============================================================================================================ FRONT-VIEW PATTERNS
def _fly_topdown(hil):
    """Lying dumbbell fly seen from above (head up): the arms open sideways in the picture plane."""
    pel = (0, -20)
    common = dict(pelvis=pel, leg_l=(14, 4), leg_r=(14, 4), sc_leg=(0.34, 0.34), foot_out=8)
    A = fpose(arm_l=(70, 90), arm_r=(70, 90), sc_arm=(0.2, 0.2), **common)
    B = fpose(arm_l=(92, 120), arm_r=(92, 120), sc_arm=(1.0, 1.0), **common)

    def pad(d, T, P, s):
        px, py = pel
        wrect(d, T, s, px - 30, py - 142, px + 30, py + 34, 8, BENCHC)
        wrect(d, T, s, px - 25, py - 137, px + 25, py + 29, 6, (136, 144, 166))
    sc = Gear(back=pad, bounds=(pel[0] - 34, pel[1] - 146, pel[0] + 34, pel[1] + 100))
    return spec([A, B], front_dumbbells(1.1, axis="y"), sc, hil, floor=False, margin=(20, 14))


@pattern("lateral_raise", used=("seated", "standing", "single_arm", "alternating", "bent", "reverse"),
         demos=[("dumbbell", [], "shoulders"), ("dumbbell", ["single_arm"], "shoulders"), ("cable", [], "shoulders"),
                ("band", [], "shoulders"), ("machine", [], "shoulders")])
def lateral_raise(eq, var, hil):
    single = has(var, "single_arm")
    low = (10, 14)
    high = (86, 74)
    common = dict(leg_l=(3, 3), leg_r=(3, 3), foot_out=10)
    if single:
        A = fpose(arm_l=(6, 8), arm_r=low, **common)
        B = fpose(arm_l=(6, 8), arm_r=high, **common)
        which = ("r",)
    else:
        A = fpose(arm_l=low, arm_r=low, **common)
        B = fpose(arm_l=high, arm_r=high, **common)
        which = ("l", "r")
    equip = None
    if eq == "cable":
        A = fpose(arm_l=(6, 8), arm_r=low, **common)
        B = fpose(arm_l=(6, 8), arm_r=high, **common)
        equip = cable_station((-64, -16), "wr_r", handle="d", face=-1)
    elif eq == "band":
        equip = gear(band((-8, FLOOR - 3), "wr_l"), band((8, FLOOR - 3), "wr_r"))
    elif eq == "machine":
        def pads(d, T, P, s):
            for sd in ("l", "r"):
                wcap(d, T, s, P["el_" + sd], P["wr_" + sd], 5.2, 5.2, PAD)
        equip = Gear(mid=pads)
    else:
        equip = front_dumbbells(1.1, which=which)
    return spec([A, B], equip, None, hil)


@pattern("side_leg_raise", used=("lying", "standing", "side", "single_arm", "seated"),
         demos=[("none", [], "glutes"), ("band", ["standing"], "glutes"), ("cable", ["standing"], "glutes"),
                ("none", ["standing"], "glutes"), ("machine", [], "glutes")])
def side_leg_raise(eq, var, hil):
    if eq == "machine" or has(var, "seated"):
        # hip abduction machine seen from the front: knees open sideways
        py = -76
        common = dict(pelvis=(0, py), arm_l=(30, 70), arm_r=(30, 70), foot_out=8, sc_leg=(1.0, 1.0))
        A = fpose(leg_l=(90, 4), leg_r=(90, 4), sc_thigh=(0.2, 0.2), **common)
        B = fpose(leg_l=(90, 14), leg_r=(90, 14), sc_thigh=(0.78, 0.78), **common)

        def seatg(d, T, P, s):
            wrect(d, T, s, -34, py + 6, 34, py + 20, 6, PAD)
            wrect(d, T, s, -5, py + 20, 5, FLOOR - 4, 1, METAL_D)
            wrect(d, T, s, -34, FLOOR - 5, 34, FLOOR, 2, METAL_D)

        def pads(d, T, P, s):
            for sd, sg in (("l", -1), ("r", 1)):
                k = P["kn_" + sd]
                wcap(d, T, s, (k[0] + sg * 9, k[1] - 17), (k[0] + sg * 9, k[1] + 17), 6, 6, PAD)
        return spec([A, B], Gear(front=pads), Gear(back=seatg, bounds=(-40, py, 40, FLOOR)), hil)
    if has(var, "standing") or eq == "cable" and not has(var, "lying"):
        common = dict(arm_l=(18, 56), arm_r=(18, 56), foot_out=10)
        A = fpose(leg_l=(0, 0), leg_r=(1, 1), **common)
        B = fpose(leg_l=(0, 0), leg_r=(34, 34), **common)
        equip = None
        if eq == "cable":
            equip = cable_station((-62, -16), "an_r", handle="strap", face=-1)
        elif eq == "band":
            equip = band((-70, FLOOR - 3), "an_r")
        return spec([A, B], equip, None, hil)
    py = FLOOR - 21
    common = dict(rot=-90, pelvis=(0, py), arm_l=(172, 172), arm_r=(-70, -88), sc_arm=(1.0, 0.42), foot_out=-4)
    A = fpose(leg_l=(0, 0), leg_r=(0, 1), **common)
    B = fpose(leg_l=(0, 0), leg_r=(38, 38), **common)
    scene = mat(-200, 190, 3) if eq in ("mat",) else None
    equip = None
    if eq == "band":
        def cuff(d, T, P, s):
            for k in ("kn_r",):
                wline(d, T, s, add(P[k], (-1, 5)), add(P[k], (-1, -5)), 4, BANDC)
        equip = Gear(front=cuff)
    return spec([A, B], equip, scene, hil)
