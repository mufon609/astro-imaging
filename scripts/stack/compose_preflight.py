#!/usr/bin/env python3
"""Compose preflight: STOP before a union silently regresses to star-pair.

Usage: compose_preflight.py <member.fit>... [--json=<out>] [--selftest]

WHY THIS EXISTS — one MEASURED failure, and it is the largest defect this
project has shipped.

The cross-set/cross-night union used `register -2pass`: one star-pair homography
per member against a common reference. The members' optical axes span 13 deg of
RA across two nights, and a single projective fit cannot carry that. Measured on
the 28-member union at RA 294.86:

    register -2pass (star-pair) ....  FWHM 4.383 px / roundness 0.458
    seqplatesolve  (astrometric) ..   FWHM 2.678 px / roundness 0.974

The clean band of the same union reads 0.961-0.968, so the astrometric route
does not improve the defect — it removes it, with no regression in the clean
band (0.968 -> 0.961, inside noise) and star counts within 1-2%. It also covers
MORE sky (800.1 against 773.5 sq.deg) and lands north-up instead of inheriting
whatever orientation the pinned reference member happened to have.

The information was always there: the members' own astrometric solutions place
the same stars within 0.10 px median / 0.26 px p90 at exactly the sky where the
homography lost 0.34 of roundness. The homography is what discarded it.

WHAT MAKES THAT ROUTE POSSIBLE, AND WHAT THIS GUARDS. `seqplatesolve` derives
registration from each member's OWN plate solution, and `seqapplyreg` then
applies that member's OWN SIP undistortion before projecting. Both require every
member to carry a WCS *with SIP order >= 2*. A member that is unsolved, or
solved LINEAR-only, silently costs the undistortion that is the whole point —
and siril will not say so: it registers what it can and exports a product that
looks finished. That is the same shape as the darktable trap
(`lens_preflight.py`): the tool never fails, so the CHAIN must assert.

Two distinct hard failures, reported separately because the fixes differ:
  NO WCS   -> the member was never solved. Run scripts/calibrate/solve_field.py
              with --inject before composing.
  NO SIP   -> solved, but linear only (no A_ORDER, or A_ORDER < 2). Re-solve;
              siril's own platesolve takes -order=, solve_field.py emits SIP by
              default. Registration would still run and would still discard the
              per-member distortion.

Header-only (astropy). No pixel is read here, nothing is decided: it reports and
STOPS, and the caller does not proceed. `--selftest` executes the falsification —
it builds a good and a bad header and asserts this guard accepts the one and
rejects the other, so a guard that has quietly stopped guarding is detectable.

REMOVAL CONDITION: retires when the compose stage cannot run without per-member
astrometric registration at all — i.e. when siril itself refuses to register a
sequence whose members lack a usable solution, or when the chain has no
star-pair path left to fall back to.
"""
import json
import os
import sys


def check(path):
    """Header-only verdict for one member. Returns (ok, kind, detail)."""
    from astropy.io import fits
    if not os.path.exists(path):
        return False, "MISSING", "file does not exist"
    try:
        h = fits.getheader(path)
    except Exception as e:                                  # unreadable header
        return False, "UNREADABLE", str(e)[:80]
    have_wcs = all(k in h for k in ("CRVAL1", "CRVAL2", "CRPIX1", "CRPIX2")) and (
        all(k in h for k in ("CD1_1", "CD1_2", "CD2_1", "CD2_2"))
        or all(k in h for k in ("CDELT1", "CDELT2")))
    if not have_wcs:
        return False, "NO_WCS", "no plate solution in the header"
    order = h.get("A_ORDER")
    if order is None or int(order) < 2:
        return False, "NO_SIP", (f"solved but LINEAR only (A_ORDER={order}) — "
                                 "per-member undistortion would be discarded")
    ctype = str(h.get("CTYPE1", ""))
    if "TAN" not in ctype.upper():
        return False, "NOT_TAN", f"CTYPE1={ctype!r}, expected a TAN projection"
    return True, "OK", (f"A_ORDER={int(order)} CRVAL="
                        f"{float(h['CRVAL1']):.3f},{float(h['CRVAL2']):+.3f}")


