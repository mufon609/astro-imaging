#!/usr/bin/env bash
# RENDER TIER — the aesthetic finish, past the diagnostic judge surface.
# Separates stars, denoises the gas, stretches each layer on its own terms, and
# screen-recombines. Every pixel op is an official tool's (Siril starnet / mtf /
# asinh / pm; Cosmic Clarity denoise); this sequences them and records the knobs.
#
#   render_tier.sh <linear-spcc-stack.fit> <name> --session=<dir> --set=<set>
#                  [--sky=0.10] [--gas-top=0.16] [--black-k=4]
#                  [--lum=0.6] [--chroma=0.85] [--stars=1000]
#                  [--no-separate] [--no-denoise] [--plan]
#
# THE GATE (the chain's own pattern: derive -> propose -> user ratifies -> run).
# The render block in datasets/<session>/<set>/recipe.json PINS every knob. When
# it is absent this script DERIVES a proposal from Siril-measured statistics,
# writes it as `render.proposed`, prints it, and STOPS with exit 7. Nothing
# aesthetic runs on a knob the user has not seen. Move the block to `render` to
# ratify it; re-running then executes exactly those numbers.
#
# WHY THE STRETCH POINTS ARE PROPORTIONAL, NOT ABSOLUTE. On this data class the
# sky sits only ~7% above the black point, so a COMMON black point turns sub-1%
# linear colour differences into a ~10% render cast (measured: a first pass put
# B/G at 0.90 where the linear data was 0.995). Setting low and high as a
# FRACTION of each channel's own median makes (sky - low) keep the linear ratio
# by construction — verified to four decimals (R/G 1.0022 B/G 1.0048 vs linear
# 1.0024 / 1.0047). The black-point depth comes from Siril's own MAD, the same
# statistic autostretch uses, so it is tool-measured rather than eyeballed.
#
# WHAT NO PARAMETER FIXES: a nonlinear curve cannot preserve channel ratios —
# channels enter at different points and leave with different local slopes, so
# ~5-7% colour error remains at the bright end. `asinh -human` (which preserves
# L*a*b* lightness) splits that error more evenly but costs contrast. Both are
# legitimate; the choice is aesthetic and therefore the user's.
#
# ORDER follows the researched mainstream (docs/graxpert-3x-and-workflow-order.md):
# background extraction -> colour calibration -> [deconvolution] -> star removal
# -> noise reduction on the starless -> stretch -> recomposition. Deconvolution
# is SKIPPED here by design: classical RL is a measured dead end on in-exposure
# trailing, BlurXTerminator is not installed, and GraXpert's is the immature path.
# The consensus "deconvolve before removing stars" therefore does not bind.
#
# GUARDS, all measured and fatal:
# - the separation must screen-recombine to the original (invertible split);
# - the denoise must not eat the object: a BLANK-SKY control must lose MORE
#   band-pass power than an OBJECT region at every scale. A region-mean contrast
#   check and a smoothed-sigma check are BOTH BLIND to the 3-8px band where
#   resolution-limit detail lives and will pass a denoiser that flattens it.
set -euo pipefail
REPO=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
STACK=${1:?usage: render_tier.sh <stack.fit> <name> --session= --set= [opts]}
NAME=${2:?missing <name>}
SESSION= SET= SKY=0.10 GASTOP=0.16 BLACKK=4 LUM=0.6 CHROMA=0.85 STARS=1000
SEPARATE=1 DENOISE=1 PLAN=0
for a in "${@:3}"; do case "$a" in
  --session=*) SESSION=${a#*=};; --set=*) SET=${a#*=};;
  --sky=*) SKY=${a#*=};; --gas-top=*) GASTOP=${a#*=};; --black-k=*) BLACKK=${a#*=};;
  --lum=*) LUM=${a#*=};; --chroma=*) CHROMA=${a#*=};; --stars=*) STARS=${a#*=};;
  --no-separate) SEPARATE=0;; --no-denoise) DENOISE=0;; --plan) PLAN=1;;
  *) echo "unknown arg $a" >&2; exit 1;;
esac; done
[ -f "$STACK" ] || { echo "no such stack: $STACK" >&2; exit 1; }
[ -n "$SESSION" ] && [ -n "$SET" ] || { echo "need --session= --set=" >&2; exit 1; }
SESSION=$(cd "$SESSION" && pwd); SNAME=$(basename "$SESSION")
STACK=$(cd "$(dirname "$STACK")" && pwd)/$(basename "$STACK")
RES=$REPO/web/results/$SNAME; DSET=$REPO/datasets/$SNAME/$SET
RECIPE=$DSET/recipe.json
W=$SESSION/work/render_$NAME
CC=/opt/cosmicclarity-6.6
say(){ echo "[render $NAME] $*"; }
sir(){ flatpak run --command=siril-cli org.siril.Siril -d "$W" -s "$1" >> "$W/siril.log" 2>&1; }

