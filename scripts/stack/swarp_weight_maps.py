#!/usr/bin/env python3
"""Writers for the SWarp tapered-weight compose (the WEIGHTED form of the
partial-frame knob): the per-member TPV `.head`, the per-member weight map,
and the output `coadd.head` that pins the coadd to the canonical's grid.

    swarp_weight_maps.py head   <member.fit> <out.head> [--flxscale=F]
    swarp_weight_maps.py weight <member.fit> <out.weight.fits> --stackcnt=N [--xc=PX] [--tmin=0.02] [--taper=300]
    swarp_weight_maps.py coadd-head <raw_compose_product.fit> <coadd.head>
    swarp_weight_maps.py norm <seqstat.csv> <members dir> <ref member path> <out.csv>
    swarp_weight_maps.py --selftest

WHY THIS EXISTS. Siril's astrometric compose (`seqplatesolve` + `seqapplyreg`,
run_undistort_compose.sh) takes no per-member weight map, so a member's
measured-bad entry-side zone can only be REMOVED (Siril `crop` — the crop20 /
cropT arms), and removing it starves the coverage of the canvas rim those
columns alone feed (the bottom-left staircase, member_selection_arm.json /
cropT_arm.json). SWarp takes a weight map per input, so the zone can be
TAPERED instead: full weight inside the member's clean field, a raised cosine
down to `tmin` over the rule's own half-width, never zero — where good cover
exists the tapered columns contribute ~2 %, where they are the only cover the
weighted mean normalises to them and the coverage stays.

WHAT IS IN-HOUSE HERE, AND WHAT IS NOT. No deliverable pixel is read or
written by this file. The weight map is a FORMULA over three tool-sourced
numbers — x_c (Siril `findstar` via the GO #13 asymmetry rule), STACKCNT and
NAXIS1 (the member's header) — and the map is an INPUT to SWarp, like a mask.
The `.head` is a header conversion by the standard tool for it, `sip_tpv`
(SIP -> TPV, exact in this direction: no fit — TOOLS.md's SWarp row), written
as ASCII cards SWarp reads beside the image; the member FITS is never
rewritten. The output `coadd.head` copies the canonical raw compose product's
TAN WCS (CRVAL/CRPIX/CD from its PC x CDELT) and canvas size.

    weight map:  w(x, y) = STACKCNT * t(x)
                 t(x) = 1                                   x <= x0 = W/2 + x_c
                      = tmin + (1 - tmin) * (1 + cos(pi (x - x0)/taper)) / 2   x0 < x < x0 + taper
                      = tmin                                x >= x0 + taper
                 a member with no x_c: t = 1 everywhere (the untouched 50).
    STACKCNT in the map reproduces the compose's `-weight=nbstack` under
    SWarp's COMBINE_TYPE WEIGHTED (sum w f / sum w).

Runs under /opt/astro-venv/bin/python (sip_tpv lives there); numpy + astropy
only otherwise. Every card the .head carries is printed by --selftest on a
synthetic SIP header, and the taper's three anchor values are asserted.

REMOVAL CONDITION: retire when Siril's compose accepts per-member weight maps
(a scriptable per-image weight input to `stack`/`seqapplyreg`, or an
equivalent in the shipped route). Registered in BACKLOG `removal-conditions`.
"""
import math
import os
import sys

import numpy as np
from astropy.io import fits


def cd_matrix(h):
    """The linear part as a CD matrix from either form (CD, or PC x CDELT)."""
    if "CD1_1" in h:
        return [[float(h["CD1_1"]), float(h.get("CD1_2", 0.0))],
                [float(h.get("CD2_1", 0.0)), float(h["CD2_2"])]]
    d1, d2 = float(h["CDELT1"]), float(h["CDELT2"])
    p = [[float(h.get("PC1_1", 1.0)), float(h.get("PC1_2", 0.0))],
         [float(h.get("PC2_1", 0.0)), float(h.get("PC2_2", 1.0))]]
    return [[d1 * p[0][0], d1 * p[0][1]], [d2 * p[1][0], d2 * p[1][1]]]


