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


def run_graxpert_rbf(stack_fit, work, log):
    """GraXpert CLASSICAL background extraction (RBF, thin-plate) driven
    by a pipeline-generated OFF-OBJECT sample grid — the constrained mode
    for fields carrying BOTH a real (coloured / higher-order) gradient
    AND frame-filling faint object signal: there the AI mode absorbs the
    object (it classifies a 256 px thumbnail, where a frame-filling
    faint complex reads as the light-pollution class) and a first-degree
    plane tilts into the object and under-corrects the colour (both
    measured). Sample points are placed per grid cell on the darkest
    smoothed sky; cells mostly covered by the dilated extended-object
    mask contribute none, so the interpolant can only model the true
    background. Coordinates are GraXpert's raw FITS array order (x=col,
    y=row — it applies no orientation flip). Cached by input identity;
    fails loud when the field leaves too few sky cells to constrain the
    fit."""
    import json

    from scipy import ndimage
    from scipy.ndimage import gaussian_filter

    st = os.stat(stack_fit)
    key = f"gx_rbf_{st.st_size}_{int(st.st_mtime)}"
    out = os.path.join(work, f"{key}.fits")
    if os.path.exists(out):
        log(f"graxpert-rbf: cache hit {os.path.basename(out)}")
        return out

    cards, planes, _ = am.read_fits_planes(stack_fit)
    G = planes[min(1, planes.shape[0] - 1)]
    del planes, cards
    G4 = G[::4, ::4].astype(np.float32)
    del G
    # object exclusion at quarter resolution: k slightly permissive and a
    # 64 full-res px dilation margin so faint envelope edges stay out of
    # the sample set (a sample ON faint object lifts it into the model)
    obj4 = am.extended_object_mask(G4, k=3.0, scale=12)
    obj4 = ndimage.binary_dilation(obj4, iterations=16)
    sm4 = gaussian_filter(G4.astype(np.float64), 4)
    h4, w4 = G4.shape
    ny, nx = 10, 15                      # sample grid (GraXpert-typical)
    pts = []
    for iy in range(ny):
        for ix in range(nx):
            y0, y1 = h4 * iy // ny, h4 * (iy + 1) // ny
            x0, x1 = w4 * ix // nx, w4 * (ix + 1) // nx
            cell_obj = obj4[y0:y1, x0:x1]
            if cell_obj.mean() > 0.5:    # cell is mostly object: no sample
                continue
            cell = np.where(cell_obj, np.inf, sm4[y0:y1, x0:x1])
            flat = int(np.argmin(cell))
            ry, rx = divmod(flat, cell.shape[1])
            pts.append([int((x0 + rx) * 4), int((y0 + ry) * 4)])
    if len(pts) < 20:
        sys.exit(f"graxpert-rbf: only {len(pts)} off-object sample cells "
                 f"on {stack_fit} — the field is too object-filled to "
                 "constrain a background fit; use bgelin_mode plane or "
                 "gx deliberately instead")
    prefs = {"interpol_type_option": "RBF", "RBF_kernel": "thin_plate",
             "smoothing_option": 0.5, "sample_size": 25,
             "spline_order": 3, "corr_type": "Subtraction",
             "background_points": pts}
    prefs_p = os.path.join(work, f"{key}_prefs.json")
    with open(prefs_p, "w") as f:
        json.dump(prefs, f)
    log(f"graxpert-rbf: {len(pts)}/{nx * ny} off-object samples "
        "(object cells excluded), RBF thin-plate smoothing 0.5")
    r = subprocess.run([GRAXPERT, "-cmd", "background-extraction",
                        stack_fit, "-preferences_file", prefs_p,
                        "-output", out[:-5], "-gpu", "false"],
                       capture_output=True, text=True)
    if not os.path.exists(out):
        # graxpert writes relative to the input dir when it dislikes the
        # output path; look there before failing
        alt = os.path.join(os.path.dirname(stack_fit),
                           os.path.basename(out))
        if os.path.exists(alt):
            os.replace(alt, out)
    if not os.path.exists(out):
        sys.exit("graxpert-rbf: produced no output:\n"
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
