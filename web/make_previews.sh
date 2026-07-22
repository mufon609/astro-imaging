#!/usr/bin/env bash
# Generate the browser SELECTION surfaces for a session — every pixel op is
# Siril's (load / autostretch / resample / savepng); this script only
# orchestrates and records the manifest. Outputs are NAVIGATION previews,
# never judgment surfaces (judgment = the full PNG16 in the user's viewers).
#
#   web/make_previews.sh <session> [--maxdim-thumb=1600] [--maxdim-sel=2200]
#                                  [--cov-min=25]
#
# Writes into web/results/<session>/previews/:
#   thumb_<judge-name>.png   downscaled gallery thumbs of judge/ surfaces
#   sel_<stack-stem>.png     linked-autostretch selection surface per
#                            *_max_spcc.fit stack (the crop UI's canvas)
#   cov_<map-stem>_lt<N>.png coverage VEIL per coverage_*.fit map: white where
#                            member coverage < N (Siril pm iif threshold at
#                            N*1000/65535 in pm's [0,1] domain), area-downscaled
#                            — the crop UI tints it as the insufficient-coverage
#                            layer. Falls back to covheat_<map-stem>.png (plain
#                            autostretch heat) if the pm arm fails.
#   manifest.json            native dims + preview dims + EXACT scale per item,
#                            plus any matching crop-map reference boxes found
#                            in datasets/<session>/*/qa_work/*_map.json
# The generated .ssf lives under sessions/<session>/work/ (flatpak-visible —
# CLAUDE.md environment rule) and pins setcompress 0.
set -euo pipefail
REPO=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
SESSION=${1:?usage: make_previews.sh <session> [--maxdim-thumb=] [--maxdim-sel=]}
shift || true
TH=1600 SEL=2200 COVMIN=25
for a in "$@"; do case "$a" in
  --maxdim-thumb=*) TH=${a#*=};; --maxdim-sel=*) SEL=${a#*=};;
  --cov-min=*) COVMIN=${a#*=};;
  *) echo "unknown arg $a" >&2; exit 1;;
esac; done
SBASE=$(basename "$SESSION")
RES=$REPO/web/results/$SBASE
PREV=$RES/previews
WORK=$REPO/sessions/$SBASE/work
[ -d "$RES" ] || { echo "no results tree: $RES" >&2; exit 1; }
mkdir -p "$PREV" "$WORK"
SSF=$WORK/previews_gen.ssf