def _card(key, val, comment=""):
    if isinstance(val, str):
        v = "'" + val.replace("'", "''").ljust(8) + "'"
        return f"{key:<8}= {v:<20} / {comment}"[:80].rstrip()
    if isinstance(val, bool):
        return f"{key:<8}= {'T' if val else 'F':>20} / {comment}"[:80].rstrip()
    if isinstance(val, int):
        return f"{key:<8}= {val:>20d} / {comment}"[:80].rstrip()
    return f"{key:<8}= {val:>20.15G} / {comment}"[:80].rstrip()


def head_cards(h, flxscale=None):
    """The TPV WCS cards for a member's SIP header (sip_tpv, exact direction).

    CD ONLY, deliberately. MEASURED (GO #15, P2b/P2c/P5): SWarp reads the CD
    matrix and ignores PC/CDELT when CD is present (a .head with deliberately
    wrong PC/CDELT beside a correct CD coadds pixel-identically), so the
    Siril-written channel file's own PC+CDELT are inert under this .head; and
    astropy reads a TPV header with BOTH forms present WRONGLY (PV terms on the
    wrong basis — thousands of px off), while CD-only reproduces the SIP sky
    exactly. Two forms in one header is the registry's dual-matrix trap
    (plate-solving-wcs.md); this writer never emits it."""
    import sip_tpv                                       # the standard converter
    hh = h.copy()
    sip_tpv.sip_to_pv(hh, tpv_format=True, preserve=False)   # in place: CTYPE -> TPV, PV1_*/PV2_* written, SIP deleted
    assert str(hh["CTYPE1"]).startswith("RA---TPV") and str(hh["CTYPE2"]).startswith("DEC--TPV"), "TPV CTYPE missing"
    pv = [(k, float(hh[k])) for k in hh if k.startswith(("PV1_", "PV2_"))]
    assert pv, "no PV terms written — the SIP -> TPV conversion produced nothing"
    cd = cd_matrix(h)
    cards = [_card("CTYPE1", "RA---TPV", "TPV: the member's SIP converted by sip_tpv"),
             _card("CTYPE2", "DEC--TPV", ""),
             _card("CRVAL1", float(h["CRVAL1"]), "deg"), _card("CRVAL2", float(h["CRVAL2"]), "deg"),
             _card("CRPIX1", float(h["CRPIX1"]), ""), _card("CRPIX2", float(h["CRPIX2"]), ""),
             _card("CUNIT1", "deg", ""), _card("CUNIT2", "deg", ""),
             _card("EQUINOX", 2000.0, ""),
             _card("CD1_1", cd[0][0], ""), _card("CD1_2", cd[0][1], ""),
             _card("CD2_1", cd[1][0], ""), _card("CD2_2", cd[1][1], "")]
    cards += [_card(k, v, "TPV distortion term") for k, v in pv]
    if flxscale is not None:
        cards.append(_card("FLXSCALE", float(flxscale), "s_ref/s_i: the addscale scale term (D4)"))
    cards.append("END")
    return cards


def write_head(member, out, flxscale=None):
    h = fits.getheader(member)
    cards = head_cards(h, flxscale)
    with open(out, "w") as f:
        f.write("\n".join(cards) + "\n")
    return len(cards)


def taper(x, x0, tmin, width):
    """t(x) — 1 inside, raised cosine over `width` px, tmin beyond; never zero."""
    t = np.ones_like(x, dtype=np.float64)
    ramp = (x > x0) & (x < x0 + width)
    t[ramp] = tmin + (1.0 - tmin) * (1.0 + np.cos(np.pi * (x[ramp] - x0) / width)) / 2.0
    t[x >= x0 + width] = tmin
    return t