mkdir -p "$W" "$RES/judge" "$DSET"
: > "$W/siril.log"

# ---- 1. tool-measured statistics (Siril stat: median + MAD per channel) ----
say "measuring the stack (Siril stat)"
# `stat main` (not plain `stat`): the short form reports Sigma, which on a
# star-containing stack is inflated by the stars (measured 138 against a MAD of
# 1.7 on the same layer) and would drive the black point far below zero. MAD is
# the robust statistic and is what autostretch's shadow clip is built on.
# Siril reports float images in 16-bit ADU while `mtf` takes normalized [0,1],
# so everything is divided by 65535 here — mixing those scales silently
# produces a black point ~65000x too deep.
# `fmul 100` BEFORE measuring (nothing is saved, so the file is untouched).
# Siril prints stat to 0.1 ADU, which on a sky of ~50 ADU is 0.2% — and because
# the sky sits only ~14% above the black point, that 0.2% becomes a ~1.4% error
# in (sky - low) PER CHANNEL and casts the render's background by several
# percent. Scaling up first makes the same quantum 100x finer. Median and MAD
# are robust statistics, so the bright end clipping at the top of the range does
# not affect them.
printf 'requires 1.4.0\nsetcompress 0\nload %s\nfmul 100\nstat main\n' "$STACK" > "$W/stat.ssf"
sir "$W/stat.ssf"
STATS=$(python3 - "$W/siril.log" <<'PY'
import re, sys
SCALE = 100.0 * 65535.0            # the fmul factor x Siril's 16-bit reporting
med, mad = [], []
for line in open(sys.argv[1]):
    m = re.search(r"\w+ layer: .*?Median: ([0-9.eE+-]+),.*?MAD: ([0-9.eE+-]+)", line)
    if m:
        med.append(float(m.group(1)) / SCALE)
        mad.append(float(m.group(2)) / SCALE)
if len(med) < 3:
    sys.exit("could not parse three layers with MAD from `stat main`")
print(" ".join(f"{v:.10f}" for v in med[:3]))
print(" ".join(f"{v:.10f}" for v in mad[:3]))
PY
) || { echo "stat parse failed — read $W/siril.log" >&2; exit 1; }
{ read -r MEDS; read -r MADS; } <<< "$STATS"
say "median R/G/B: $MEDS"

