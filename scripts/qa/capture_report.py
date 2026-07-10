#!/usr/bin/env python3
"""Per-channel capture report card for a composed multi-filter target.

Usage: capture_report.py <session> <target>

Objective, inspection-style measurement (WARN-only, never a gate): what
each filter channel actually CAPTURED, so palette/balance decisions and
acquisition planning rest on numbers instead of the rendered look.

Per member (composition.json `members`): filter identity (line + rest
wavelength from the recipe's spcc block, else the canonical line table),
subs x exposure + gain/offset, the EFFECTIVE object capture rate from
dark-subtracted mid-sequence raw lights (net ADU16/s over the sky at the
same instant — one number folding filter transmission x sensor QE at that
wavelength x optics), the sky rate per band (how sky-effective the
passband is), the member stack's object SNR, and the integration needed
for SNR parity with the best channel at these settings.

Regions are DERIVED, not hand-picked: object = bounding box of the
largest extended-object component on the composition's reference member
stack (>=400 px square); sky = the darkest 400 px corner box (100 px
inset). Raw-light coordinates approximate stack coordinates to within
the per-frame registration shifts — mid-sequence frames sit nearest the
registration reference, so the boxes land on the same sky (stated here,
measured shifts are tens of px against >=400 px boxes).

The capture-ratio table then meets the COMPOSED stack's display ratio at
the same boxes (the _comp_spcc stack when it exists, else _comp): the
gap between the two IS what member normalization + SPCC did to the
balance. Writes <session>/results/capture_report_<target>.md.

Scope: kind `mono-filters` (per-filter raw lights exist per member).
A dualband-osc target's lines share CFA frames — its per-line raw rates
need the extraction step first; the tool refuses loudly until that
lands. LRGB: L slots in as one more member row when the L-join lands.
"""
import json
import os
import sys
import time

import numpy as np

_libdir = os.path.dirname(os.path.abspath(__file__))
while _libdir != os.path.dirname(_libdir):
    if os.path.isdir(os.path.join(_libdir, "lib")):
        sys.path.insert(0, os.path.join(_libdir, "lib"))
        sys.path.insert(0, os.path.join(os.path.dirname(_libdir), "scripts",
                                        "stack"))
        break
    _libdir = os.path.dirname(_libdir)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), "stack"))
import astrometrics as am  # noqa: E402
import fitsmeta  # noqa: E402

# canonical emission lines / broadband labels for the report's identity
# column (a recipe spcc block with explicit wavelengths overrides)
LINES = {"Ha": ("H-alpha (hydrogen)", 656.28),
         "OIII": ("OIII (oxygen)", 500.70),
         "SII": ("SII (sulfur)", 671.60),
         "L": ("broadband luminance", None),
         "R": ("broadband red", None),
         "G": ("broadband green", None),
         "B": ("broadband blue", None)}
BOX = 400          # sky corner box (px); object box floor
INSET = 100        # corner inset (px)
N_LIGHTS = 3       # mid-sequence raw lights sampled per member
N_DARKS = 9        # raw dark frames medianed when no prebuilt master


def fits_list(d):
    return sorted(os.path.join(d, f) for f in os.listdir(d)
                  if f.lower().endswith((".fit", ".fits", ".fts")))


def load_adu(path):
    """A raw ushort light via the normalizing reader, rescaled back to
    ADU16 (read_fits divides integer data by 65535)."""
    data, _ = am.read_fits(path)
    return data[0] * 65535.0