def write_weight(member, out, stackcnt, xc=None, tmin=0.02, width=300):
    h = fits.getheader(member)
    W, H = int(h["NAXIS1"]), int(h["NAXIS2"])
    x = np.arange(W, dtype=np.float64)                  # 0-based column index
    if xc is None:
        t = np.ones(W)
    else:
        t = taper(x, W / 2.0 + float(xc), float(tmin), float(width))
    assert t.min() > 0, "a weight map must never reach zero"
    w = (float(stackcnt) * t).astype(np.float32)
    data = np.repeat(w[None, :], H, axis=0)
    hdr = fits.Header()
    hdr["WMAPFORM"] = ("STACKCNT*t(x); 1|raised-cos|tmin", "swarp_weight_maps.py D5")
    hdr["WMAPXC"] = (-1 if xc is None else int(xc), "x_c px from the member centre; -1 = flat")
    hdr["WMAPMIN"] = (float(tmin), "t_min at and beyond x0+taper")
    hdr["WMAPTAP"] = (int(width), "taper width px (= the rule's station half-width)")
    hdr["WMAPCNT"] = (int(stackcnt), "STACKCNT multiplier (nbstack)")
    fits.PrimaryHDU(data, header=hdr).writeto(out, overwrite=True)
    return W, H, float(w.min()), float(w.max())


def write_coadd_head(product, out):
    """The output grid: the canonical raw compose product's TAN field and canvas."""
    h = fits.getheader(product)
    assert str(h["CTYPE1"]).startswith("RA---TAN") and "SIP" not in str(h["CTYPE1"]), "the output grid must be a clean TAN"
    cd = cd_matrix(h)
    cards = [_card("NAXIS", 2, ""), _card("NAXIS1", int(h["NAXIS1"]), ""), _card("NAXIS2", int(h["NAXIS2"]), ""),
             _card("CTYPE1", "RA---TAN", "the canonical compose product's field (D2)"), _card("CTYPE2", "DEC--TAN", ""),
             _card("CRVAL1", float(h["CRVAL1"]), "deg"), _card("CRVAL2", float(h["CRVAL2"]), "deg"),
             _card("CRPIX1", float(h["CRPIX1"]), ""), _card("CRPIX2", float(h["CRPIX2"]), ""),
             _card("CUNIT1", "deg", ""), _card("CUNIT2", "deg", ""), _card("EQUINOX", 2000.0, ""),
             _card("CD1_1", cd[0][0], ""), _card("CD1_2", cd[0][1], ""), _card("CD2_1", cd[1][0], ""), _card("CD2_2", cd[1][1], ""),
             "END"]
    with open(out, "w") as f:
        f.write("\n".join(cards) + "\n")
    return int(h["NAXIS1"]), int(h["NAXIS2"])


def write_norm(seqstat_csv, members_dir, ref_path, out):
    """The addscale terms from Siril `seqstat ... full` (tab-separated: image chan mean
    median sigma min max noise avgDev mad sqrtbwmv location scale; image = the linked
    order = the curated dir's sorted order, chan 0/1/2 = R/G/B). Per member per channel:
    fscale = s_ref/s_i and back_default = loc_i - loc_ref * (s_i/s_ref) (D4), so that
    SWarp's (v - back)*fscale equals Siril's (v - loc_i)*(s_ref/s_i) + loc_ref."""
    names = sorted(f[:-4] for f in os.listdir(members_dir) if f.endswith(".fit"))
    real = [os.path.realpath(os.path.join(members_dir, n + ".fit")) for n in names]
    ref = os.path.realpath(ref_path)
    assert ref in real, f"the reference {ref} is not one of the {len(names)} members"
    iref = real.index(ref) + 1
    stats = {}
    with open(seqstat_csv) as f:
        header = f.readline().split()
        ic, il, isc = header.index("image"), header.index("location"), header.index("scale")
        ich = header.index("chan")
        for line in f:
            p = line.split()
            if len(p) <= isc:
                continue
            stats[(int(p[ic]), int(p[ich]))] = (float(p[il]), float(p[isc]))
    with open(out, "w") as f:
        f.write("member,channel,location,scale,fscale,back_default\n")
        for i, n in enumerate(names, 1):
            for ch, c in enumerate("RGB"):
                loc, s = stats[(i, ch)]; loc_r, s_r = stats[(iref, ch)]
                fscale = s_r / s
                back = loc - loc_r * (s / s_r)
                f.write(f"{n},{c},{loc:.9e},{s:.9e},{fscale:.9f},{back:.9e}\n")
    return len(names), iref


