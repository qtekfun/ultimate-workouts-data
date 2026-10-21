"""Gait / cardio machines / rotations / chops / landmine / single-leg and front-view squat drills (agent q).

Patterns (all keys specs rendered by extras_b.render_spec, conventions as patterns_b.py):
  q_gait (walk, alternate, retro, buttkick), q_elliptical, q_skierg, q_rotation (machine, cable, landmine),
  q_chop (front, reverse, cable), q_landmine_press, q_sidesquat (lateral, horse, dragon, slide),
  q_shrimp, q_thruster (barbell / dumbbell), q_boxjump.
"""
import math
try:
    from . import extras_b as X
except ImportError:  # pragma: no cover
    import extras_b as X

mk = X.mk
SS = X.SS
PATTERNS = {}
TEST_VARIANTS = {}
LEN = X.LEN
TICKC = (168, 176, 196)


def pat(name, *tests):
    def deco(fn):
        PATTERNS[name] = fn
        TEST_VARIANTS[name] = list(tests) or [("none", [], None)]
        return fn
    return deco


def spec(keys, equipment=None, scene=None, front=None, hilite=None, **kw):
    d = dict(keys=keys, rotation=0.0, equipment=equipment, scene=scene, front=front, hilite=hilite)
    d.setdefault("frame_ms", 90)
    d.update(kw)
    return d


def has(var, *names):
    return any(n in var for n in names)


def vup(a, n=1.0):
    return X.vup(a, n)


def add(p, q):
    return (p[0] + q[0], p[1] + q[1])


def sh_of(hip, torso):
    return add(hip, vup(torso, LEN["torso"]))


# --------------------------------------------------------------------------------------------- scene items
def floor_ticks(per_cycle=126.0, spacing=63.0, dirn=-1):
    """Marks on the floor that scroll with the gait phase stored in J['hand_pt'] - J['wrist'] (cos, sin of the phase)."""
    def fn(d, T, J, s):
        k = s * SS
        v = (J["hand_pt"][0] - J["wrist"][0], J["hand_pt"][1] - J["wrist"][1])
        frac = math.atan2(v[1], v[0]) / (2 * math.pi)
        off = dirn * frac * per_cycle
        x = -400 + (off % spacing)
        while x < 400:
            ax, ay = T((x, 0))
            d.rectangle([ax, ay + 1.5 * SS, ax + 10 * k, ay + 4.5 * SS], fill=TICKC)
            x += spacing
    return X.Item(fn, lambda J: [])


def treadmill(deck_h=9.0, x0=-130, x1=118, rail_y=-156, rail_x0=18, dirn=-1, per_cycle=126.0, spacing=63.0):
    """Treadmill: raised deck with a scrolling belt, post and console, handrail at rail_y."""
    def fn(d, T, J, s):
        k = s * SS
        a, b = T((x0, -deck_h)), T((x1, 0))
        d.rounded_rectangle([a[0], a[1], b[0], b[1]], radius=3 * k, fill=X.METAL_D)
        a2, b2 = T((x0 + 8, -deck_h)), T((x1 - 8, -deck_h + 3))
        d.rounded_rectangle([a2[0], a2[1], b2[0], b2[1]], radius=1.5 * k, fill=X.RUBBER)
        v = (J["hand_pt"][0] - J["wrist"][0], J["hand_pt"][1] - J["wrist"][1])
        frac = math.atan2(v[1], v[0]) / (2 * math.pi)
        off = dirn * frac * per_cycle
        x = x0 + 14 + (off % spacing)
        while x < x1 - 20:
            p, q = T((x, -deck_h)), T((x + 9, -deck_h + 3))
            d.rectangle([p[0], p[1], q[0], q[1]], fill=(150, 156, 178))
            x += spacing
        # post + console
        p, q = T((x1 - 24, -rail_y + 0 if False else -190)), T((x1 - 8, -deck_h))
        d.rounded_rectangle([p[0], p[1], q[0], q[1]], radius=2 * k, fill=X.BENCHC)
        c0, c1 = T((x1 - 42, -212)), T((x1 + 6, -190))
        d.rounded_rectangle([c0[0], c0[1], c1[0], c1[1]], radius=4 * k, fill=X.EQUIP)
        s0, s1 = T((x1 - 36, -207)), T((x1 - 6, -196))
        d.rounded_rectangle([s0[0], s0[1], s1[0], s1[1]], radius=2 * k, fill=(170, 220, 200))
        r0, r1 = T((rail_x0, rail_y - 3)), T((x1 - 12, rail_y + 3))
        d.rounded_rectangle([r0[0], r0[1], r1[0], r1[1]], radius=3 * k, fill=X.METAL)
    return X.Item(fn, lambda J: [(x0, -214), (x1 + 8, 0)])