# ---- 2. the render block: pinned, or derive a proposal and STOP ------------
PINNED=$(python3 -c "
import json,sys
try: r=json.load(open('$RECIPE'))
except (OSError,ValueError): r={}
print('yes' if isinstance(r.get('render'),dict) and r['render'].get('name')=='$NAME' else '')" 2>/dev/null || true)

if [ -z "$PINNED" ]; then
  say "no ratified render block for '$NAME' — deriving a PROPOSAL"
  python3 - "$RECIPE" "$NAME" "$MEDS" "$MADS" "$SKY" "$GASTOP" "$BLACKK" \
           "$LUM" "$CHROMA" "$STARS" <<'PY'
import json, os, sys
from scipy.optimize import brentq
rec_p, name, meds, mads, sky, gastop, bk, lum, chroma, stars = sys.argv[1:11]
med = [float(v) for v in meds.split()]; mad = [float(v) for v in mads.split()]
sky, gastop, bk = float(sky), float(gastop), float(bk)
# black-point depth: deep enough to clear the dark tail on EVERY channel, taken
# from Siril's own MAD (the statistic autostretch uses), then applied as a COMMON
# FRACTION so (median - low) keeps the linear channel ratio.
f = max(bk * mad[c] / med[c] for c in range(3))
# Sanity: f is the black point's depth as a fraction of the sky. Outside a sane
# band the inputs are wrong (wrong statistic, or a unit-scale mismatch between
# Siril's 16-bit ADU reporting and mtf's [0,1]) and a silently absurd proposal
# is worse than a stop.
if not (0.001 < f < 0.5):
    sys.exit(f"derived black-point fraction {f:.4f} is implausible "
             f"(median={med}, mad={mad}) — check the statistic and its scale")
mtf = lambda x, m: ((m - 1) * x) / ((2 * m - 1) * x - m)
x = f / (f + gastop)                      # identical for every channel
m = brentq(lambda mm: mtf(x, mm) - sky, 0.5001, 0.9999)
block = {
 "name": name, "status": "PROPOSED — not ratified; move to \"render\" to accept",
 "derived_from": {"tool": "Siril stat", "median": med, "mad": mad},
 "knobs": {"sky_target": sky, "gas_top_frac": gastop, "black_k_mad": bk,
           "denoise_lum": float(lum), "denoise_chroma": float(chroma),
           "star_asinh": float(stars)},
 "gas_mtf_per_channel": {nm: [round(med[c]*(1-f),8), round(m,4), round(med[c]*(1+gastop),8)]
                         for c, nm in enumerate("RGB")},
 "why_proportional": ("low/high are a fraction of each channel's OWN median so "
   "(sky-low) keeps the linear ratio; a common black point casts the render "
   "because the sky sits only ~%.0f%% above black" % (100*f)),
}
try: rec = json.load(open(rec_p))
except (OSError, ValueError): rec = {}
rec["render_proposed"] = block
os.makedirs(os.path.dirname(rec_p), exist_ok=True)
json.dump(rec, open(rec_p, "w"), indent=1)
print(json.dumps(block["gas_mtf_per_channel"], indent=1))
print(f"  black point = median x {1-f:.4f}   white = median x {1+gastop:.4f}   mid = {m:.4f}")
PY
  say "PROPOSAL written to $RECIPE as \"render_proposed\""
  say "STOP: review it, rename the block to \"render\" to ratify, then re-run"
  exit 7
fi
say "using the RATIFIED render block from $RECIPE"
eval "$(python3 -c "
import json
r=json.load(open('$RECIPE'))['render']
g=r['gas_mtf_per_channel']
for nm in 'RGB':
    lo,mid,hi=g[nm]; print(f'MTF_{nm}=\"{lo:.8f} {mid} {hi:.8f}\"')
k=r['knobs']
print(f'LUM={k[\"denoise_lum\"]}'); print(f'CHROMA={k[\"denoise_chroma\"]}')
print(f'STARS={k[\"star_asinh\"]}')")"

if [ "$PLAN" = 1 ]; then
  say "PLAN — separate:$SEPARATE denoise:$DENOISE"
  say "PLAN — gas mtf R: $MTF_R | G: $MTF_G | B: $MTF_B"
  say "PLAN — denoise lum $LUM chroma $CHROMA | stars asinh $STARS"
  say "plan only — nothing executed"; exit 0
fi

GAS=$STACK
# ---- 3. star separation ----------------------------------------------------
if [ "$SEPARATE" = 1 ]; then
  say "separating stars (Siril starnet -> StarNet2, invertible pre-stretch)"
  printf 'requires 1.4.0\nsetcompress 0\nset32bits\ncd %s\nload %s\nstarnet -stretch\nsave %s/starless\n' \
    "$W" "$STACK" "$W" > "$W/sep.ssf"
  sir "$W/sep.ssf"
  [ -f "$W/starless.fit" ] || { echo "separation failed — read $W/siril.log" >&2; exit 1; }
  MASK=$(ls "$W"/starmask_*.fit 2>/dev/null | head -1)
  [ -n "$MASK" ] || { echo "no star mask produced" >&2; exit 1; }
  say "GUARD: the split must be invertible"
  python3 - "$STACK" "$W/starless.fit" "$MASK" <<'PY'
import sys, numpy as np
from astropy.io import fits
o,s,m=[fits.getdata(p).astype(np.float64) for p in sys.argv[1:4]]
d=o-(1-(1-s)*(1-m)); r=d.std()/o.std()
print(f"  screen recombine residual {d.std():.3e} = {100*r:.4f}% of sigma")
if r > 1e-3: sys.exit("SEPARATION NOT INVERTIBLE — refusing to continue")
PY
  GAS=$W/starless.fit
fi

# ---- 4. denoise the gas layer ---------------------------------------------
if [ "$DENOISE" = 1 ]; then
  say "denoising the gas layer (Cosmic Clarity, lum $LUM / chroma $CHROMA)"
  [ -x "$CC/SetiAstroCosmicClarity_denoise" ] || { echo "Cosmic Clarity not at $CC" >&2; exit 1; }
  rm -f "$CC"/input/* "$CC"/output/*; mkdir -p "$CC/input" "$CC/output"
  cp "$GAS" "$CC/input/gas.fit"
  ( cd "$CC" && ./SetiAstroCosmicClarity_denoise --disable_gpu --denoise_mode separate \
      --denoise_strength "$LUM" --color_denoise_strength "$CHROMA" ) >> "$W/denoise.log" 2>&1
  DN=$(ls "$CC"/output/*.fit 2>/dev/null | head -1)
  [ -n "$DN" ] || { echo "denoise produced nothing — read $W/denoise.log" >&2; exit 1; }
  cp "$DN" "$W/gas_dn.fit"
  say "GUARD: blank sky must lose MORE band-pass power than the object"
  python3 - "$GAS" "$W/gas_dn.fit" <<'PY'
import sys, numpy as np
from astropy.io import fits
from scipy.ndimage import uniform_filter
A=fits.getdata(sys.argv[1]).astype(np.float64)[1]
B=fits.getdata(sys.argv[2]).astype(np.float64)[1]
sm=uniform_filter(A,101); H,W=A.shape
ys=range(300,H-800,200); xs=range(300,W-800,200)
cells=[(sm[y+250,x+250],y,x) for y in ys for x in xs]
obj=max(cells); blank=min(cells)
bad=[]
for s in (3,4,6,8):
    def loss(y,x):
        r=(slice(y,y+500),slice(x,x+500))
        a=(uniform_filter(A,s)-uniform_filter(A,2*s))[r]
        b=(uniform_filter(B,s)-uniform_filter(B,2*s))[r]
        return 100*(b.std()/a.std()-1)
    lb,lo=loss(blank[1],blank[2]),loss(obj[1],obj[2])
    print(f"  {s}-{2*s}px: blank {lb:+.1f}%  object {lo:+.1f}%  margin {lo-lb:+.1f}%")
    if lo < lb - 1.0: bad.append(s)
if bad: sys.exit(f"DENOISE EATS THE OBJECT at {bad} px — refusing to continue")
PY
  GAS=$W/gas_dn.fit
fi

# ---- 5. stretch each layer on its own terms, recombine --------------------
say "stretching (gas: per-channel mtf | stars: asinh -human $STARS) and recombining"
{ echo "requires 1.4.0"; echo "setcompress 0"; echo "set32bits"; echo "cd $W"
  echo "load $GAS"
  echo "mtf $MTF_R R"; echo "mtf $MTF_G G"; echo "mtf $MTF_B B"
  echo "save gas_stretched"
  if [ "$SEPARATE" = 1 ]; then
    echo "load $MASK"; echo "asinh -human $STARS 0.00002"; echo "save stars_stretched"
    echo 'pm "1 - (1 - $gas_stretched$) * (1 - $stars_stretched$)"'
  else
    echo "load gas_stretched"
  fi
  echo "save $RES/stack_${NAME}_render"
  echo "savepng $RES/judge/${NAME}_render"; } > "$W/render.ssf"
sir "$W/render.ssf"
[ -f "$RES/judge/${NAME}_render.png" ] || { echo "render failed — read $W/siril.log" >&2; exit 1; }

# ---- 6. record what was actually produced ---------------------------------
python3 - "$RECIPE" "$RES/judge/${NAME}_render.png" "$RES/stack_${NAME}_render.fit" \
         "$SEPARATE" "$DENOISE" "$DSET/qa_work/render_${NAME}.json" <<'PY'
import json, os, sys
import numpy as np
from astropy.io import fits
rec_p, png, fitp, sep, dn, out = sys.argv[1:7]
d = fits.getdata(fitp).astype(np.float64)
g = d[1]
sel = (g > np.percentile(g, 40)) & (g < np.percentile(g, 60))
hi = (g > np.percentile(g, 97)) & (g < np.percentile(g, 99.8))
r = {"render": png, "stack": fitp,
     "separated": bool(int(sep)), "denoised": bool(int(dn)),
     "sky_level_of_1": round(float(np.median(g)), 4),
     "colour_ratios": {
        "sky": {"R_over_G": round(float(np.mean(d[0][sel])/np.mean(d[1][sel])), 4),
                "B_over_G": round(float(np.mean(d[2][sel])/np.mean(d[1][sel])), 4)},
        "bright": {"R_over_G": round(float(np.mean(d[0][hi])/np.mean(d[1][hi])), 4),
                   "B_over_G": round(float(np.mean(d[2][hi])/np.mean(d[1][hi])), 4)}},
     "note": ("a nonlinear stretch cannot preserve channel ratios exactly; "
              "compare these against the LINEAR stack's ratios, and treat any "
              "residual as inherent rather than a parameter error")}
os.makedirs(os.path.dirname(out), exist_ok=True)
json.dump(r, open(out, "w"), indent=1)
print(f"  sky level {r['sky_level_of_1']:.4f}  "
      f"sky R/G {r['colour_ratios']['sky']['R_over_G']:.4f} "
      f"B/G {r['colour_ratios']['sky']['B_over_G']:.4f}  |  "
      f"bright R/G {r['colour_ratios']['bright']['R_over_G']:.4f} "
      f"B/G {r['colour_ratios']['bright']['B_over_G']:.4f}")
print(f"  record -> {out}")
PY
say "DONE -> $RES/judge/${NAME}_render.png"