def selftest():
    fails = 0
    def check(name, cond, detail=""):
        nonlocal fails
        print(f"  {'PASS' if cond else 'FAIL'}  {name} {detail}")
        fails += 0 if cond else 1
    # the taper's anchors
    x = np.array([0.0, 3000.0, 3150.0, 3300.0, 5000.0]); t = taper(x, 3000.0, 0.02, 300)
    check("taper anchors: 1 inside, (1+tmin)/2 at mid-ramp, tmin at the end and beyond",
          abs(t[0] - 1) < 1e-12 and abs(t[1] - 1) < 1e-12 and abs(t[2] - 0.51) < 1e-9 and abs(t[3] - 0.02) < 1e-12 and abs(t[4] - 0.02) < 1e-12, str(t))
    check("taper never zero", t.min() > 0)
    check("taper monotone non-increasing", np.all(np.diff(taper(np.arange(0, 6000.0), 3000.0, 0.02, 300)) <= 1e-12))
    # a synthetic SIP header -> TPV cards (data-free)
    h = fits.Header()
    for k, v in {"NAXIS": 2, "NAXIS1": 400, "NAXIS2": 300, "CTYPE1": "RA---TAN-SIP", "CTYPE2": "DEC--TAN-SIP", "CRVAL1": 310.0, "CRVAL2": 43.0,
                 "CRPIX1": 200.0, "CRPIX2": 150.0, "CD1_1": -4.7e-3, "CD1_2": 1.0e-5, "CD2_1": 1.2e-5, "CD2_2": 4.7e-3,
                 "A_ORDER": 2, "B_ORDER": 2, "A_2_0": 1e-7, "A_0_2": -2e-7, "A_1_1": 3e-8, "B_2_0": 2e-7, "B_0_2": 1e-7, "B_1_1": -4e-8}.items():
        h[k] = v
    try:
        cards = head_cards(h, flxscale=1.5)
        keys = [c.split("=")[0].strip() for c in cards if "=" in c]
        check("head: CTYPE TPV + PV terms + CD + FLXSCALE + END",
              "CTYPE1" in keys and any(k.startswith("PV1_") for k in keys) and any(k.startswith("PV2_") for k in keys) and "CD1_1" in keys and "FLXSCALE" in keys and cards[-1] == "END", f"{len(cards)} cards")
        check("head: NO PC/CDELT cards (the dual-matrix trap; SWarp ignores them, astropy misreads TPV with them)",
              not any(k.startswith(("PC", "CDELT")) for k in keys))
    except ImportError as e:
        check("head: sip_tpv importable (run under /opt/astro-venv/bin/python)", False, str(e))
    check("head cards <= 80 chars", all(len(c) <= 80 for c in cards) if fails == 0 else True)
    print(f"swarp_weight_maps --selftest: {'PASS' if fails == 0 else f'{fails} FAILED'}")
    return 0 if fails == 0 else 1


def main():
    a = sys.argv[1:]
    if not a or a[0] == "--selftest":
        sys.exit(selftest())
    opts = {k.lstrip("-"): v for k, v in (s.split("=", 1) for s in a if s.startswith("--") and "=" in s)}
    pos = [s for s in a if not s.startswith("--")]
    cmd = pos[0]
    if cmd == "head":
        n = write_head(pos[1], pos[2], float(opts["flxscale"]) if "flxscale" in opts else None)
        print(f"  head -> {pos[2]} ({n} cards, TPV)")
    elif cmd == "weight":
        W, H, lo, hi = write_weight(pos[1], pos[2], int(opts["stackcnt"]), int(opts["xc"]) if "xc" in opts else None,
                                    float(opts.get("tmin", 0.02)), int(opts.get("taper", 300)))
        print(f"  weight -> {pos[2]} ({W}x{H}, w {lo:.3f}..{hi:.1f})")
    elif cmd == "norm":
        n, iref = write_norm(pos[1], pos[2], pos[3], pos[4])
        print(f"  norm -> {pos[4]} ({n} members x RGB, reference index {iref})")
    elif cmd == "coadd-head":
        W, H = write_coadd_head(pos[1], pos[2])
        print(f"  coadd.head -> {pos[2]} ({W}x{H}, TAN)")
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