# --------------------------------------------------------------------------------------------- GAIT
def gait_kw(u, hip_y=-146.0, stance=0.62, lift=28.0, stride=76.0, torso=3.0, arm_amp=30.0, arm_bend=14.0, hop=0.0,
            floor=-6.0, foot_down=30.0, rev=False, rail=None, kh=(1, 0.2), arm_scale=1.0, straight=False):
    """Two legs half a cycle apart (treadmill style: the body stays at x = 0 while the stance foot slides back)."""
    def foot(phase):
        phase %= 1.0
        if phase < stance:
            t = phase / stance
            return (stride * (0.5 - t), floor), 0.0, False
        t = (phase - stance) / (1 - stance)
        x = stride * (-0.5 + t)
        y = floor - lift * math.sin(math.pi * t) ** 1.2
        return (x, y), (foot_down * math.sin(math.pi * min(1, t * 1.15)) if t < 0.87 else 0.0), True
    p = -u if rev else u
    f1, a1, s1 = foot(p)
    f2, a2, s2 = foot(p + 0.5)
    hy = hip_y - (hop if (s1 or s2) else 0.0)
    hip = (0.0, hy)
    kw = dict(A=(f1[0], f1[1]), A2=(f2[0], f2[1]), hip=hip, torso=torso, head=torso * 0.5, kh=kh, kh2=kh,
              foot=a1, foot2=a2)
    c = math.cos(2 * math.pi * u)
    if rail is not None:
        kw.update(W=rail, W2=(rail[0] + 2, rail[1]), ah=(0, 1), ah2=(0, 1))
    elif straight:
        kw.update(uarm=-arm_amp * c * arm_scale, farm=-arm_amp * c * arm_scale * 1.1,
                  FA=(arm_amp * c * arm_scale, arm_amp * c * arm_scale * 1.1))
    else:
        ua = -arm_amp * c * arm_scale
        kw.update(uarm=ua, farm=ua + arm_bend, FA=(-ua, -ua + arm_bend))
    kw["hand"] = (math.cos(2 * math.pi * u), math.sin(2 * math.pi * u))
    return kw


@pat("q_gait", ("none", ["walk"], "quads"), ("none", ["alternate"], "calves"), ("none", ["retro"], "hamstrings"),
     ("none", ["buttkick"], "hamstrings"))
def q_gait(eq, var, hil):
    if has(var, "buttkick"):
        return _butt_kicks(hil or "hamstrings")
    if has(var, "retro"):
        # backward walk on a treadmill, hands on the handrail
        rail = (34.0, -156.0)
        keys = [gait_kw(i / 8.0, hip_y=-155.0, stance=0.6, lift=26, stride=58, torso=7, rev=True, floor=-15.0,
                        rail=rail, foot_down=10) for i in range(8)]
        for kk in keys:
            kk["foot"] = -kk["foot"] * 0.5
            kk["foot2"] = -kk["foot2"] * 0.5
        sc = treadmill(dirn=+1)
        return spec(keys, sc, None, hilite=hil or "hamstrings", loop="cycle", linear=True, steps=3, frame_ms=80)
    if has(var, "alternate"):
        # exaggerated alternating step: long stride, high knee drive, opposite arm swing
        keys = [gait_kw(i / 8.0, hip_y=-141.0, stance=0.5, lift=48, stride=92, torso=4, arm_amp=40, arm_bend=26,
                        foot_down=34, kh=(1, 0.05)) for i in range(8)]
        return spec(keys, None, floor_ticks(per_cycle=184.0, spacing=92.0), hilite=hil or "calves", loop="cycle",
                    linear=True, steps=3, frame_ms=80)
    keys = [gait_kw(i / 8.0, hip_y=-146.0, stance=0.62, lift=26, stride=78, torso=3, arm_amp=28, arm_bend=16,
                    hop=0, foot_down=34) for i in range(8)]
    return spec(keys, None, floor_ticks(per_cycle=126.0, spacing=63.0), hilite=hil or "quads", loop="cycle",
                linear=True, steps=3, frame_ms=80)


def _butt_kicks(hil):
    def pose(near_kick, hop=0.0):
        hip = (0.0, -150.0 - hop)
        kw = dict(hip=hip, torso=4, head=2, kh=(1, 0.1), kh2=(1, 0.1), foot=0, foot2=0)
        kick = (-30.0, hip[1] + 22)
        down = (4.0, -6.0)
        if near_kick is None:
            kw["A"], kw["A2"] = (-4.0, -26.0), (8.0, -28.0)
            kw["foot"] = kw["foot2"] = 25
            kw.update(uarm=0, farm=70, FA=(0, 70))
        elif near_kick:
            kw["A"], kw["A2"] = kick, down
            kw["foot"] = 80
            kw.update(uarm=30, farm=100, FA=(-30, 40))
        else:
            kw["A"], kw["A2"] = down, kick
            kw["foot2"] = 80
            kw.update(uarm=-30, farm=40, FA=(30, 100))
        return kw
    keys = [pose(True), pose(None, 8), pose(False), pose(None, 8)]
    return spec(keys, None, None, hilite=hil, loop="cycle", linear=False, steps=5)


