#!/usr/bin/env python3
"""Render the exercise animations.

  python3 render_all.py                 # read mapping.json, write out_all/<exerciseId>.anim.webp, print a report
  python3 render_all.py --demo          # one animation per pattern+variant -> out_demo/ plus contact sheets (PNG)
  python3 render_all.py --demo --only squat,lunge   # restrict to some patterns
  options: --mapping FILE  --out DIR  --jobs N  --max-kb 45
"""
import argparse
import json
import os
import sys
import time
import shutil
import traceback
from multiprocessing import Pool

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from PIL import Image, ImageDraw  # noqa: E402
from tools_imggen import patterns as PT  # noqa: E402
from tools_imggen import figure as F  # noqa: E402

CONTRACT_VARIANTS = {"incline", "decline", "seated", "standing", "lying", "single_arm", "alternating", "narrow",
                     "wide", "reverse", "front", "overhead", "bodyweight"}


def demos():
    """{pattern: [(equipment, variants, hilite), ...]} from the pattern modules (DEMOS / TEST_VARIANTS)."""
    out = {}
    for modname in ("patterns_a", "patterns_b"):
        try:
            mod = __import__("tools_imggen.patterns." + modname, fromlist=["x"])
        except ImportError:
            continue
        d = getattr(mod, "DEMOS", None) or getattr(mod, "TEST_VARIANTS", None) or {}
        for k, v in d.items():
            out.setdefault(k, v)
    for k in PT.PATTERNS:
        out.setdefault(k, [("none", [], None)])
    return out


def used_variants(pattern):
    for modname in ("patterns_a", "patterns_b"):
        try:
            mod = __import__("tools_imggen.patterns." + modname, fromlist=["x"])
        except ImportError:
            continue
        uv = getattr(mod, "USED_VARIANTS", {})
        if pattern in uv:
            return uv[pattern]
    return None


def render_one(args):
    pattern, eq, variants, hilite, path, max_kb = args
    try:
        spec = PT.build_spec(pattern, eq, variants, hilite)
        imgs, durs = PT.render_spec(spec)
        size = F.save_webp(imgs, durs, path, max_kb=max_kb)
        return (args, size, len(imgs), None, imgs)
    except Exception:
        return (args, 0, 0, traceback.format_exc(limit=4), None)


def contact_sheet(rows, path, cell=270, cols=(0, 3, 6, 9)):
    """rows: [(label, imgs)] -> PNG with the frames at indices cols (clamped)."""
    sh = Image.new("RGB", (cell * len(cols), (cell + 16) * len(rows)), (255, 255, 255))
    dr = ImageDraw.Draw(sh)
    for ri, (label, imgs) in enumerate(rows):
        dr.text((4, ri * (cell + 16) + 2), label, fill=(0, 0, 0))
        n = len(imgs)
        for ci, fi in enumerate(cols):
            if n == 0:
                continue
            # frames in a ping-pong are symmetric, "peak" is at (n-1)//2
            peak = (n - 1) // 2
            idx = [0, int(peak * 0.38), int(peak * 0.7), peak][ci] if len(cols) == 4 else min(fi, n - 1)
            sh.paste(imgs[min(idx, n - 1)].resize((cell, cell), Image.LANCZOS), (ci * cell, ri * (cell + 16) + 16))
    sh.save(path)


def run_demo(only, out_dir, jobs, max_kb):
    os.makedirs(out_dir, exist_ok=True)
    dm = demos()
    names = [n for n in dm if (not only or n in only)]
    tasks = []
    for n in names:
        if n not in PT.PATTERNS:
            continue
        for i, (eq, var, hil) in enumerate(dm[n]):
            fn = f"{n}__{eq}__{'-'.join(var) or 'base'}.webp"
            tasks.append((n, eq, list(var), hil, os.path.join(out_dir, fn), max_kb))
    t0 = time.time()
    with Pool(jobs) as pool:
        res = pool.map(render_one, tasks)
    byp = {}
    for (args, size, nfr, err, imgs) in res:
        pattern, eq, var, hil, path, _ = args
        label = f"{pattern} | {eq} | {','.join(var)} | {hil}  {size // 1000}KB {nfr}f"
        if err:
            print("FAIL", pattern, eq, var, "\n", err)
            continue
        byp.setdefault(pattern, []).append((label, imgs))
        if size > max_kb * 1000:
            print(f"OVERSIZE {pattern} {eq} {var}: {size // 1000} KB")
    for p, rows in byp.items():
        for j in range(0, len(rows), 4):
            contact_sheet(rows[j:j + 4], os.path.join(out_dir, f"sheet_{p}_{j // 4}.png"))
    print(f"demo: {len(tasks)} animations, {time.time() - t0:.0f}s -> {out_dir}")


