#!/usr/bin/env python3
"""JWST archival acquisition driver (MAST) — query / list / download / verify.

The archival class's ACQUISITION stage: no photons are shot; acquiring means
querying MAST and pulling the OFFICIAL upstream pipeline's products. This
script drives `astroquery.mast` (the sanctioned scripted route) and records
what was fetched; it reads FITS HEADERS only, never pixels.

Contract (mirrors the web execution surface):
  - `query` and `list` are read-only reconnaissance; `list` prints every
    candidate file WITH ITS SIZE and the total GB — the DECIDE surface.
  - `download` REFUSES to run without --go (the user's explicit gate), and
    writes a resumable curl script for bulk pulls (the STScI-recommended
    bulk route) unless --direct.
  - `verify` opens each product with astropy, requires SCI + a parsing WCS,
    and captures the reproducibility anchors (CAL_VER, CRDS_CTX — which
    quarterly STScI build produced the product) into the tracked
    datasets/<session>/acquisition_manifest.json.
  - Public JWST data needs no MAST account or token (EAP data is out of
    scope here).

Layout: products stage into sessions/<session>/products/ (gitignored bulk);
the tracked record lives at datasets/<session>/acquisition_manifest.json.
Product doctrine: per-filter stage-3 `_i2d` mosaics (calib_level=3,
SCIENCE/I2D) — what press-release composites are built from. Deps
(astroquery) auto-bootstrap into ~/.local/share/jwst-venv on first run
(the solve_field.py venv precedent).
"""
import argparse
import json
import os
import subprocess
import sys

VENV = os.path.expanduser("~/.local/share/jwst-venv")
REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def ensure_venv():
    """Re-exec inside the jwst venv, creating it (astroquery + astropy) on
    first run. Loud, resumable, no side effects beyond the venv dir."""
    vpy = os.path.join(VENV, "bin", "python3")
    # NEVER compare interpreter realpaths here: the venv python3 is a SYMLINK
    # to the system interpreter, so realpath collapses them and the re-exec
    # gets skipped once the venv exists. sys.prefix is the venv identity.
    if os.path.abspath(sys.prefix) == os.path.abspath(VENV):
        return
    if not os.path.exists(vpy):
        print(f"[jwst-venv] bootstrapping {VENV} (astroquery)...", flush=True)
        subprocess.run([sys.executable, "-m", "venv", VENV], check=True)
        subprocess.run([vpy, "-m", "pip", "install", "--quiet",
                        "astroquery", "astropy"], check=True)
    os.execv(vpy, [vpy] + sys.argv)


def obs_query(args):
    from astroquery.mast import Observations
    crit = dict(obs_collection="JWST", proposal_id=str(args.proposal),
                dataproduct_type="image", calib_level=args.calib_level)
    if args.instrument:
        crit["instrument_name"] = args.instrument
    obs = Observations.query_criteria(**crit)
    if len(obs) == 0:
        print("no observations matched", file=sys.stderr)
        sys.exit(1)
    cols = ["obs_id", "filters", "t_exptime", "calib_level", "obsid"]
    obs[cols].pprint(max_lines=-1, max_width=-1)
    print(f"\n{len(obs)} observation(s).")
    return obs


def product_list(args):
    from astropy.table import unique, vstack
    from astroquery.mast import Observations
    obs = obs_query(args)
    chunks = [Observations.get_product_list(obs[i:i + 5])
              for i in range(0, len(obs), 5)]           # STScI bulk guidance
    plist = unique(vstack(chunks), keys="productFilename")
    sel = Observations.filter_products(
        plist, productType="SCIENCE",
        productSubGroupDescription=args.subgroup, calib_level=args.calib_level)
    if args.filters:
        want = {f.strip().lower() for f in args.filters.split(",")}
        keep = [any(w in fn.lower() for w in want)
                for fn in sel["productFilename"]]
        sel = sel[keep]
    total = sum(int(s) for s in sel["size"])
    for row in sel:
        print(f"{int(row['size'])/1e6:9.1f} MB  {row['productFilename']}")
    print(f"\n{len(sel)} file(s), TOTAL {total/1e9:.2f} GB "
          f"-> decide, then re-run with 'download --go'")
    return sel