# --------------------------------------------------------------------------------------------- ELLIPTICAL
def _ell_phase(phi, hx=22.0):
    """Ankle on the pedal for phase phi (radians): flat ellipse tilted slightly."""
    x = hx + 34 * math.cos(phi)
    y = -52.0 - 15 * math.sin(phi) * 1.0
    return (x, y)


@pat("q_elliptical", ("none", [], "glutes"))
def q_elliptical(eq, var, hil):
    hx = 22.0
    P = (80.0, -150.0)   # handle pivot
    HL = 80.0            # handle length above the pivot
    LL = 40.0            # handle tail below the pivot

    def handle_top(th):
        return (P[0] + math.sin(math.radians(th)) * HL, P[1] - math.cos(math.radians(th)) * HL)

    keys = []
    for i in range(8):
        phi = 2 * math.pi * i / 8
        a1 = _ell_phase(phi, hx)
        a2 = _ell_phase(phi + math.pi, hx)
        th = -18 * math.cos(phi)       # near handle swings back when near foot is forward
        W = handle_top(th)
        W2 = handle_top(-th)
        kw = dict(A=a1, A2=a2, hip=(hx - 2, -183.0), torso=5, head=3, kh=(1, 0.0), kh2=(1, 0.0),
                  foot=2, foot2=2, W=W, W2=W2, ah=(0, 1), ah2=(0, 1), hand=(math.cos(phi), math.sin(phi)))
        keys.append(kw)

    def pedal(near):
        def fn(d, T, J, s):
            k = s * SS
            A = J["ankle" if near else "ankle2"]
            v = (J["hand_pt"][0] - J["wrist"][0], J["hand_pt"][1] - J["wrist"][1])
            phi = math.atan2(v[1], v[0]) + (0 if near else math.pi)
            th = -18 * math.cos(phi)
            L = (P[0] - math.sin(math.radians(th)) * LL, P[1] + math.cos(math.radians(th)) * LL)
            top = handle_top(th)
            col = X.METAL_D if near else X.METAL
            # pedal platform
            a, b = T((A[0] - 20, A[1] + 5)), T((A[0] + 40, A[1] + 12))
            d.rounded_rectangle([a[0], a[1], b[0], b[1]], radius=3 * k, fill=X.EQUIP if near else X.METAL_D)
            # link from the pedal front to the handle tail
            X.capsule(d, T((A[0] + 38, A[1] + 8)), T(L), 2.6 * k, 2.6 * k, col)
            # handle
            X.capsule(d, T(L), T(top), 3.4 * k, 3.4 * k, col)
            X.disc(d, T(P), 5 * k, X.EQUIP)
            X.disc(d, T(top), 4.6 * k, X.RUBBER)
        return X.Item(fn, lambda J: [(J["ankle"][0] - 22, J["ankle"][1]), (P[0] + 12, P[1] - HL - 6)])

    def body(d, T, J, s):
        k = s * SS
        # base frame on the floor, front column up to the pivot, console above
        a, b = T((-70, -9)), T((125, 0))
        d.rounded_rectangle([a[0], a[1], b[0], b[1]], radius=3 * k, fill=X.METAL_D)
        # rear flywheel housing
        c = T((-52, -34))
        X.disc(d, c, 30 * k, X.BENCHC)
        X.disc(d, c, 12 * k, X.METAL)
        p, q = T((P[0] - 8, P[1] - 4)), T((P[0] + 10, -9))
        d.rounded_rectangle([p[0], p[1], q[0], q[1]], radius=2 * k, fill=X.BENCHC)
        # console on a short stem above the pivot
        p, q = T((P[0] - 3, -250)), T((P[0] + 5, P[1] - 4))
        d.rectangle([p[0], p[1], q[0], q[1]], fill=X.BENCHC)
        c0, c1 = T((P[0] - 14, -270)), T((P[0] + 22, -246))
        d.rounded_rectangle([c0[0], c0[1], c1[0], c1[1]], radius=4 * k, fill=X.EQUIP)
        s0, s1 = T((P[0] - 9, -265)), T((P[0] + 17, -252))
        d.rounded_rectangle([s0[0], s0[1], s1[0], s1[1]], radius=2 * k, fill=(170, 220, 200))
    scene = X.many(X.Item(body, lambda J: [(-84, -270), (130, 0)]), pedal(False))
    return spec(keys, pedal(True), scene, hilite=hil or "glutes", loop="cycle", linear=True, steps=3)


