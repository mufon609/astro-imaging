"""Shared helpers for starcomb's comparison-ladder (--param mode): the GraXpert
runner and rendered-JPEG measurement. Imported, not run standalone
(astrometrics/bg_qa resolve as lib siblings)."""
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


def fmt(v, spec="{:.2f}"):
    return "" if v is None else spec.format(v)