def selftest():
    """Falsify the guard: it must ACCEPT a solved+SIP header and REJECT each
    failure mode. A guard that has stopped guarding fails here."""
    import tempfile
    import numpy as np
    from astropy.io import fits
    ok = True
    with tempfile.TemporaryDirectory() as d:
        base = {"CRVAL1": 300.0, "CRVAL2": 42.0, "CRPIX1": 100.0, "CRPIX2": 100.0,
                "CD1_1": -4.7e-3, "CD1_2": 0.0, "CD2_1": 0.0, "CD2_2": 4.7e-3,
                "CTYPE1": "RA---TAN-SIP", "CTYPE2": "DEC--TAN-SIP", "A_ORDER": 3}
        cases = [("good", base, True, "OK"),
                 ("no_wcs", {k: v for k, v in base.items()
                             if k not in ("CRVAL1", "CRVAL2")}, False, "NO_WCS"),
                 ("linear", {k: v for k, v in base.items() if k != "A_ORDER"},
                  False, "NO_SIP"),
                 ("order1", {**base, "A_ORDER": 1}, False, "NO_SIP"),
                 ("not_tan", {**base, "CTYPE1": "RA---SIN"}, False, "NOT_TAN")]
        for name, hdr, want_ok, want_kind in cases:
            p = os.path.join(d, f"{name}.fit")
            hdu = fits.PrimaryHDU(np.zeros((4, 4), dtype="float32"))
            for k, v in hdr.items():
                hdu.header[k] = v
            hdu.writeto(p)
            got_ok, got_kind, _ = check(p)
            good = (got_ok == want_ok and got_kind == want_kind)
            ok &= good
            print(f"  [{'PASS' if good else 'FAIL'}] {name:8s} "
                  f"expected {want_kind:9s} got {got_kind}")
        missing_ok, missing_kind, _ = check(os.path.join(d, "nope.fit"))
        good = (not missing_ok and missing_kind == "MISSING")
        ok &= good
        print(f"  [{'PASS' if good else 'FAIL'}] absent   expected MISSING   "
              f"got {missing_kind}")
    print("SELFTEST", "PASS — the guard still guards" if ok else "FAIL")
    return 0 if ok else 1


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    opts = dict(a[2:].split("=", 1) if "=" in a else (a[2:], "1")
                for a in sys.argv[1:] if a.startswith("--"))
    if "selftest" in opts:
        sys.exit(selftest())
    if not args:
        sys.exit(__doc__)
    rows, bad = [], []
    for p in args:
        ok, kind, detail = check(p)
        rows.append({"member": p, "ok": ok, "kind": kind, "detail": detail})
        if not ok:
            bad.append((p, kind, detail))
    if "json" in opts:
        json.dump({"n": len(rows), "n_bad": len(bad), "members": rows},
                  open(opts["json"], "w"), indent=1)
    if bad:
        print(f"\ncompose_preflight: REFUSING TO COMPOSE — {len(bad)} of "
              f"{len(rows)} members cannot carry astrometric registration.\n",
              file=sys.stderr)
        for p, kind, detail in bad:
            print(f"  {kind:10s} {os.path.basename(p)}  — {detail}", file=sys.stderr)
        print("\n  Why this is fatal and not a warning: without a per-member "
              "solution the compose\n  falls back to ONE star-pair homography per "
              "member, which is MEASURED at\n  roundness 0.458 against 0.974 on "
              "this corpus' 28-member union — the largest\n  defect this project "
              "has shipped, and siril reports nothing when it happens.\n"
              "\n  Fix: scripts/calibrate/solve_field.py <member> --inject=<member> "
              "for each\n  member listed above, then re-run.\n", file=sys.stderr)
        sys.exit(2)
    print(f"compose_preflight: {len(rows)}/{len(rows)} members carry a TAN+SIP "
          f"solution — astrometric registration is available")
    for r in rows[:3]:
        print(f"    {os.path.basename(r['member'])}  {r['detail']}")
    if len(rows) > 3:
        print(f"    … and {len(rows)-3} more")


if __name__ == "__main__":
    main()