# --------------------------------------------------------------------------------------------- SKI ERGOMETER
@pat("q_skierg", ("none", [], "lats"))
def q_skierg(eq, var, hil):
    TX = 74.0
    PUL = (50.0, -300.0)

    def pose(hip, torso, W, ah=(0, 1), A=(0.0, -6.0), foot=0.0, kh=(1, 0.1)):
        return dict(A=A, hip=hip, torso=torso, head=torso * 0.6, W=W, W2=(W[0] - 3, W[1] + 2), ah=ah, ah2=ah,
                    kh=kh, foot=foot)
    top = pose((0, -152), 0, (28, -310), A=(0, -10), foot=22)
    # crunch down: hands drive to the knees
    mid = pose((-22, -126), 30, (36, -196), kh=(1, 0.2))
    low = pose((-40, -98), 62, (-8, -78), ah=(-1, 0.4), kh=(1, 0.0))
    keys = [top, mid, low, mid]

    def machine(d, T, J, s):
        k = s * SS
        a, b = T((-40, -6)), T((TX + 24, 0))
        d.rounded_rectangle([a[0], a[1], b[0], b[1]], radius=3 * k, fill=X.METAL_D)
        p, q = T((TX - 12, -312)), T((TX + 12, -6))
        d.rounded_rectangle([p[0], p[1], q[0], q[1]], radius=4 * k, fill=X.BENCHC)
        c = T((TX, -316))
        X.disc(d, c, 34 * k, X.BENCHC)
        X.disc(d, c, 21 * k, X.EQUIP)
        X.disc(d, c, 8 * k, X.METAL)
        X.disc(d, T(PUL), 5 * k, X.METAL)
    cords = X.many(X.cable_line(PUL, anchor="wrist2", handle="d"), X.cable_line(PUL, anchor="wrist", handle="d"))
    return spec(keys, cords, X.Item(machine, lambda J: [(-46, -352), (TX + 30, 0)]), hilite=hil or "lats",
                loop="cycle", linear=False, steps=5)


# --------------------------------------------------------------------------------------------- top-view cue
def top_inset(angle_of, offset=(120.0, -120.0), anchor="hip", amp=1.0):
    """Tiny top-down icon: hips (grey) and shoulders (orange) with the nose; the shoulder line turns by angle_of(J) degrees."""
    def fn(d, T, J, s):
        k = s * SS
        c = add(J[anchor] if anchor in J else J["H"], offset)
        x, y = T(c)
        w = 33 * k
        d.rounded_rectangle([x - w, y - w, x + w, y + w], radius=6 * k, fill=(255, 255, 255, 215), outline=(170, 178, 198),
                            width=int(1.4 * k))
        a = math.radians(angle_of(J) * amp)
        # hips fixed
        d.line([(x - 13 * k, y + 8 * k), (x + 13 * k, y + 8 * k)], fill=X.SHORTS, width=int(6 * k))
        # shoulders turn about the spine
        sx, sy = math.cos(a) * 19 * k, math.sin(a) * 19 * k
        d.line([(x - sx, y - 2 * k - sy), (x + sx, y - 2 * k + sy)], fill=(255, 120, 20), width=int(6.5 * k))
        d.line([(x, y + 8 * k), (x, y - 2 * k)], fill=X.SHIRT, width=int(4 * k))
        nx, ny = math.sin(a) * 12 * k * -1, -math.cos(a) * 12 * k
        X.disc(d, (x + nx, y - 2 * k + ny), 4.5 * k, X.SKIN)
        # facing arrow at rest
        d.polygon([(x, y - 27 * k), (x - 3 * k, y - 22 * k), (x + 3 * k, y - 22 * k)], fill=(170, 178, 198))
    return X.Item(fn, lambda J: [add(J[anchor] if anchor in J else J["H"], (offset[0] - 36, offset[1] - 36)),
                                 add(J[anchor] if anchor in J else J["H"], (offset[0] + 36, offset[1] + 36))])


# --------------------------------------------------------------------------------------------- ROTATION
@pat("q_rotation", ("machine", ["machine"], "abs"), ("cable", ["cable"], "obliques"),
     ("barbell", ["landmine"], "obliques"))
def q_rotation(eq, var, hil):
    hil = hil or "obliques"
    if has(var, "machine"):
        return _rotary_machine(hil)
    if has(var, "landmine"):
        return _landmine_rotation(hil)
    return _cable_rotation(hil)


def _rotary_machine(hil):
    hip = (-6.0, -50.0)
    AX = -56.0
    AY = -112.0
    LL = 88.0

    def pose(tw):
        th = math.radians(tw * 26)
        xp = AX + LL * math.cos(th)
        kw = dict(A=(66.0, -6.0), hip=hip, torso=0, head=0, kh=(0, -1), foot=0, twist=tw, hand=(xp, 0.0),
                  W=(xp + 8, -110.0), W2=(xp + 6, -112.0), ah=(-0.3, 1), ah2=(-0.3, 1))
        return kw
    keys = [pose(-1.0), pose(0.0), pose(1.0), pose(0.0)]

    def machine(d, T, J, s):
        k = s * SS
        # base, seat, back column with rotation axis
        a, b = T((-85, -8)), T((95, 0))
        d.rounded_rectangle([a[0], a[1], b[0], b[1]], radius=3 * k, fill=X.METAL_D)
        a, b = T((-36, -50)), T((26, -40))
        d.rounded_rectangle([a[0], a[1], b[0], b[1]], radius=5 * k, fill=(70, 78, 100))
        a, b = T((-14, -40)), T((-8, -8))
        d.rectangle([a[0], a[1], b[0], b[1]], fill=X.BENCHC)
        a, b = T((AX - 8, -176)), T((AX + 6, -8))
        d.rounded_rectangle([a[0], a[1], b[0], b[1]], radius=3 * k, fill=X.BENCHC)
        X.disc(d, T((AX, AY)), 6 * k, X.METAL)

    def arm_pad(d, T, J, s):
        k = s * SS
        xp = J["hand_pt"][0] - J["wrist"][0]
        # rotating arm (horizontal, seen foreshortened) and the pad in front of the chest
        X.capsule(d, T((AX, AY)), T((xp + 14, AY)), 3.4 * k, 3.4 * k, X.METAL)
        X.capsule(d, T((xp + 14, AY - 26)), T((xp + 14, AY + 26)), 7 * k, 7 * k, (70, 78, 100))
    cue = top_inset(lambda J: -J["twist"] * 40, offset=(100, -150), anchor="hip")
    return spec(keys, X.many(X.Item(arm_pad, lambda J: [(AX, AY - 34), (AX + LL + 20, AY + 34)]), cue),
                X.Item(machine, lambda J: [(-90, -180), (100, 0)]), hilite=hil, loop="cycle", linear=False, steps=6)