def download(args):
    if not args.go:
        print("REFUSED: download runs only with an explicit --go "
              "(the decide gate; run 'list' first for sizes)", file=sys.stderr)
        sys.exit(2)
    import glob
    import shutil
    from astroquery.mast import Observations
    sel = product_list(args)
    dest = os.path.join(REPO, "sessions", args.session, "products")
    os.makedirs(dest, exist_ok=True)
    if args.direct:
        print(Observations.download_products(sel, download_dir=dest, flat=True))
        return
    # curl route: the API call only WRITES the resumable script — the --go the
    # operator gave covers the PULL, so run it here (its output is the
    # progress; re-running resumes a partial pull)
    Observations.download_products(sel, download_dir=dest, curl_flag=True)
    scripts = sorted(glob.glob(os.path.join(dest, "mastDownload_*.sh")))
    if not scripts:
        print("DOWNLOAD FAIL: MAST returned no curl script", file=sys.stderr)
        sys.exit(1)
    print(f"pulling via {os.path.basename(scripts[-1])} ...", flush=True)
    subprocess.run(["bash", scripts[-1]], cwd=dest, check=True)
    # the bundle script writes a MAST_*/ tree — flatten into products/
    moved = 0
    for f in glob.glob(os.path.join(dest, "**", "*.fits"), recursive=True):
        if os.path.dirname(f) != dest:
            shutil.move(f, os.path.join(dest, os.path.basename(f)))
            moved += 1
    for d in sorted(glob.glob(os.path.join(dest, "MAST_*")), reverse=True):
        shutil.rmtree(d, ignore_errors=True)
    got = glob.glob(os.path.join(dest, "*.fits"))
    total = sum(os.path.getsize(f) for f in got)
    print(f"DOWNLOAD OK: {len(got)} fits ({total/1e9:.2f} GB) in {dest} "
          f"({moved} flattened) — run 'verify'")


def verify(args):
    from astropy.io import fits
    from astropy.wcs import WCS
    dest = os.path.join(REPO, "sessions", args.session, "products")
    rows, bad = [], []
    for fn in sorted(os.listdir(dest)):
        if not fn.endswith(".fits"):
            continue
        path = os.path.join(dest, fn)
        try:
            with fits.open(path) as hdul:
                sci = hdul["SCI"]
                WCS(sci.header)                      # must parse
                h0, hs = hdul[0].header, sci.header
                rows.append({
                    "file": fn,
                    "instrument": h0.get("INSTRUME"),
                    "filter": h0.get("FILTER") or h0.get("PUPIL"),
                    "target": h0.get("TARGNAME"),
                    "date_obs": h0.get("DATE-OBS"),
                    "bunit": hs.get("BUNIT"),
                    "shape": [sci.header.get("NAXIS2"), sci.header.get("NAXIS1")],
                    "cal_ver": h0.get("CAL_VER"),
                    "crds_ctx": h0.get("CRDS_CTX"),
                    "size_bytes": os.path.getsize(path),
                })
        except Exception as e:                       # loud, per file
            bad.append({"file": fn, "error": str(e)})
    record = {"session": args.session,
              "products": rows, "failed_verify": bad,
              "why": "acquisition manifest — the tracked record of what was "
                     "fetched from MAST; cal_ver/crds_ctx pin the STScI "
                     "quarterly build that produced each product "
                     "(reproducibility anchors)"}
    ds = os.path.join(REPO, "datasets", args.session)
    os.makedirs(ds, exist_ok=True)
    if not rows and not bad:
        print(f"VERIFY FAIL: no .fits products under {dest} — the download "
              f"did not stage anything (nothing recorded)", file=sys.stderr)
        sys.exit(1)
    out = os.path.join(ds, "acquisition_manifest.json")
    json.dump(record, open(out, "w"), indent=1)
    print(f"{len(rows)} verified, {len(bad)} failed -> {out}")
    if bad:
        for b in bad:
            print(f"  FAIL {b['file']}: {b['error']}", file=sys.stderr)
        sys.exit(1)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    common = dict(proposal=lambda p: p.add_argument("--proposal", required=True),
                  instrument=lambda p: p.add_argument("--instrument", default="NIRCAM*"),
                  level=lambda p: p.add_argument("--calib-level", type=int, default=3),
                  subgroup=lambda p: p.add_argument("--subgroup", default="I2D"),
                  filters=lambda p: p.add_argument(
                      "--filters", help="comma list matched against filenames, e.g. f212n,f335m"),
                  session=lambda p: p.add_argument(
                      "--session", required=True, help="sessions/<session> staging + datasets/<session> records"))
    q = sub.add_parser("query");    [common[k](q) for k in ("proposal", "instrument", "level")]
    l = sub.add_parser("list");     [common[k](l) for k in ("proposal", "instrument", "level", "subgroup", "filters")]
    d = sub.add_parser("download"); [common[k](d) for k in ("proposal", "instrument", "level", "subgroup", "filters", "session")]
    d.add_argument("--go", action="store_true", help="the explicit decide gate")
    d.add_argument("--direct", action="store_true", help="direct download instead of the resumable curl script")
    v = sub.add_parser("verify");   common["session"](v)
    args = ap.parse_args()
    if getattr(args, "session", None):
        # the jwst- prefix is the system's on-disk labelling, not the
        # operator's to type — normalize a bare target slug here too
        s = args.session.strip().lower()
        args.session = s if s.startswith("jwst-") else "jwst-" + s
    {"query": obs_query, "list": product_list,
     "download": download, "verify": verify}[args.cmd](args)


if __name__ == "__main__":
    ensure_venv()
    main()
