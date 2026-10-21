"""Local runner: python3 run_b.py [pattern ...]  -> test sheets under ~/re/workouts/imggen/test_b/"""
import os, sys, itertools
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from PIL import Image, ImageDraw
from tools_imggen.patterns import extras_b as X
from tools_imggen.patterns import patterns_b as PB

OUT = os.path.expanduser("~/re/workouts/imggen/test_b")


def variants_for(pid):
    return PB.TEST_VARIANTS.get(pid, [("", [], "")])


def run(pid, eq, var, hil, size=360):
    spec = PB.PATTERNS[pid](eq, var, hil)
    return spec, X.render_spec(spec, size=size)


def sheet(pid, cell=300, save_webp=False):
    rows = PB.TEST_VARIANTS.get(pid, [("none", [], None)])
    W = cell * 5
    sh = Image.new("RGB", (W, cell * len(rows)), (255, 255, 255))
    dr = ImageDraw.Draw(sh)
    for ri, (eq, var, hil) in enumerate(rows):
        spec, (imgs, durs, Js) = run(pid, eq, var, hil)
        n = len(imgs)
        idx = [0, n // 8 * 1, n // 4, n // 2 - 1 if False else n // 2 - 1, n // 2]
        # frames: start, quarter, middle (at the peak), then 3/4 and a final
        pick = []
        span = n if spec.get("loop") == "cycle" else n // 2
        for i in range(5):
            pick.append(int(round(i * span / (5 if spec.get("loop") == "cycle" else 4))))
        for ci, fi in enumerate(pick):
            im = imgs[min(fi, n - 1)].resize((cell, cell), Image.LANCZOS)
            sh.paste(im, (ci * cell, ri * cell))
        dr.text((6, ri * cell + 4), f"{pid} {eq} {','.join(var)} {hil}", fill=(0, 0, 0))
        miss = max(j.get("miss", 0) for j in Js)
        if miss > 0.5:
            print(f"  WARN {pid} {eq} {var}: unreachable by {miss:.1f}px")
        if save_webp:
            p = os.path.join(OUT, f"{pid}_{eq}_{'-'.join(var)}_{hil}.webp")
            kb = X.save_webp(imgs, durs, p) // 1024
            print(f"  {pid} {eq} {var}: {len(imgs)} frames {kb} KB")
    p = os.path.join(OUT, f"{pid}.png")
    sh.save(p)
    return p


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    names = [a for a in sys.argv[1:] if not a.startswith("-")] or list(PB.PATTERNS)
    for n in names:
        print(n, sheet(n, save_webp="-w" in sys.argv))