def _cable_rotation(hil):
    """Front view: standing, arms straight at chest height pulling a cable across the body."""
    base = dict(H=(0, -152), lR=(0, 0), lL=(0, 0), lean=0, face=1)

    def pose(theta):
        hx = 82 * math.sin(math.radians(theta))
        hy = -214 - 8 * (1 - math.cos(math.radians(theta)))
        return dict(base, wR=(hx + 2, hy), wL=(hx - 2, hy), hR=(0, 1), hL=(0, 1), ry=theta * 0.9,
                    lR=(3, 0), lL=(-3, 0))
    keys = [pose(48), pose(0), pose(-48), pose(0)]
    TX = 128.0
    scene = X.cable_tower(TX, -214, side=1, w=24, stack_h=96)
    equip = X.many(X.cable_line((TX, -214), anchor="wR", handle="d"))
    cue = top_inset(lambda J: J["ry"], offset=(-92, -148), anchor="H")
    return spec(keys, equip, scene, front=cue, hilite=hil, view_kind="front", loop="cycle", linear=False, steps=6)


def _landmine_rotation(hil):
    P = (178.0, -8.0)

    def pose(tw):
        hx = 84 - 22 * abs(tw)
        kw = dict(A=(0.0, -6.0), hip=(0.0, -142.0), torso=3, head=2, kh=(1, 0.1), foot=0, A2=(-8.0, -6.0),
                  twist=tw * 0.9, W=(hx, -196.0), W2=(hx - 3, -197.0), ah=(0, 1), ah2=(0, 1))
        return kw
    keys = [pose(-1.0), pose(0.0), pose(1.0), pose(0.0)]

    def bar(d, T, J, s):
        k = s * SS
        w = J["wrist"]
        dx, dy = w[0] - P[0], w[1] - P[1]
        n = math.hypot(dx, dy)
        u = (dx / n, dy / n)
        end = (w[0] + u[0] * 22, w[1] + u[1] * 22)
        X.capsule(d, T(P), T(end), 2.6 * k, 2.6 * k, X.METAL)
        # plates on the free end
        for off, hh, col in ((-8, 20, X.EQUIP), (-1, 15, X.RUBBER)):
            c = (end[0] + u[0] * off, end[1] + u[1] * off)
            nx, ny = -u[1], u[0]
            X.capsule(d, T((c[0] + nx * hh, c[1] + ny * hh)), T((c[0] - nx * hh, c[1] - ny * hh)), 3.4 * k, 3.4 * k, col)
        # corner pivot on the floor
        X.disc(d, T(P), 6 * k, X.EQUIP)
        a, b = T((P[0] - 10, -8)), T((P[0] + 10, 0))
        d.rounded_rectangle([a[0], a[1], b[0], b[1]], radius=2 * k, fill=X.METAL_D)
    cue = top_inset(lambda J: -J["twist"] * 45, offset=(110, -150), anchor="hip")
    return spec(keys, X.many(X.Item(bar, lambda J: [(P[0] - 8, -16), (J["wrist"][0] - 30, J["wrist"][1] - 26)]), cue),
                None, hilite=hil, loop="cycle", linear=False, steps=6)


# --------------------------------------------------------------------------------------------- front-view helpers
def fleg(Hc, side, ank, out=1.0):
    """Thigh / shin angles (from down, + towards screen right) of a front-view leg whose ankle sits at `ank`."""
    hp = (Hc[0] + 9 * side, Hc[1])
    k, a, m = X.ik2(hp, ank, LEN["thigh"], LEN["shin"], (side * out, 0.0))
    return (X.ang_down(hp, k), X.ang_down(k, a))


def fpose(Hc, ankR, ankL, lean=0.0, out=1.0, **kw):
    d = dict(H=Hc, lean=lean, lR=fleg(Hc, 1, ankR, out), lL=fleg(Hc, -1, ankL, out))
    d.update(kw)
    return d