def run_mapping(mapping_path, out_dir, jobs, max_kb):
    os.makedirs(out_dir, exist_ok=True)
    with open(mapping_path) as f:
        mapping = json.load(f)
    dm_patterns = set(PT.PATTERNS)
    unknown_patterns, unknown_variants, skipped = {}, {}, []
    groups = {}
    for eid, m in mapping.items():
        pat = m.get("pattern") or "none"
        if pat == "none":
            skipped.append(eid)
            continue
        if pat not in dm_patterns:
            unknown_patterns.setdefault(pat, []).append(eid)
            continue
        var = [v for v in (m.get("variants") or [])]
        uv = used_variants(pat)
        for v in var:
            if v not in CONTRACT_VARIANTS or (uv is not None and v not in uv):
                unknown_variants.setdefault(v, set()).add(pat)
        key = (pat, m.get("equipment") or "none", tuple(sorted(var)), m.get("hilite") or None)
        groups.setdefault(key, []).append(eid)
    tmp = os.path.join(out_dir, ".cache")
    os.makedirs(tmp, exist_ok=True)
    tasks, keypath = [], {}
    for i, key in enumerate(groups):
        p = os.path.join(tmp, f"{i}.webp")
        keypath[key] = p
        tasks.append((key[0], key[1], list(key[2]), key[3], p, max_kb))
    t0 = time.time()
    fails, big = [], []
    with Pool(jobs) as pool:
        for (args, size, nfr, err, _imgs) in pool.imap_unordered(render_one, tasks, chunksize=2):
            if err:
                fails.append((args[:4], err))
            elif size > max_kb * 1000:
                big.append((args[:4], size // 1000))
    ok = 0
    for key, eids in groups.items():
        src = keypath[key]
        if not os.path.exists(src) or any(key[:4] == f[0] for f in fails):
            continue
        for eid in eids:
            shutil.copyfile(src, os.path.join(out_dir, f"{eid}.anim.webp"))
            ok += 1
    shutil.rmtree(tmp, ignore_errors=True)
    print(f"rendered {ok} animations from {len(groups)} unique combinations in {time.time() - t0:.0f}s -> {out_dir}")
    print(f"skipped (pattern none): {len(skipped)}")
    if unknown_patterns:
        print("UNKNOWN PATTERNS (no generator, the app shows the muscle icon):")
        for p, ids in sorted(unknown_patterns.items()):
            print(f"  {p}: {len(ids)} exercises")
    if unknown_variants:
        print("VARIANTS NOT DRAWN (ignored by the pattern):")
        for v, ps in sorted(unknown_variants.items()):
            print(f"  {v}: {sorted(ps)}")
    if big:
        print("OVER SIZE LIMIT:")
        for a, kb in big:
            print("  ", a, kb, "KB")
    if fails:
        print("FAILURES:")
        for a, e in fails:
            print("  ", a, "\n", e)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--demo", action="store_true")
    ap.add_argument("--only", default="")
    ap.add_argument("--mapping", default=os.path.join(HERE, "mapping.json"))
    ap.add_argument("--out", default=None)
    ap.add_argument("--jobs", type=int, default=max(1, (os.cpu_count() or 2) - 1))
    ap.add_argument("--max-kb", type=int, default=45)
    a = ap.parse_args()
    only = [x for x in a.only.split(",") if x]
    if a.demo:
        run_demo(only, a.out or os.path.join(HERE, "out_demo"), a.jobs, a.max_kb)
    else:
        run_mapping(a.mapping, a.out or os.path.join(HERE, "out_all"), a.jobs, a.max_kb)


if __name__ == "__main__":
    main()
