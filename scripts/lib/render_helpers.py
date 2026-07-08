"""Shared helpers for starcomb's comparison-ladder (--param mode): the GraXpert
runner, rendered-JPEG measurement, and side-by-side strip composition.
Imported, not run standalone (astrometrics/bg_qa resolve as lib siblings)."""
import os
import subprocess
import sys

import numpy as np

import astrometrics as am
import bg_qa

GRAXPERT = os.path.expanduser("~/.local/bin/graxpert")


def run_graxpert(stack_fit, work, log):
    """GraXpert AI background extraction on the pinned stack, cached by
    input identity (mtime+size) so ladders reuse it."""
    st = os.stat(stack_fit)
    key = f"gx_{st.st_size}_{int(st.st_mtime)}"
    out = os.path.join(work, f"{key}.fits")
    if os.path.exists(out):
        log(f"graxpert: cache hit {os.path.basename(out)}")
        return out
    log("graxpert: running background-extraction (first run downloads the "
        "AI model; takes minutes on this box)")
    r = subprocess.run([GRAXPERT, "-cmd", "background-extraction",
                        stack_fit, "-output", out[:-5], "-gpu", "false"],
                       capture_output=True, text=True)
    if not os.path.exists(out):
        sys.exit("graxpert: produced no output:\n"
                 + r.stdout[-3000:] + "\n" + r.stderr[-2000:])
    return out


def sanitize(v):
    return str(v).replace(" ", "").replace("/", "_").replace("=", "") \
        .replace("-", "m").replace(".", "p")[:40]


def measure_jpg(path):
    from PIL import Image
    a8 = np.asarray(Image.open(path), dtype=np.float64)
    qa = bg_qa.qa_metrics(a8)
    data = (a8.transpose(2, 0, 1) / 255.0).astype(np.float32)
    stars = am.star_metrics(data[1])
    lev = am.channel_levels(data)
    return qa, stars, lev


def star_region(stack_path):
    """Pick a deterministic star-rich 1:1 crop region from the pinned stack
    (brightest measured star nearest the frame center, branch excluded).
    Returns (x0, y0) of a 700x450 rect in stack display coords."""
    data, _ = am.load_image(stack_path)
    g = data[min(1, data.shape[0] - 1)]
    h, w = g.shape
    from scipy import ndimage
    bg, sig = am.bg_stats(g)
    mx = ndimage.maximum_filter(g, size=9, mode="nearest")
    cand = (g >= mx) & (g > bg + 25 * sig)
    cand[:100] = cand[-100:] = False
    cand[:, :100] = cand[:, -100:] = False
    cand &= am.branch_mask(h, w)
    ys, xs = np.nonzero(cand)
    if len(ys) == 0:
        return (w // 2 - 350, h // 2 - 225)
    d2 = (ys - h / 2) ** 2 + (xs - w / 2) ** 2
    order = np.argsort(g[ys, xs])[::-1][:30]     # 30 brightest
    best = order[np.argmin(d2[order])]           # nearest center among them
    x0 = int(np.clip(xs[best] - 350, 0, w - 700))
    y0 = int(np.clip(ys[best] - 225, 0, h - 450))
    return (x0, y0)


def compose_rows(rows, labels, out_path):
    """Stack per-value rows (already same width) with a text label bar."""
    from PIL import Image, ImageDraw
    parts = []
    for lab, row in zip(labels, rows):
        bar = Image.new("RGB", (row.width, 26), (18, 18, 18))
        d = ImageDraw.Draw(bar)
        d.text((8, 6), lab, fill=(230, 230, 230))
        parts += [bar, row]
    wmax = max(p.width for p in parts)
    total_h = sum(p.height for p in parts)
    canvas = Image.new("RGB", (wmax, total_h), (24, 24, 24))
    y = 0
    for p in parts:
        canvas.paste(p, (0, y))
        y += p.height
    canvas.save(out_path, quality=88)


def value_row(jpg_path, crop_margin, star_xy, thumb_div=6):
    """One comparison row for a value: full thumb | star crop | corner crop.
    star_xy is in STACK coords; the jpg may be cropped by crop_margin."""
    from PIL import Image
    im = Image.open(jpg_path)
    w, h = im.size
    th = im.resize((w // thumb_div, h // thumb_div), Image.LANCZOS)
    sx = star_xy[0] - crop_margin
    sy = star_xy[1] - crop_margin
    sx = max(0, min(sx, w - 700))
    sy = max(0, min(sy, h - 450))
    star = im.crop((sx, sy, sx + 700, sy + 450))
    corner = im.crop((w - 760, 60, w - 60, 510))
    gutter = 10
    hrow = max(th.height, 450)
    row = Image.new("RGB", (th.width + 700 + 700 + 2 * gutter, hrow), (24, 24, 24))
    row.paste(th, (0, 0))
    row.paste(star, (th.width + gutter, 0))
    row.paste(corner, (th.width + 700 + 2 * gutter, 0))
    return row


def fmt(v, spec="{:.2f}"):
    return "" if v is None else spec.format(v)