def hands_chest(Hc, lean=0.0, dy=26.0):
    S = (Hc[0] + math.sin(math.radians(lean)) * LEN["torso"], Hc[1] - math.cos(math.radians(lean)) * LEN["torso"])
    return dict(wR=(S[0] + 3, S[1] + dy), wL=(S[0] - 3, S[1] + dy), hR=(1, 0.2), hL=(-1, 0.2))


# --------------------------------------------------------------------------------------------- CHOPS (front view)
@pat("q_chop", ("none", ["front"], "obliques"), ("none", ["reverse"], "glutes"), ("cable", ["cable"], "obliques"))
def q_chop(eq, var, hil):
    hil = hil or "obliques"
    # high (upper right) <-> low (outside the left knee)
    hi = dict(H=(0, -152), lean=4, lR=(0, 0), lL=(0, 0))
    hi_h = (62.0, -300.0)
    lo_h = (-52.0, -92.0)
    A_hi = ((16.0, -6.0), (-16.0, -6.0))
    A_lo = ((30.0, -6.0), (-30.0, -6.0))
    high = fpose((0, -152), A_hi[0], A_hi[1], lean=6, wR=(hi_h[0] + 3, hi_h[1]), wL=(hi_h[0] - 3, hi_h[1] + 3),
                 hR=(1, 0.2), hL=(0, 1), ry=-30)
    Hc = (-6, -112)
    low = fpose(Hc, A_lo[0], A_lo[1], lean=-12, wR=(lo_h[0] + 3, lo_h[1]), wL=(lo_h[0] - 3, lo_h[1] + 3),
                hR=(0, 1), hL=(-1, 0.4), ry=30)
    mid = fpose((-3, -130), (22.0, -6.0), (-22.0, -6.0), lean=-4, wR=(14, -205), wL=(10, -203), hR=(1, 0.2),
                hL=(-1, 0.2), ry=0)
    cue = top_inset(lambda J: J["ry"], offset=(-98, -146), anchor="H")
    scene = equip = None
    if has(var, "cable"):
        TX = 140.0
        scene = X.cable_tower(TX, -300, side=1, w=24, stack_h=150)
        equip = X.cable_line((TX, -300), anchor="wR", handle="rope")
        keys = [high, mid, low, mid]
    elif has(var, "reverse"):
        keys = [low, mid, high, mid]
    else:
        keys = [high, mid, low, mid]
    return spec(keys, equip, scene, front=cue, hilite=hil, view_kind="front", loop="cycle", linear=False, steps=6)


# --------------------------------------------------------------------------------------------- LANDMINE SQUAT TO PRESS
def landmine_bar(P=(176.0, -8.0)):
    def fn(d, T, J, s):
        k = s * SS
        w = J["wrist"]
        dx, dy = w[0] - P[0], w[1] - P[1]
        n = math.hypot(dx, dy)
        u = (dx / n, dy / n)
        end = (w[0] + u[0] * 22, w[1] + u[1] * 22)
        X.capsule(d, T(P), T(end), 2.6 * k, 2.6 * k, X.METAL)
        for off, hh, col in ((-8, 20, X.EQUIP), (-1, 15, X.RUBBER)):
            c = (end[0] + u[0] * off, end[1] + u[1] * off)
            nx, ny = -u[1], u[0]
            X.capsule(d, T((c[0] + nx * hh, c[1] + ny * hh)), T((c[0] - nx * hh, c[1] - ny * hh)), 3.4 * k, 3.4 * k, col)
        X.disc(d, T(P), 6 * k, X.EQUIP)
        a, b = T((P[0] - 10, -8)), T((P[0] + 10, 0))
        d.rounded_rectangle([a[0], a[1], b[0], b[1]], radius=2 * k, fill=X.METAL_D)
    return X.Item(fn, lambda J: [(P[0] - 8, -16), (J["wrist"][0] - 28, J["wrist"][1] - 26)])


def squat_pose(depth, torso_extra=0.0, A=(0.0, -6.0)):
    """Profile squat: depth 0 = standing, 1 = full squat.  Returns (hip, torso)."""
    hip = (-42.0 * depth, -152.0 + 82.0 * depth)
    torso = 3 + 40 * depth + torso_extra
    return hip, torso


@pat("q_landmine_press", ("barbell", [], "shoulders"))
def q_landmine_press(eq, var, hil):
    hil = hil or "shoulders"

    def pose(depth, press):
        hip, torso = squat_pose(depth)
        S = sh_of(hip, torso)
        if press:
            W = (S[0] + 76, S[1] - 52)
        else:
            W = (S[0] + 26, S[1] + 6)
        return dict(A=(0.0, -6.0), A2=(-6.0, -6.0), hip=hip, torso=torso, head=torso * 0.5, W=W, W2=(W[0] - 3, W[1] + 2),
                    ah=(0, 1) if not press else (0, 1), ah2=(0, 1), kh=(1, 0.05), foot=0, foot2=0)
    rack = pose(0, False)
    down = pose(1.0, False)
    mid = pose(0.5, False)
    up = pose(0, True)
    keys = [rack, mid, down, mid, rack, up]
    return spec(keys, landmine_bar(), None, hilite=hil, loop="cycle", linear=False, steps=4)