{ echo "requires 1.4.0"; echo "setcompress 0"
  # gallery thumbs: judge PNGs -> downscale (16-bit PNG stays 16-bit)
  if [ -d "$RES/judge" ]; then
    for p in "$RES"/judge/*.png; do
      [ -e "$p" ] || continue
      n=$(basename "$p" .png)
      echo "load $p"
      echo "resample -maxdim=$TH -interp=area"
      echo "savepng $PREV/thumb_$n"
    done
  fi
  # crop-UI selection surfaces: each *_max_spcc stack, linked autostretch
  for f in "$RES"/stack_*_max_spcc.fit; do
    [ -e "$f" ] || continue
    stem=$(basename "$f" .fit)
    echo "load $f"
    echo "autostretch -linked"
    echo "resample -maxdim=$SEL -interp=area"
    echo "savepng $PREV/sel_$stem"
  done
} > "$SSF"

flatpak run --command=siril-cli org.siril.Siril -d "$WORK" -s "$SSF" \
  > "$WORK/previews_gen.log" 2>&1 \
  || { echo "siril preview run FAILED — $WORK/previews_gen.log" >&2; exit 1; }

# coverage veils: separate ssf per map so a pm failure cannot kill the main
# previews; fallback = plain autostretch heat of the map (still tool-made)
THR=$(awk -v n="$COVMIN" 'BEGIN{printf "%.6f", n*1000/65535}')
for map in "$RES"/coverage_*.fit; do
  [ -e "$map" ] || continue
  stem=$(basename "$map" .fit)
  CSSF=$WORK/previews_cov.ssf
  { echo "requires 1.4.0"; echo "setcompress 0"
    echo "cd $RES"
    echo "pm \"iif(\$$stem\$ < $THR, 1, 0)\""
    echo "resample -maxdim=$SEL -interp=area"
    echo "savepng $PREV/cov_${stem}_lt$COVMIN"
  } > "$CSSF"
  if ! flatpak run --command=siril-cli org.siril.Siril -d "$WORK" -s "$CSSF" \
      >> "$WORK/previews_gen.log" 2>&1; then
    echo "pm veil failed for $stem — falling back to heat (previews_gen.log)"
    { echo "requires 1.4.0"; echo "setcompress 0"
      echo "load $map"; echo "autostretch"
      echo "resample -maxdim=$SEL -interp=area"
      echo "savepng $PREV/covheat_$stem"
    } > "$CSSF"
    flatpak run --command=siril-cli org.siril.Siril -d "$WORK" -s "$CSSF" \
      >> "$WORK/previews_gen.log" 2>&1 \
      || echo "coverage heat fallback ALSO failed for $stem" >&2
  fi
done

# manifest: native + preview dims and the exact scale, from file headers
# (astropy header read for FITS; PNG IHDR for previews — metadata only,
# no pixel analysis). Reference boxes: any *_map.json whose recorded canvas
# matches a selection surface's native dims is attached to that item.
python3 - "$REPO" "$SBASE" "$PREV" "$COVMIN" <<'PY'
import glob, json, os, struct, sys
repo, session, prev, covmin = sys.argv[1:5]
res = os.path.join(repo, "web", "results", session)

def png_wh(path):
    with open(path, "rb") as f:
        head = f.read(33)
    if head[:8] != b"\x89PNG\r\n\x1a\n" or head[12:16] != b"IHDR":
        raise ValueError(f"not a PNG: {path}")
    w, h = struct.unpack(">II", head[16:24])
    return int(w), int(h)

def fits_wh(path):
    from astropy.io import fits
    with fits.open(path) as h:
        hdr = h[0].header
    return int(hdr["NAXIS1"]), int(hdr["NAXIS2"])

maps = []
for mp in glob.glob(os.path.join(repo, "datasets", session, "*", "qa_work",
                                 "*_map.json")):
    try:
        d = json.load(open(mp))
        cw, chh = d.get("new_canvas") or (None, None)
        x, y, w, h = d.get("siril_crop_args") or (None,) * 4
        if None not in (cw, chh, x, y, w, h):
            maps.append({"record": os.path.relpath(mp, repo),
                         "canvas": [int(cw), int(chh)],
                         "siril_crop_args": [int(x), int(y), int(w), int(h)]})
    except (ValueError, TypeError):
        pass

items = []
for p in sorted(glob.glob(os.path.join(res, "judge", "*.png"))):
    n = os.path.basename(p)
    t = os.path.join(prev, "thumb_" + n)
    if os.path.exists(t):
        items.append({"kind": "judge", "name": n,
                      "file": f"judge/{n}", "thumb": f"previews/thumb_{n}"})
for f in sorted(glob.glob(os.path.join(res, "stack_*_max_spcc.fit"))):
    stem = os.path.basename(f)[:-4]
    sp = os.path.join(prev, f"sel_{stem}.png")
    if not os.path.exists(sp):
        continue
    nw, nh = fits_wh(f)
    pw, ph = png_wh(sp)
    refs = [m for m in maps if m["canvas"] == [nw, nh]]
    items.append({"kind": "selection", "product": stem,
                  "file": os.path.basename(f), "native_wh": [nw, nh],
                  "preview": f"previews/sel_{stem}.png",
                  "preview_wh": [pw, ph],
                  "scale": pw / nw,
                  "reference_boxes": refs,
                  "note": "SELECTION surface (linked autostretch + area "
                          "downscale by Siril) — never a judgment surface"})
for f in sorted(glob.glob(os.path.join(res, "coverage_*.fit"))):
    stem = os.path.basename(f)[:-4]
    veil = os.path.join(prev, f"cov_{stem}_lt{covmin}.png")
    heat = os.path.join(prev, f"covheat_{stem}.png")
    p = veil if os.path.exists(veil) else heat if os.path.exists(heat) else None
    if not p:
        continue
    nw, nh = fits_wh(f)
    pw, ph = png_wh(p)
    items.append({"kind": "coverage", "map": os.path.basename(f),
                  "style": "veil-below" if p == veil else "heat",
                  "threshold_members": int(covmin) if p == veil else None,
                  "canvas": [nw, nh],
                  "preview": f"previews/{os.path.basename(p)}",
                  "preview_wh": [pw, ph], "scale": pw / nw,
                  "note": "coverage overlay (Siril pm threshold / autostretch "
                          "of the probe map) — a navigation layer for the "
                          "crop UI, matched to products by canvas"})
out = {"session": session, "items": items}
mf = os.path.join(prev, "manifest.json")
json.dump(out, open(mf, "w"), indent=1)
print(f"[previews] {len(items)} items -> {os.path.relpath(mf, repo)}")
PY