def object_box(ref_stack):
    """Largest extended-object component's bbox on the reference member
    stack, floored to BOX px square; plus the darkest corner sky box."""
    from scipy import ndimage
    plane = am.read_fits(ref_stack)[0][0]
    h, w = plane.shape
    mask = am.extended_object_mask(plane)
    lab, n = ndimage.label(mask)
    if n:
        sizes = ndimage.sum(mask, lab, range(1, n + 1))
        ys, xs = np.nonzero(lab == (1 + int(np.argmax(sizes))))
        y0, y1, x0, x1 = ys.min(), ys.max(), xs.min(), xs.max()
    else:
        y0, y1, x0, x1 = h // 2 - BOX // 2, h // 2 + BOX // 2, \
            w // 2 - BOX // 2, w // 2 + BOX // 2
    # floor to BOX square, clamp to frame
    cy, cx = (y0 + y1) // 2, (x0 + x1) // 2
    hy = max((y1 - y0) // 2, BOX // 2)
    hx = max((x1 - x0) // 2, BOX // 2)
    oy0, oy1 = max(0, cy - hy), min(h, cy + hy)
    ox0, ox1 = max(0, cx - hx), min(w, cx + hx)
    corners = {}
    for name, (yy, xx) in {"tl": (INSET, INSET),
                           "tr": (INSET, w - INSET - BOX),
                           "bl": (h - INSET - BOX, INSET),
                           "br": (h - INSET - BOX, w - INSET - BOX)}.items():
        corners[name] = float(np.median(plane[yy:yy + BOX, xx:xx + BOX]))
    dark = min(corners, key=corners.get)
    sy, sx = {"tl": (INSET, INSET), "tr": (INSET, w - INSET - BOX),
              "bl": (h - INSET - BOX, INSET),
              "br": (h - INSET - BOX, w - INSET - BOX)}[dark]
    return (oy0, oy1, ox0, ox1), (sy, sy + BOX, sx, sx + BOX), dark


def member_dark(sdir, token):
    """Master dark in ADU16 for a member: prebuilt calib/ (ADU-scale
    float, read raw) wins; else median of raw darks/; else None."""
    calib = os.path.join(sdir, "calib")
    if os.path.isdir(calib) and fits_list(calib):
        import subprocess
        r = subprocess.run([sys.executable,
                            os.path.join(os.path.dirname(
                                os.path.abspath(fitsmeta.__file__)),
                                "fitsmeta.py"),
                            "--pick-masters", calib, token or "-"],
                           capture_output=True, text=True)
        if r.returncode == 0:
            dark_p = r.stdout.strip().split("\t")[0]
            if dark_p != "-":
                _, planes, _ = am.read_fits_planes(dark_p)
                return planes[0], f"prebuilt {os.path.basename(dark_p)}"
    darks = os.path.join(sdir, "darks")
    if os.path.isdir(darks):
        fl = fits_list(darks)
        if fl:
            sel = fl[:: max(1, len(fl) // N_DARKS)][:N_DARKS]
            med = np.median(np.stack([load_adu(p) for p in sel]), axis=0)
            return med, f"median of {len(sel)} darks/"
    return None, "NONE (rates include dark current)"


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    session, target = sys.argv[1], sys.argv[2]
    repo = os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))))
    sdir = os.path.join(repo, session)
    dsdir = os.path.join(repo, "datasets",
                         os.path.basename(os.path.normpath(session)), target)
    comp_p = os.path.join(dsdir, "composition.json")
    if not os.path.exists(comp_p):
        sys.exit(f"capture_report: no composition record {comp_p} — the "
                 "card is a multi-channel product (single-stack sets have "
                 "one channel to report)")
    comp = json.load(open(comp_p))
    if comp.get("kind") != "mono-filters":
        sys.exit(f"capture_report: kind {comp.get('kind')!r} not supported "
                 "yet — a dualband-osc target's lines share CFA frames, so "
                 "per-line raw rates need the extraction step first")
    members = comp["members"]
    reference = comp.get("reference", sorted(members)[0])
    chan_of_member = {v: c for c, v in comp["channels"].items()}
    wl_of_chan = {}
    recipe_p = os.path.join(dsdir, "recipe.json")
    if os.path.exists(recipe_p):
        spcc = json.load(open(recipe_p)).get("spcc", {})
        wl_of_chan = {"R": spcc.get("rwl"), "G": spcc.get("gwl"),
                      "B": spcc.get("bwl")}

    ref_stack = os.path.join(sdir, "results",
                             f"stack_{members[reference]}.fit")
    if not os.path.exists(ref_stack):
        sys.exit(f"capture_report: reference member stack missing "
                 f"({ref_stack}) — stack the members first")
    (oy0, oy1, ox0, ox1), (sy0, sy1, sx0, sx1), corner = \
        object_box(ref_stack)
    print(f"[capture_report] object box y{oy0}:{oy1} x{ox0}:{ox1} "
          f"(largest extended-object component on '{reference}'), "
          f"sky box {corner} corner")

    rows = []
    for name in sorted(members, key=lambda n: "RGB".find(
            chan_of_member.get(n, "?"))):
        set_name = members[name]
        ldir = os.path.join(sdir, set_name)
        frames = fits_list(ldir)
        if not frames:
            sys.exit(f"capture_report: no lights in {ldir}")
        meta = fitsmeta.frame_meta(frames[0])
        exp, gain, off, token = (float(meta[0]), meta[1], meta[2], meta[3])
        dark, dark_src = member_dark(sdir, token)
        mid = len(frames) // 2
        sel = frames[max(0, mid - 1):mid + N_LIGHTS - 1]
        obj_rates, sky_rates = [], []
        for p in sel:
            a = load_adu(p)
            if dark is not None:
                a = a - dark
            om = float(np.median(a[oy0:oy1, ox0:ox1]))
            sm = float(np.median(a[sy0:sy1, sx0:sx1]))
            obj_rates.append((om - sm) / exp)
            sky_rates.append(sm / exp)
        stack_p = os.path.join(sdir, "results", f"stack_{set_name}.fit")
        snr = None
        if os.path.exists(stack_p):
            plane = am.read_fits(stack_p)[0][0]
            _, sig = am.bg_stats(plane)
            net = float(np.median(plane[oy0:oy1, ox0:ox1])
                        - np.median(plane[sy0:sy1, sx0:sx1]))
            snr = net / max(sig, 1e-12)
        chan = chan_of_member.get(name, "?")
        wl = wl_of_chan.get(chan) or LINES.get(token, (None, None))[1]
        gas = LINES.get(token, (f"filter '{token}'", None))[0]
        rows.append({
            "member": name, "set": set_name, "chan": chan, "token": token,
            "gas": gas, "wl": wl, "n": len(frames), "exp": exp,
            "gain": gain, "offset": off,
            "hours": len(frames) * exp / 3600.0,
            "obj_rate": float(np.median(obj_rates)),
            "sky_rate": float(np.median(sky_rates)),
            "snr": snr, "dark_src": dark_src,
        })

    best = max((r for r in rows if r["snr"]), key=lambda r: r["snr"],
               default=None)
    ref_row = next((r for r in rows if r["member"] == reference), rows[0])
    for r in rows:
        r["flux_ratio"] = (r["obj_rate"] / ref_row["obj_rate"]
                           if ref_row["obj_rate"] else None)
        if best and r["snr"] and r is not best:
            need = r["hours"] * ((best["snr"] / r["snr"]) ** 2 - 1.0)
            r["parity_h"] = need
        else:
            r["parity_h"] = None

    # composed display ratio at the same boxes (what normalization + SPCC
    # did to the captured balance)
    comp_stack, comp_kind_note = None, ""
    for cand, note in ((f"stack_{target}_comp_spcc.fit", "SPCC'd"),
                       (f"stack_{target}_comp.fit", "pre-SPCC")):
        p = os.path.join(sdir, "results", cand)
        if os.path.exists(p):
            comp_stack, comp_kind_note = p, note
            break
    disp = {}
    if comp_stack:
        planes = am.read_fits(comp_stack)[0]
        ref_chan = chan_of_member[reference]
        idx = {"R": 0, "G": 1, "B": 2}
        ref_net = (np.median(planes[idx[ref_chan]][oy0:oy1, ox0:ox1])
                   - np.median(planes[idx[ref_chan]][sy0:sy1, sx0:sx1]))
        for r in rows:
            pl = planes[idx[r["chan"]]]
            net = (np.median(pl[oy0:oy1, ox0:ox1])
                   - np.median(pl[sy0:sy1, sx0:sx1]))
            disp[r["member"]] = float(net / ref_net) if ref_net else None

    lines = [f"# Capture report card — {target} "
             f"(generated {time.strftime('%Y-%m-%d')})", ""]
    lines += [f"Method: {N_LIGHTS} mid-sequence raw lights per member, "
              "master-dark subtracted, rates in net ADU16/s (same sensor "
              "and gain across members folds filter transmission x QE x "
              "optics into one comparable number). Object box "
              f"y{oy0}:{oy1} x{ox0}:{ox1} = largest extended-object "
              f"component on the reference member stack ('{reference}'); "
              f"sky = darkest corner box ({corner}). Raw-light coords "
              "approximate stack coords within the per-frame registration "
              "shifts (mid-sequence frames sit nearest the reference). "
              "Stack SNR = object net counts per stacked pixel / sky "
              "pixel noise.", ""]
    hdr = ("| member | ch | line (gas) | nm | subs x exp | total | gain/"
           "off | object rate | sky rate | stack SNR | to match best |")
    lines += [hdr, "|" + "---|" * 11]
    for r in rows:
        wl = f"{r['wl']:.2f}" if r["wl"] else "—"
        parity = (f"+{r['parity_h']:.1f} h" if r["parity_h"] is not None
                  else "—")
        snr = f"{r['snr']:.1f}" if r["snr"] else "n/a"
        lines.append(
            f"| {r['member']} | {r['chan']} | {r['gas']} | {wl} | "
            f"{r['n']} x {r['exp']:g} s | {r['hours']:.2f} h | "
            f"{r['gain'] or '—'}/{r['offset'] or '—'} | "
            f"{r['obj_rate'] * 1000:.1f} "
            f"mADU/s | {r['sky_rate'] * 1000:.1f} mADU/s | {snr} | "
            f"{parity} |")
    lines += ["", f"Captured line-flux ratios ({reference} = 1): "
              + " : ".join(f"{r['member']} {r['flux_ratio']:.3f}"
                           for r in rows if r["flux_ratio"] is not None)]
    if disp:
        lines += [f"Composed-stack display ratios ({comp_kind_note}, "
                  f"{reference} = 1): "
                  + " : ".join(f"{m} {v:.3f}" for m, v in disp.items()
                               if v is not None),
                  "The gap between the two lines is what member "
                  "normalization + SPCC did to the captured balance."]
    else:
        lines += ["Composed stack not found — rerun after compose/SPCC "
                  "for the display-ratio section."]
    lines += ["", "Dark subtraction per member: "
              + "; ".join(f"{r['member']}: {r['dark_src']}" for r in rows)]

    out = os.path.join(sdir, "results", f"capture_report_{target}.md")
    with open(out, "w") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines))
    print(f"[capture_report] wrote {os.path.relpath(out, repo)}")


if __name__ == "__main__":
    main()