# --------------------------------------------------------------------------------------------- SIDE-ON LEG DRILLS (front view)
@pat("q_sidesquat", ("none", ["lateral"], "glutes"), ("none", ["horse"], "glutes"), ("none", ["dragon"], "quads"),
     ("none", ["slide"], "quads"))
def q_sidesquat(eq, var, hil):
    if has(var, "horse"):
        return _horse(hil or "glutes")
    if has(var, "dragon"):
        return _dragon(hil or "quads")
    if has(var, "slide"):
        return _slide_squat(hil or "quads")
    return _lateral_walk(hil or "glutes")


def _lateral_walk(hil):
    def P(hx, hy, R, L, **kw):
        return fpose((hx, hy), R, L, wR=(hx + 21, hy - 76), wL=(hx - 21, hy - 76), hR=(1, 0.3), hL=(-1, 0.3), **kw)
    # arms bent in front of the chest for balance
    def Q(hx, hy, R, L):
        d = fpose((hx, hy), R, L, lean=0)
        d.update(hands_chest((hx, hy)))
        return d
    keys = [Q(0, -134, (30, -6), (-30, -6)),
            Q(8, -132, (72, -26), (-30, -6)),
            Q(22, -130, (72, -6), (-30, -6)),
            Q(36, -132, (72, -6), (8, -26)),
            Q(44, -134, (72, -6), (16, -6))]
    return spec(keys, None, None, hilite=hil, view_kind="front", loop="pingpong", linear=False, steps=3)


def _horse(hil):
    def Q(hy, aw, tremor=0.0):
        Hc = (0, hy)
        d = fpose(Hc, (aw, -6), (-aw, -6), out=1.0)
        d.update(hands_chest(Hc, dy=34))
        return d
    stand = Q(-152, 14)
    wide = Q(-130, 74)
    sink = Q(-88, 76)
    hold_a = Q(-86, 76)
    hold_b = Q(-90, 76)
    keys = [stand, wide, sink, hold_b, hold_a]
    return spec(keys, None, None, hilite=hil, view_kind="front", loop="pingpong", linear=False, steps=3,
                hold=(500, 1000))


def _dragon(hil):
    """Front view: the left foot steps behind and across the standing (right) leg, then a single-leg squat."""
    def Q(hx, hy, R, L, outL=0.4, **kw):
        d = fpose((hx, hy), R, L, **kw)
        d["lL"] = fleg((hx, hy), -1, L, outL)
        d.update(hands_chest((hx, hy), dy=30))
        return d
    keys = [Q(0, -150, (16, -6), (-16, -6), -1.0),
            Q(10, -148, (26, -6), (-16, -6), -1.0),
            Q(14, -147, (26, -6), (52, -34), 0.6),
            Q(16, -146, (26, -6), (62, -6), 0.6),
            Q(24, -112, (30, -6), (66, -6), 0.8, lean=-4),
            Q(26, -92, (32, -6), (70, -8), 0.8, lean=-6)]
    return spec(keys, None, None, hilite=hil, view_kind="front", loop="pingpong", linear=False, steps=2,
                hold=(500, 800))


def _slide_squat(hil):
    def Q(hx, hy, R, L):
        d = fpose((hx, hy), R, L)
        d.update(hands_chest((hx, hy)))
        return d
    keys = [Q(0, -106, (30, -6), (-30, -6)),     # squat in the centre
            Q(0, -150, (14, -6), (-14, -6)),     # stand
            Q(20, -146, (60, -26), (-14, -6)),   # step right
            Q(40, -150, (54, -6), (26, -6)),     # close
            Q(40, -106, (70, -6), (10, -6)),     # squat on the right
            Q(40, -150, (54, -6), (26, -6)),     # stand
            Q(20, -146, (54, -6), (-14, -26)),   # step back left
            Q(2, -150, (14, -6), (-14, -6))]     # close
    return spec(keys, None, None, hilite=hil, view_kind="front", loop="cycle", linear=False, steps=3)


# --------------------------------------------------------------------------------------------- SHRIMP SQUAT
@pat("q_shrimp", ("none", [], "quads"))
def q_shrimp(eq, var, hil):
    hil = hil or "quads"

    def pose(depth):
        hip = (-34.0 * depth, -152.0 + 82.0 * depth)
        torso = 4 + 36 * depth
        S = sh_of(hip, torso)
        # far foot held behind the hip by the far hand; the knee hangs down and drops to the floor
        A2 = (hip[0] - 40, hip[1] - 4)
        W2 = (A2[0] + 2, A2[1] - 1)
        W = (S[0] + 60, S[1] + 8 - 20 * depth)
        return dict(A=(0.0, -6.0), hip=hip, torso=torso, head=torso * 0.5, kh=(1, 0.1), A2=A2, kh2=(0.25, 1),
                    W=W, ah=(0, 1), W2=W2, ah2=(-1, 0.5), foot=0, foot2=-40, front2=False)
    keys = [pose(0.0), pose(0.5), pose(1.0)]
    return spec(keys, None, None, hilite=hil, loop="pingpong", linear=False, steps=5, hold=(600, 700))


