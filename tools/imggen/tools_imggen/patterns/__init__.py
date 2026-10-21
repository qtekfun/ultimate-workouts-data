"""Pattern registry.

PATTERNS maps a movement-pattern id (see CONTRACT.md) to a function(equipment, variants, hilite) -> spec.
  equipment : equipment id string ("barbell", "dumbbell", "machine", "none", ...)
  variants  : list of variant tags ("incline", "seated", "single_arm", ...)
  hilite    : muscle id to paint orange, or None

Two spec styles are rendered by render_spec():
  * engine specs (patterns_a.py):  dict(poses=[...], equipment=Gear, scene=Gear, hilite=..., cycle=False, hold=(ms, ms))
    see tools_imggen/figure.py (body() builds poses from contact targets, Gear classes draw equipment).
  * keys specs (patterns_b.py):    dict(keys=[...], ...) rendered by patterns/extras_b.py
"""
import os
import sys

PATTERNS = {}
SOURCES = {}

try:
    from .patterns_a import PATTERNS as _A
    PATTERNS.update(_A)
    SOURCES.update({k: "a" for k in _A})
except Exception as e:  # pragma: no cover
    print("patterns_a not available:", e, file=sys.stderr)

try:
    from .patterns_b import PATTERNS as _B
    for _k, _v in _B.items():
        PATTERNS.setdefault(_k, _v)
        SOURCES.setdefault(_k, "b")
except Exception as e:
    print("patterns_b not available:", e, file=sys.stderr)


try:
    from .patterns_z import PATTERNS as _Z
    for _k, _v in _Z.items():
        PATTERNS.setdefault(_k, _v)
        SOURCES.setdefault(_k, "z")
except Exception as e:
    print("patterns_z not available:", e, file=sys.stderr)

try:
    from .patterns_x import PATTERNS as _X
    for _k, _v in _X.items():
        PATTERNS.setdefault(_k, _v)
        SOURCES.setdefault(_k, "x")
except Exception as e:
    print("patterns_x not available:", e, file=sys.stderr)


try:
    from .patterns_y import PATTERNS as _Y
    for _k, _v in _Y.items():
        PATTERNS.setdefault(_k, _v)
        SOURCES.setdefault(_k, "y")
except Exception as e:
    print("patterns_y not available:", e, file=sys.stderr)


try:
    from .patterns_r import PATTERNS as _R
    for _k, _v in _R.items():
        PATTERNS.setdefault(_k, _v)
        SOURCES.setdefault(_k, "r")
except Exception as e:
    print("patterns_r not available:", e, file=sys.stderr)


try:
    from .patterns_q import PATTERNS as _Q
    for _k, _v in _Q.items():
        PATTERNS.setdefault(_k, _v)
        SOURCES.setdefault(_k, "q")
except Exception as e:
    print("patterns_q not available:", e, file=sys.stderr)


try:
    from .patterns_p import PATTERNS as _P
    for _k, _v in _P.items():
        PATTERNS.setdefault(_k, _v)
        SOURCES.setdefault(_k, "p")
except Exception as e:
    print("patterns_p not available:", e, file=sys.stderr)


def build_spec(pattern, equipment="none", variants=(), hilite=None):
    fn = PATTERNS[pattern]
    return fn(equipment or "none", list(variants or []), hilite)


def render_spec(spec, size=360, steps=9):
    """-> (frames, durations_ms)"""
    if "keys" in spec:
        from . import extras_b
        imgs, durs, _ = extras_b.render_spec(spec, size=size)
        return imgs, durs
    from .. import figure
    return figure.animate_spec(spec, steps=steps, size=size)