# --------------------------------------------------------------------------------------------- THRUSTER
@pat("q_thruster", ("barbell", [], "shoulders"), ("dumbbell", [], "quads"))
def q_thruster(eq, var, hil):
    hil = hil or "shoulders"

    def pose(depth, arms):
        hip, torso = squat_pose(depth)
        torso = 3 + 24 * depth
        S = sh_of(hip, torso)
        if arms == "rack":
            W = (S[0] + 21, S[1] - 6)
            ah = (1, 0.1)
        elif arms == "mid":
            W = (S[0] + 14, S[1] - 56)
            ah = (1, 0.2)
        else:
            W = (S[0] + 4, S[1] - 93)
            ah = (1, 0)
        return dict(A=(0.0, -6.0), hip=hip, torso=torso, head=torso * 0.4 if arms == "top" else torso * 0.7, W=W,
                    W2=(W[0] - 2, W[1]), ah=ah, ah2=ah, kh=(1, 0.05), foot=0)
    keys = [pose(0, "rack"), pose(0.5, "rack"), pose(1.0, "rack"), pose(0.55, "mid"), pose(0.05, "mid"), pose(0, "top"),
            pose(0, "mid"), pose(0, "rack")]
    if eq == "dumbbell":
        equip = X.dumbbell("wrist")
        scene = X.dumbbell("wrist2")
    else:
        equip, scene = X.barbell("wrist", half=60, plate=21), None
    return spec(keys, equip, scene, hilite=hil, loop="cycle", linear=False, steps=3)


# --------------------------------------------------------------------------------------------- BOX JUMP
@pat("q_boxjump", ("none", [], "glutes"))
def q_boxjump(eq, var, hil):
    hil = hil or "glutes"
    BX0, BX1, BY = 66.0, 170.0, -84.0

    def P(**kw):
        d = dict(kh=(1, 0.05), foot=0, foot2=0)
        d.update(kw)
        return d
    stand = P(A=(18.0, -6.0), A2=(10.0, -6.0), hip=(18.0, -152.0), torso=2, head=0, uarm=2, farm=6, FA=(2, 6))
    dip = P(A=(18.0, -6.0), A2=(10.0, -6.0), hip=(-12.0, -92.0), torso=38, head=24, uarm=-62, farm=-48, FA=(-62, -48))
    toff = P(A=(30.0, -24.0), A2=(22.0, -26.0), hip=(24.0, -168.0), torso=-4, head=-2, foot=55, foot2=55,
             uarm=-170, farm=-170, FA=(-170, -170))
    air = P(A=(98.0, -104.0), A2=(88.0, -108.0), hip=(56.0, -166.0), torso=8, head=6, foot=20, foot2=20,
            uarm=-70, farm=-70, FA=(-70, -70), kh=(1, -0.1))
    land = P(A=(104.0, BY - 6), A2=(96.0, BY - 6), hip=(78.0, BY - 82), torso=30, head=18, foot=0, foot2=0,
             uarm=-55, farm=-50, FA=(-55, -50))
    top = P(A=(106.0, BY - 6), A2=(98.0, BY - 6), hip=(106.0, BY - 152), torso=2, head=0, uarm=2, farm=6, FA=(2, 6))
    down1 = P(A=(112.0, BY - 6), A2=(50.0, -40.0), hip=(96.0, BY - 88), torso=10, head=6, uarm=-20, farm=-10, FA=(-20, -10))
    down2 = P(A=(106.0, BY - 6), A2=(40.0, -6.0), hip=(68.0, -152.0), torso=0, head=0, uarm=2, farm=6, FA=(2, 6))
    keys = [stand, dip, toff, air, land, top, down1, down2]
    boxitem = X.Item(lambda d, T, J, s: _box(d, T, s, BX0, BX1, BY), lambda J: [(BX0, BY), (BX1, 0)])
    return spec(keys, None, boxitem, hilite=hil, loop="cycle", linear=False, steps=3)


def _box(d, T, s, x0, x1, y):
    k = s * SS
    a, b = T((x0, y)), T((x1, 0))
    d.rounded_rectangle([a[0], a[1], b[0], b[1]], radius=3 * k, fill=(214, 176, 124))
    a2, b2 = T((x0, y)), T((x1, y + 5))
    d.rounded_rectangle([a2[0], a2[1], b2[0], b2[1]], radius=2 * k, fill=(188, 148, 98))
    # side slot
    c0, c1 = T(((x0 + x1) / 2 - 12, y + 16)), T(((x0 + x1) / 2 + 12, y + 24))
    d.rounded_rectangle([c0[0], c0[1], c1[0], c1[1]], radius=3 * k, fill=(188, 148, 98))
