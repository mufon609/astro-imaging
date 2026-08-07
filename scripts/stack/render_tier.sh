#!/usr/bin/env bash
# RENDER TIER — the aesthetic finish, past the diagnostic judge surface.
# Separates stars, denoises the gas, stretches, screen-recombines. EVERY pixel
# operation and EVERY measurement here is an official tool's (Siril starnet /
# pm / isub / bgnoise / wavelet / wrecons / findstar / stat / mtf / asinh /
# savepng; Cosmic Clarity denoise). This script only sequences them, applies
# decision logic to the numbers they report, and records what happened. No
# in-house code reads, transforms or analyzes the deliverable's pixels — the
# bright line in CLAUDE.md "What this repo IS". In-house python here parses tool
# logs, reads FITS HEADERS, resolves config and writes JSON. Nothing else.
#
#   render_tier.sh <linear-spcc-stack.fit> <name> --session=<dir> --set=<set>
#                  [--sky=] [--gas-top=] [--black-k=] [--lum=] [--chroma=]
#                  [--stars=] [--star-black=] [--no-separate] [--no-denoise]
#                  [--fresh] [--overwrite] [--plan]
#
# THE GATE (the chain's own pattern: derive -> propose -> user ratifies -> run).
# The `render` block in datasets/<session>/<set>/recipe.json pins the knobs. With
# no ratified block for <name> this script does the measurable work, writes its
# proposal as `render_proposed`, prints it and STOPS with exit 7. Nothing
# aesthetic runs on a knob the user has not seen. Move the block to `render` to
# ratify, then re-run: the intermediates are reused (see REUSE), so ratifying
# costs one stretch, not another separation + denoise.
#
# KNOB RESOLUTION is CLI > recipe.render.knobs > datasets/GENERIC.json render >
# built-in, and the provenance of every knob is PRINTED on every run. A ratified
# recipe does NOT silently override an explicit CLI flag: that inversion made
# `--lum=` a no-op on a ratified set, so a one-knob ladder rendered three
# identical images and read NULL.
#
# THE RECIPE PINS ONLY SCALE-FREE FRACTIONS (sky_target, gas_top_frac,
# black_k_mad, the denoise strengths, star_asinh). The absolute mtf triplet is
# derived AT RUN TIME from the layer that is actually about to be stretched.
# WHY THIS IS THE WHOLE POINT: the first build measured Siril `stat` on the
# star-ful input stack and applied the resulting ABSOLUTE black/white points to
# the starless, denoised layer produced later. Those are different layers, and
# BOTH of their statistics differ — MEASURED, both by `stat main` on the same
# chain: the layer's medians run 3.90% below the stack's (which is why the shipped
# render's sky landed at 0.063 for a 0.100 target), the layer's channel BALANCE is
# 0.60% different (B-vs-G), and the layer's MAD/median is only ~0.012 against the
# stack's ~0.034, so a black point of "4 x MAD" is 0.0527 of the sky measured on
# the layer versus 0.1391 measured on the stack — 2.6x too deep, crushing faint
# extended signal the policy never intended to crush. The colour consequence is
# amplified because the render's sky sits only f above the black point: a
# per-channel level error is magnified by ~1/f, which was 12.2x at the stack's f
# and is 19x at the layer's. Deriving everything from the layer in hand closes all
# three, and a fractions-only recipe cannot go stale when a stage changes.
#
# THE STRETCH: NEUTRALIZE PER CHANNEL, THEN STRETCH WITH ONE COMMON GAIN. lo_c
# sits the same fraction f below each channel's OWN sky — that is the standard
# background-neutralization step, which is exactly why the mainstream orders it
# before colour calibration — and the window WIDTH and midtone balance are single
# common values, so every channel gets the identical gain and curve. The
# registry's post-SPCC "use linked" rule governs the CURVE, and it holds here.
# A FULLY common triplet (black point included) was tried and MEASURED WRONG on
# this data: because the amplification is ~1/f, the layer's real 0.48% B-vs-G sky
# difference renders as B/G 1.1147 at f=0.0527 (19x) and 1.0596 at f=0.1391
# (7.2x) — an 11% or 6% background tint out of half a percent, the same
# mechanism the registry records for spatial gradients (autostretch amplifies a
# fractional background variation by median/(2.8 x MAD), measured 8.7-17x).
# Per-channel lo renders 1.0057 against the layer truth of 1.0048: +0.09%.
# The third option, scaling the WIDTH per channel too, forces the sky to exactly
# neutral (1.0000) and so overrides the colour SPCC measured rather than
# rendering it; that is the one construction that discards a real measurement.
# Measured summary, this layer, error vs the layer's own sky B/G:
#   per-channel lo + common width  +0.09%   <- built
#   per-channel lo + per-channel width  -0.48%  (forces neutral)
#   fully common triplet           +10.94%  (1/f amplification)
#
# WHAT NO PARAMETER FIXES: a nonlinear curve cannot preserve channel ratios —
# channels enter at different points and leave with different local slopes, so a
# residual remains at the bright end. `asinh -human` (which preserves L*a*b*
# lightness) splits that error more evenly but costs contrast. Both are
# legitimate; the choice is aesthetic and therefore the user's.
#
# ORDER follows the researched mainstream (TOOLS.md, "The one process rule that
# changed everything"): background extraction -> colour calibration -> [deconvolution] ->
# star removal -> noise reduction on the starless -> stretch -> recomposition.
# The background step is per-frame `subsky 1` in the light builder and SPCC runs
# on the stack, so both precede this script. DECONVOLUTION IS SKIPPED AND THAT IS
# NOT YET A MEASURED NULL: classical RL is a measured dead end on in-exposure
# trailing and GraXpert's is the immature path, but a LEARNED deconvolver is an
# open option the registry explicitly does not dead-end, and one is installed
# beside the denoiser this script already drives (Cosmic Clarity's non-stellar
# sharpen models). Skipping is a HYPOTHESIS pending that measurement — BACKLOG.
#
# CHECKS. Both are decision logic over TOOL-REPORTED numbers (the review
# contract's model), never in-house pixel analysis, and both state the margin
# they were set from so it is clear they are not tuned:
# - the separation must actually remove stars. Siril `findstar` measured
#   18125 stars in the source, 0 in the starless and 18553 in the mask, so the
#   gate (starless <= 1% of source, mask >= 50% of source) sits orders away from
#   the real result. This replaces a screen-recombine residual check, which was
#   near-VACUOUS: Siril builds the mask by unscreening source against starless,
#   so `1-(1-s)(1-m)` reproduces the source ALGEBRAICALLY whatever the
#   separation did, and the measured residual (bgnoise 4.5e-10) was just the
#   float32 epsilon. It is still measured and recorded — it catches a clipping
#   event or a mismatched pair — but it is no longer mistaken for evidence.
# - the denoise is MEASURED, not gated: Siril's own `wavelet`/`wrecons` a-trous
#   decomposition gives per-scale background noise before and after, whole-frame
#   and per channel. The in-house band-pass gate this replaces picked its
#   "object" and "blank sky" regions as the brightest and darkest cell of the
#   image under test — a geometry derived from the measurement (registry trap 3)
#   and a hand-picked patch where the doctrine requires a statistical scope — and
#   aborted the render on an unratified 1-percentage-point threshold. The
#   registry already names the instruments for this judgement: the noise_split
#   structured term plus the user's eyes on the star field at 1:1. The gate
#   above is the gate; these numbers are what the user ratifies against.
set -euo pipefail
REPO=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
source "$REPO/scripts/lib/siril_run.sh"   # serialized siril-cli invoker (BACKLOG item 18)
STACK=${1:?usage: render_tier.sh <stack.fit> <name> --session= --set= [opts]}
NAME=${2:?missing <name>}
SESSION= SET= SEPARATE=1 DENOISE=1 PLAN=0 FRESH=0 OVERWRITE=0
CLI_sky= CLI_gas_top= CLI_black_k= CLI_lum= CLI_chroma= CLI_stars= CLI_star_black=
for a in "${@:3}"; do case "$a" in
  --session=*) SESSION=${a#*=};; --set=*) SET=${a#*=};;
  --sky=*) CLI_sky=${a#*=};; --gas-top=*) CLI_gas_top=${a#*=};;
  --black-k=*) CLI_black_k=${a#*=};; --lum=*) CLI_lum=${a#*=};;
  --chroma=*) CLI_chroma=${a#*=};; --stars=*) CLI_stars=${a#*=};;
  --star-black=*) CLI_star_black=${a#*=};;
  --no-separate) SEPARATE=0;; --no-denoise) DENOISE=0;;
  --fresh) FRESH=1;; --overwrite) OVERWRITE=1;; --plan) PLAN=1;;
  *) echo "unknown arg $a" >&2; exit 1;;
esac; done
[ -f "$STACK" ] || { echo "no such stack: $STACK" >&2; exit 1; }
[ -n "$SESSION" ] && [ -n "$SET" ] || { echo "need --session= --set=" >&2; exit 1; }
SESSION=$(cd "$SESSION" && pwd); SNAME=$(basename "$SESSION")
STACK=$(cd "$(dirname "$STACK")" && pwd)/$(basename "$STACK")
RES=$REPO/web/results/$SNAME; DSET=$REPO/datasets/$SNAME/$SET
RECIPE=$DSET/recipe.json; GENERIC=$REPO/datasets/GENERIC.json
W=$SESSION/work/render_$NAME
CC=/opt/cosmicclarity-6.6
# render_<name>.fit, NOT stack_<name>_render.fit. A render is not a stack: the
# stack_ namespace is modelled as integrated stacks everywhere (the web surfaces
# list, the solve/SPCC pickers, the frame-count confirmation against the recipe),
# so a render sitting in it was presented as a stack product with a meaningless
# frame count — and the surface token in stack_<name>_render swallowed the
# <surface> position the judge-name convention uses, orphaning the judge PNG from
# its own product. The judge surface keeps the ratified name shape:
# judge/<set>_<recipe-tag>_<surface>.png = judge/<name>_render.png.
PRODUCT=$RES/render_${NAME}
JUDGE=$RES/judge/${NAME}_render
say(){ echo "[render $NAME] $*"; }
sir(){ siril_cli -d "$W" -s "$1" >> "$W/siril.log" 2>&1; }
# a measurement invocation: its own log, so a parse can never pick up an earlier
# stage's numbers
mir(){ siril_cli -d "$W" -s "$1" > "$2" 2>&1; }

mkdir -p "$W" "$RES/judge" "$DSET/qa_work"
: > "$W/siril.log"

# ---- 0. this tier is RGB-only; a mono set must degrade loudly ---------------
# FITS header only (astropy), never the pixels.
NAXIS3=$(python3 - "$STACK" <<'PY'
import sys
from astropy.io import fits
h = fits.getheader(sys.argv[1])
print(int(h.get("NAXIS3", 1)))
PY
)
[ "$NAXIS3" = 3 ] || { cat >&2 <<EOF
ABORT: $STACK has NAXIS3=$NAXIS3 — the render tier is RGB-only.
A mono/single-filter set renders luminance-only and skips SPCC (README stage
table); that variant is not built. This STOPS rather than indexing a 2-D frame
as if it were a channel, which is what silently reported one image ROW as the
colour ratio.
EOF
exit 1; }

# ---- 1. resolve the knobs: CLI > recipe > GENERIC > built-in ----------------
KNOBS=$(python3 - "$RECIPE" "$GENERIC" "$NAME" \
        "${CLI_sky}" "${CLI_gas_top}" "${CLI_black_k}" \
        "${CLI_lum}" "${CLI_chroma}" "${CLI_stars}" "${CLI_star_black}" <<'PY'
import json, sys
rec_p, gen_p, name = sys.argv[1:4]
cli = dict(zip(["sky_target", "gas_top_frac", "black_k_mad",
                "denoise_lum", "denoise_chroma", "star_asinh",
                "star_black"], sys.argv[4:11]))
# star_black is the `asinh` OFFSET applied to the star layer. It was an
# unresolved literal (0.00002) written straight into the stretch line: not
# CLI-overridable, absent from the proposal block and absent from the render
# record, so a ratified recipe did NOT pin every parameter of the stretch —
# which is exactly what datasets/README.md says an APPROVED recipe means.
# Same class as every other absolute in here: it is a knob or it is a bug.
DEFAULT = {"sky_target": 0.10, "gas_top_frac": 0.16, "black_k_mad": 4.0,
           "denoise_lum": 0.6, "denoise_chroma": 0.85, "star_asinh": 1000.0,
           "star_black": 0.00002}
def load(p):
    try:
        return json.load(open(p))
    except (OSError, ValueError):
        return {}
rec, gen = load(rec_p), load(gen_p)
block = rec.get("render") if isinstance(rec.get("render"), dict) else {}
ratified = block.get("name") == name
pinned = block.get("knobs", {}) if ratified else {}
generic = (gen.get("render") or {})
val, prov = {}, {}
for k, d in DEFAULT.items():
    if cli.get(k):
        val[k], prov[k] = float(cli[k]), "CLI"
    elif k in pinned:
        val[k], prov[k] = float(pinned[k]), "recipe(ratified)"
    elif k in generic:
        val[k], prov[k] = float(generic[k]), "GENERIC.json"
    else:
        val[k], prov[k] = float(d), "built-in"
print("RATIFIED=%d" % (1 if ratified else 0))
for k in DEFAULT:
    print("K_%s=%r" % (k, val[k]))
print("PROVENANCE='%s'" % "  ".join(f"{k}={val[k]:g}[{prov[k]}]" for k in DEFAULT))
PY
) || { echo "knob resolution failed" >&2; exit 1; }
eval "$KNOBS"
say "knobs: $PROVENANCE"
[ "$RATIFIED" = 1 ] && say "render block for '$NAME' is RATIFIED in $RECIPE" \
                    || say "no ratified render block for '$NAME' — this run will STOP with a proposal"
if [ "$RATIFIED" = 1 ] && { [ -n "$CLI_sky" ] || [ -n "$CLI_gas_top" ] || [ -n "$CLI_black_k" ] \
     || [ -n "$CLI_lum" ] || [ -n "$CLI_chroma" ] || [ -n "$CLI_stars" ]; }; then
  say "NOTE: CLI flags OVERRIDE the ratified block above (see the provenance) —"
  say "      that is a deliberate one-knob-ladder arm, not the ratified look."
fi

# ---- 2. never silently overwrite a judged surface ---------------------------
# A ladder arm must not destroy its own control. This is why one record still
# describes a file whose parameters no longer match it.
if [ "$PLAN" = 0 ] && [ "$OVERWRITE" = 0 ]; then
  for f in "$PRODUCT.fit" "$JUDGE.png"; do
    [ -e "$f" ] && { cat >&2 <<EOF
ABORT: $f already exists.
Pass a distinct <name> for a ladder arm (the recipe-tag names the chain shape),
or --overwrite to replace this product deliberately. A per-arm experiment tree
(web/results/<session>/exp_<param>_<stamp>/) rides the ladder harness — BACKLOG.
EOF
exit 1; }
  done
fi

if [ "$PLAN" = 1 ]; then
  say "PLAN — separate:$SEPARATE denoise:$DENOISE  (ratified:$RATIFIED)"
  say "PLAN — knobs $PROVENANCE"
  say "PLAN — the mtf triplet is DERIVED at run time from the layer being"
  say "       stretched (linked, one triplet for R/G/B); nothing absolute is pinned"
  say "PLAN — product $PRODUCT.fit"
  say "PLAN — judge   $JUDGE.png"
  say "PLAN — record  $DSET/qa_work/render_${NAME}.json"
  say "plan only — nothing executed, nothing written"; exit 0
fi

SRCSTAMP="$(stat -c '%s %Y' "$STACK")"
GAS=$STACK
MSTEM=

# ---- 3. star separation (Siril starnet -> StarNet2) ------------------------
if [ "$SEPARATE" = 1 ]; then
  if [ "$FRESH" = 0 ] && [ -f "$W/starless.fit" ] && [ -f "$W/starless.stamp" ] \
     && [ "$(cat "$W/starless.stamp")" = "$SRCSTAMP" ]; then
    say "REUSING the separated layers in $W (source unchanged)"
  else
    say "separating stars (Siril starnet -> StarNet2, invertible pre-stretch)"
    rm -f "$W"/starmask_*.fit "$W/starless.fit" "$W/starless.stamp"
    printf 'requires 1.4.0\nsetcompress 0\nset32bits\ncd %s\nload %s\nstarnet -stretch\nsave %s/starless\n' \
      "$W" "$STACK" "$W" > "$W/sep.ssf"
    sir "$W/sep.ssf"
    [ -f "$W/starless.fit" ] || { echo "separation failed — read $W/siril.log" >&2; exit 1; }
    printf '%s' "$SRCSTAMP" > "$W/starless.stamp"
  fi
  MASK=$(ls "$W"/starmask_*.fit 2>/dev/null | head -1)
  [ -n "$MASK" ] || { echo "no star mask produced — read $W/siril.log" >&2; exit 1; }
  MSTEM=$(basename "$MASK" .fit)

  say "MEASURING the separation (Siril findstar + pm/isub/bgnoise)"
  rm -f "$W"/n_*.lst
  { echo "requires 1.4.0"; echo "setcompress 0"; echo "set32bits"; echo "cd $W"
    echo "load $STACK";        echo "findstar -out=$W/n_source.lst"
    echo "load $W/starless.fit"; echo "findstar -out=$W/n_starless.lst"
    echo "load $MASK";         echo "findstar -out=$W/n_mask.lst"
    printf 'pm "1 - (1 - $starless$) * (1 - $%s$)"\n' "$MSTEM"
    echo "isub $STACK"; echo "bgnoise"; } > "$W/m_sep.ssf"
  mir "$W/m_sep.ssf" "$W/m_sep.log"
  grep -q 'Candidates for stars:' "$W/m_sep.log" \
    || { echo "findstar did not run — read $W/m_sep.log" >&2; exit 1; }
  # findstar writes NO list when it finds zero stars (measured), so a missing
  # list is a legitimate 0 — never an error. Its "Candidates" line above is the
  # positive control that the measurement happened at all.
  cnt(){ [ -f "$1" ] && { grep -vc '^#' "$1" || true; } || echo 0; }
  N_SRC=$(cnt "$W/n_source.lst"); N_LESS=$(cnt "$W/n_starless.lst"); N_MASK=$(cnt "$W/n_mask.lst")
  say "  findstar: source $N_SRC -> starless $N_LESS | mask $N_MASK"
  python3 - "$N_SRC" "$N_LESS" "$N_MASK" <<'PY'
import sys
src, less, mask = (int(v) for v in sys.argv[1:4])
if src < 100:
    sys.exit(f"SEPARATION UNMEASURABLE: only {src} stars detected in the source "
             f"— too few to prove a separation happened")
if less > 0.01 * src:
    sys.exit(f"SEPARATION DID NOT REMOVE THE STARS: {less} left of {src} "
             f"({100*less/src:.1f}%, gate 1%) — refusing to continue")
if mask < 0.50 * src:
    sys.exit(f"STAR MASK IS MISSING FLUX: {mask} stars vs {src} in the source "
             f"({100*mask/src:.0f}%, gate 50%) — refusing to continue")
PY
  # anchor on bgnoise's own line: a bare "(...)" also matches Siril's
  # "found reference HDU 4404x3008x3 (-32)" and printed bitpix as a residual
  say "  recombine residual (bgnoise/channel): $(grep -oE 'Background noise value \(channel: #[0-9]\): [0-9.]+ \([0-9.eE+-]+\)' "$W/m_sep.log" | grep -oE '\([0-9.eE+-]+\)$' | tr -d '()' | tr '\n' ' ')"
  GAS=$W/starless.fit
fi

# ---- 4. denoise the gas layer (Cosmic Clarity) -----------------------------
if [ "$DENOISE" = 1 ]; then
  DNSTAMP="$SRCSTAMP ${K_denoise_lum} ${K_denoise_chroma} $SEPARATE"
  if [ "$FRESH" = 0 ] && [ -f "$W/gas_dn.fit" ] && [ -f "$W/gas_dn.stamp" ] \
     && [ "$(cat "$W/gas_dn.stamp")" = "$DNSTAMP" ]; then
    say "REUSING the denoised layer in $W (source + strengths unchanged)"
  else
    say "denoising (Cosmic Clarity, lum ${K_denoise_lum} / chroma ${K_denoise_chroma})"
    [ -x "$CC/SetiAstroCosmicClarity_denoise" ] || { echo "Cosmic Clarity not at $CC" >&2; exit 1; }
    mkdir -p "$CC/input" "$CC/output"
    # Cosmic Clarity has no path flags — it reads $CC/input and writes
    # $CC/output/<stem>_denoised.fit. So this stages exactly ONE uniquely named
    # file and removes only that file afterwards. It does NOT glob-delete those
    # dirs: they are outside the session tree, shared, and a wildcard there
    # destroys whatever another job staged.
    CSTEM=ct_${NAME//[^A-Za-z0-9._+-]/_}
    shopt -s nullglob
    STALE=("$CC/input"/*.fit "$CC/input"/*.fits "$CC/input"/*.tif "$CC/input"/*.tiff
           "$CC/output"/*.fit "$CC/output"/*.fits "$CC/output"/*.tif "$CC/output"/*.tiff)
    shopt -u nullglob
    [ ${#STALE[@]} -eq 0 ] || { { echo "ABORT: Cosmic Clarity's scratch dirs are not empty:"
        printf '  %s\n' "${STALE[@]}"
        echo "Another render may be running. If not, remove those files and re-run."; } >&2; exit 1; }
    cp "$GAS" "$CC/input/$CSTEM.fit"
    ( cd "$CC" && ./SetiAstroCosmicClarity_denoise --disable_gpu --denoise_mode separate \
        --denoise_strength "${K_denoise_lum}" --color_denoise_strength "${K_denoise_chroma}" ) \
      >> "$W/denoise.log" 2>&1
    DN=$CC/output/${CSTEM}_denoised.fit
    [ -f "$DN" ] || { { echo "ABORT: expected $DN, found:"; ls -la "$CC/output" || true
        echo "read $W/denoise.log"; } >&2; rm -f "$CC/input/$CSTEM.fit"; exit 1; }
    cp "$DN" "$W/gas_dn.fit"
    rm -f "$CC/input/$CSTEM.fit" "$DN"
    printf '%s' "$DNSTAMP" > "$W/gas_dn.stamp"
  fi
  # Measured on EVERY run, reused layer or not: it is two cheap wavelet passes,
  # and hanging it off the fresh-denoise branch would let a reused layer record an
  # empty profile that reads as "not measured" exactly like a real gap.
  say "MEASURING the denoise (Siril wavelet/wrecons a-trous, per scale)"
  for leg in pre:"$GAS" post:"$W/gas_dn.fit"; do
    { echo "requires 1.4.0"; echo "setcompress 0"; echo "set32bits"; echo "cd $W"
      echo "load ${leg#*:}"; echo "wavelet 4 2"
      for c in "1 0 0 0" "0 1 0 0" "0 0 1 0" "0 0 0 1"; do
        echo "wrecons $c"; echo "bgnoise"; done; } > "$W/m_dn_${leg%%:*}.ssf"
    mir "$W/m_dn_${leg%%:*}.ssf" "$W/m_dn_${leg%%:*}.log"
  done
  GAS=$W/gas_dn.fit
fi

# ---- 5. measure THE LAYER THAT IS ABOUT TO BE STRETCHED --------------------
# `stat main` (not plain `stat`): the short form reports Sigma, which on a
# star-containing layer is inflated by the stars (measured 138.2 against a MAD of
# 1.7 on the same layer) and would drive the black point far below zero. MAD is
# the robust statistic and is what autostretch's shadow clip is built on.
# Siril reports float images in 16-bit ADU while `mtf` takes normalized [0,1], so
# everything is divided by 65535 here — mixing those scales silently produces a
# black point ~65000x too deep.
# `fmul 100` BEFORE measuring (nothing is saved, so the file is untouched): Siril
# prints stat to 0.1 ADU, which on a sky of ~50 ADU is 0.2%, and the sky sits only
# ~14% above the black point, so that quantum becomes ~1.4% of (sky - low).
# Scaling up first makes the same quantum 100x finer. Median and MAD are robust,
# so the bright end clipping at the top of the range does not affect them. CLASS
# LIMIT, and it fails LOUDLY not silently: a stack whose sky exceeds ~0.01 of full
# range clips its own median to 1.0 under fmul 100, MAD collapses to 0, and the
# sanity band below STOPS.
say "measuring the layer being stretched (Siril stat main): $(basename "$GAS")"
printf 'requires 1.4.0\nsetcompress 0\nload %s\nfmul 100\nstat main\n' "$GAS" > "$W/m_layer.ssf"
mir "$W/m_layer.ssf" "$W/m_layer.log"
# fmul 100 for the same reason as the layer measurement: this stack's sky is
# ~50 ADU and Siril prints stat to 0.1 ADU, so unscaled its channel RATIOS carry
# a +-0.2% quantization error — the same size as the colour effect being judged.
# Levels in this log are therefore x100; ratios are unaffected. Nothing is saved.
printf 'requires 1.4.0\nsetcompress 0\nload %s\nfmul 100\nstat main\n' "$STACK" > "$W/m_source.ssf"
mir "$W/m_source.ssf" "$W/m_source.log"

MTF=$(python3 - "$W/m_layer.log" "${K_black_k_mad}" "${K_gas_top_frac}" "${K_sky_target}" <<'PY'
import re, sys
SCALE = 100.0 * 65535.0            # the fmul factor x Siril's 16-bit reporting
log, bk, gastop, sky = sys.argv[1], *(float(v) for v in sys.argv[2:5])
med, mad = [], []
for line in open(log):
    m = re.search(r"\w+ layer: .*?Median: ([0-9.eE+-]+),.*?MAD: ([0-9.eE+-]+)", line)
    if m:
        med.append(float(m.group(1)) / SCALE)
        mad.append(float(m.group(2)) / SCALE)
if len(med) < 3:
    sys.exit("could not parse three layers with MAD from `stat main` — read " + log)
med, mad = med[:3], mad[:3]
# PER-CHANNEL BLACK POINT (= background neutralization), COMMON GAIN AND CURVE
# (= linked). lo_c sits the same FRACTION below each channel's own sky, so the
# per-channel sky offset is absorbed where it belongs — the standard
# neutralize-then-stretch order — while the window WIDTH and the midtone balance
# are single common values, so every channel gets the identical gain and curve.
# WHY NOT one common lo as well: the render's sky sits only f above the black
# point, so a common lo amplifies each channel's fractional sky offset by ~1/f.
# MEASURED on this layer (sky B/G 1.0048 in linear): a common lo renders B/G
# 1.1147 at f=0.0527 (19x) and 1.0596 at f=0.1391 (7.2x), i.e. an 11% or 6%
# background tint out of a 0.5% real difference, while this construction renders
# 1.0057 — +0.09% from the truth. WHY NOT a per-channel WIDTH too (hi_c scaling
# with med_c as well): that makes the gain per-channel and forces the sky to
# exactly neutral, which overrides the colour SPCC measured instead of rendering
# it. This is the only one of the three that reproduces the layer's own ratio.
level = sum(med) / 3.0
f = max(bk * mad[c] / med[c] for c in range(3))
# Sanity: f is the black point's depth as a fraction of the sky. Outside a sane
# band the inputs are wrong (wrong statistic, or a unit-scale mismatch between
# Siril's 16-bit ADU reporting and mtf's [0,1]) and a silently absurd render is
# worse than a stop.
if not (0.001 < f < 0.5):
    sys.exit(f"derived black-point fraction {f:.4f} is implausible "
             f"(median={med}, mad={mad}) — check the statistic and its scale")
# Siril's midtone transfer, and its exact inverse for the midtone balance:
#   mtf(x, m) = (m-1)x / ((2m-1)x - m) = y   =>   m = x(1-y) / (x - 2xy + y)
# Closed form, so there is no solver and no bracket to get wrong. (The bracketed
# root-find this replaced was pinned to [0.5001, 0.9999], which silently required
# sky_target < f/(f+gas_top) and raised an opaque "f(a) and f(b) must have
# different signs" outside it instead of saying so.)
x = f / (f + gastop)                       # where the sky sits in the window
den = x - 2 * x * sky + sky
if den == 0:
    sys.exit(f"no midtone balance maps sky {sky} from window position {x:.6f}")
m = x * (1 - sky) / den
if not (0.0 < m < 1.0):
    sys.exit(f"midtone balance {m:.4f} is outside Siril's [0,1] range: a sky_target "
             f"of {sky} is unreachable from window position {x:.6f} "
             f"(black point {f:.4f} of sky, gas_top {gastop}) — raise gas_top_frac "
             f"or lower sky_target")
W = level * (f + gastop)                   # ONE window width => one common gain
lo = [med[c] * (1 - f) for c in range(3)]  # per-channel black point
hi = [lo[c] + W for c in range(3)]
for c, nm in enumerate("RGB"):
    print(f"MTF_{nm}='{lo[c]:.10f} {m:.4f} {hi[c]:.10f}'")
print(f"MID={m:.4f}\nBPFRAC={f:.6f}\nLEVEL={level:.10f}\nWIDTH={W:.10f}")
print("LOS='%s'" % " ".join(f"{v:.10f}" for v in lo))
print("HIS='%s'" % " ".join(f"{v:.10f}" for v in hi))
print("MEDIANS='%s'" % " ".join(f"{v:.10f}" for v in med))
print("MADS='%s'" % " ".join(f"{v:.10f}" for v in mad))
PY
) || { echo "could not derive the stretch from $W/m_layer.log" >&2; exit 1; }
eval "$MTF"
say "  layer medians R/G/B: $MEDIANS"
say "  mtf per channel (common gain): R[$MTF_R] G[$MTF_G] B[$MTF_B]"
say "  black point $(python3 -c "print(f'{100*$BPFRAC:.2f}')")% below each channel's own sky | common width $WIDTH"

# ---- 6. the gate: ratified, or write the proposal and STOP ------------------
if [ "$RATIFIED" != 1 ]; then
  python3 - "$RECIPE" "$NAME" "$LOS" "$MID" "$HIS" "$BPFRAC" "$MEDIANS" "$MADS" \
           "${K_sky_target}" "${K_gas_top_frac}" "${K_black_k_mad}" \
           "${K_denoise_lum}" "${K_denoise_chroma}" "${K_star_asinh}" \
           "${K_star_black}" "$SEPARATE" "$DENOISE" <<'PY'
import json, os, sys, tempfile
(rec_p, name, lo, mid, hi, bp, meds, mads, sky, gastop, bk,
 lum, chroma, stars, starblack, sep, dn) = sys.argv[1:18]
block = {
 "name": name,
 "status": 'PROPOSED — not ratified; rename this block to "render" to accept',
 "stretch": ("per-channel black point (background neutralization) + ONE common "
             "window width and midtone balance (linked gain and curve)"),
 "knobs": {"sky_target": float(sky), "gas_top_frac": float(gastop),
           "black_k_mad": float(bk), "denoise_lum": float(lum),
           "denoise_chroma": float(chroma), "star_asinh": float(stars),
           "star_black": float(starblack)},
 "stages": {"separate": bool(int(sep)), "denoise": bool(int(dn))},
 "derived_at_run_time_do_not_pin": {
     "tool": "Siril stat main on the layer being stretched",
     "median": [float(v) for v in meds.split()],
     "mad": [float(v) for v in mads.split()],
     "mtf_lo_per_channel": [round(float(v), 8) for v in lo.split()],
     "mtf_hi_per_channel": [round(float(v), 8) for v in hi.split()],
     "mtf_mid_common": float(mid),
     "black_point_fraction_of_sky": round(float(bp), 6)},
 "why_fractions_only": ("only the scale-free fractions above are pinned; the "
   "absolute mtf triplet is re-derived on every run from the layer actually "
   "being stretched, so it cannot go stale when a stage changes. Deriving it "
   "from the star-ful input stack instead put the render's sky at 0.063 for a "
   "0.100 target and cast it 5.6% in B/G, at 12.2x amplification."),
}
try:
    rec = json.load(open(rec_p))
except (OSError, ValueError):
    rec = {}
rec["render_proposed"] = block
# atomic: a crash mid-write must not truncate the tracked record that carries
# this set's ratified cull policy
os.makedirs(os.path.dirname(rec_p), exist_ok=True)
fd, tmp = tempfile.mkstemp(dir=os.path.dirname(rec_p), suffix=".tmp")
with os.fdopen(fd, "w") as fh:
    json.dump(rec, fh, indent=1)
os.replace(tmp, rec_p)
print(json.dumps(block, indent=1))
PY
  say "PROPOSAL written to $RECIPE as \"render_proposed\""
  say "STOP: review it, rename the block to \"render\" to ratify, then re-run"
  say "      (the layers in $W are reused, so the re-run is just the stretch)"
  exit 7
fi

# ---- 7. stretch (linked) and recombine ------------------------------------
say "stretching (per-channel lo, common gain | stars asinh -human ${K_star_asinh} ${K_star_black}) and recombining"
{ echo "requires 1.4.0"; echo "setcompress 0"; echo "set32bits"; echo "cd $W"
  echo "load $GAS"
  echo "mtf $MTF_R R"; echo "mtf $MTF_G G"; echo "mtf $MTF_B B"
  echo "save gas_stretched"
  if [ "$SEPARATE" = 1 ]; then
    echo "load $MASK"; echo "asinh -human ${K_star_asinh} ${K_star_black}"; echo "save stars_stretched"
    echo 'pm "1 - (1 - $gas_stretched$) * (1 - $stars_stretched$)"'
  else
    echo "load gas_stretched"
  fi
  echo "save $PRODUCT"
  echo "savepng $JUDGE"; } > "$W/render.ssf"
sir "$W/render.ssf"
[ -f "$JUDGE.png" ] || { echo "render failed — read $W/siril.log" >&2; exit 1; }

# ---- 8. measure the product (Siril stat main) and record -------------------
printf 'requires 1.4.0\nsetcompress 0\nload %s\nstat main\n' "$PRODUCT.fit" > "$W/m_final.ssf"
mir "$W/m_final.ssf" "$W/m_final.log"
# The rendered SKY colour is the stretched GAS layer's, not the product's: the
# product is the gas screened with the asinh-stretched star layer, and the stars
# drag its median away from the sky (measured on one render: gas layer median B/G
# 1.0043, product 0.9897). Reading the product's median as "the sky" is what let a
# 5.6% sky cast be reported against a bright-end number.
printf 'requires 1.4.0\nsetcompress 0\nload %s/gas_stretched.fit\nstat main\n' "$W" > "$W/m_sky.ssf"
mir "$W/m_sky.ssf" "$W/m_sky.log"

python3 - "$DSET/qa_work/render_${NAME}.json" "$JUDGE.png" "$PRODUCT.fit" "$STACK" \
         "$SEPARATE" "$DENOISE" "$W" "$LOS" "$MID" "$HIS" "$BPFRAC" \
         "${N_SRC:-0}" "${N_LESS:-0}" "${N_MASK:-0}" "$PROVENANCE" \
         "${K_star_black}" <<'PY'
import json, os, re, sys, tempfile
(out, png, prod, src, sep, dn, W, lo, mid, hi, bp,
 nsrc, nless, nmask, prov, starblack) = sys.argv[1:17]

def stat_main(path):
    """per-channel numbers from a Siril `stat main` log — the tool measures."""
    rows = {}
    if not os.path.exists(path):
        return rows
    for line in open(path):
        m = re.search(r"(\w+) layer: Mean: ([0-9.eE+-]+), Median: ([0-9.eE+-]+), "
                      r"Sigma: ([0-9.eE+-]+), Min: ([0-9.eE+-]+), Max: ([0-9.eE+-]+), "
                      r"bgnoise: ([0-9.eE+-]+)", line)
        if m and m.group(1) in ("Red", "Green", "Blue"):
            rows[m.group(1)[0]] = {k: float(v) for k, v in zip(
                ("mean", "median", "sigma", "min", "max", "bgnoise"), m.groups()[1:])}
    return rows

def bgnoise_series(path):
    if not os.path.exists(path):
        return []
    v = [float(x) for x in re.findall(
        r"Background noise value \(channel: #\d\): [0-9.]+ \(([0-9.eE+-]+)\)", open(path).read())]
    return [v[i:i + 3] for i in range(0, len(v), 3)]

rec = {
 "render": png, "product": prod, "linear_source": src,
 "stages": {"separated": bool(int(sep)), "denoised": bool(int(dn))},
 "knob_provenance": prov,
 "stretch": {"rule": ("per-channel black point (background neutralization) + one "
                     "common window width and midtone balance (linked gain/curve)"),
             "mtf_lo_per_channel": [float(v) for v in lo.split()],
             "mtf_hi_per_channel": [float(v) for v in hi.split()],
             "mtf_mid_common": float(mid),
             "star_layer_asinh_black_point": float(starblack),
             "black_point_fraction_of_sky": float(bp),
             "note": ("derived at run time from Siril `stat main` on the layer "
                      "actually stretched, not from the star-ful input stack")},
 "measures": {
    "tool": "Siril — findstar / pm+isub+bgnoise / wavelet+wrecons+bgnoise / stat main",
    "linear_source_stat_main_x100": stat_main(f"{W}/m_source.log"),
    "stretched_layer_linear_stat_main_x100": stat_main(f"{W}/m_layer.log"),
    "rendered_sky_stat_main": stat_main(f"{W}/m_sky.log"),
    "rendered_product_stat_main": stat_main(f"{W}/m_final.log")},
 "note": ("A nonlinear stretch cannot preserve channel ratios exactly. Compare "
          "rendered_sky_stat_main against stretched_layer_linear_stat_main_x100 — "
          "those are the SAME pixels before and after the curve, so the difference "
          "is the curve's. linear_source_stat_main_x100 is the star-ful input and "
          "differs from the layer by ~0.6% in channel balance, so it is the wrong "
          "control for the sky (levels differ by the x100 fmul, ratios do not); a "
          "residual at the bright end is inherent to the curve, not a parameter "
          "error. Both sets of numbers are Siril's own."),
}
if int(sep):
    resid = bgnoise_series(f"{W}/m_sep.log")
    rec["measures"]["separation"] = {
        "findstar_stars": {"source": int(nsrc), "starless": int(nless), "mask": int(nmask)},
        "starless_pct_of_source": round(100 * int(nless) / max(int(nsrc), 1), 3),
        "screen_recombine_residual_bgnoise": resid[-1] if resid else None,
        "residual_note": ("near-vacuous by construction — Siril derives the mask by "
                          "unscreening source against starless, so the recombine "
                          "reproduces the source algebraically whatever the separation "
                          "did. Recorded because it catches clipping or a mismatched "
                          "pair; the findstar collapse is the evidence of separation.")}
if int(dn):
    pre, post = bgnoise_series(f"{W}/m_dn_pre.log"), bgnoise_series(f"{W}/m_dn_post.log")
    scales = ["1 (~1-2 px)", "2 (~2-4 px)", "3 (~4-8 px)", "4 (~8-16 px)"]
    prof = {}
    for i, nm in enumerate(scales):
        if i < len(pre) and i < len(post):
            prof[nm] = {
                "before": pre[i], "after": post[i],
                "change_pct": [round(100 * (post[i][c] / pre[i][c] - 1), 1)
                               if pre[i][c] else None for c in range(3)]}
    rec["measures"]["denoise_per_scale_bgnoise"] = {
        "atrous": "Siril `wavelet 4 2` + `wrecons` per layer, then `bgnoise`",
        "profile": prof,
        "note": ("whole-frame and per channel, so there is no region geometry to "
                 "derive from the measurement. Structure preservation is judged by "
                 "the noise_split structured term and the user's eyes on the "
                 "unresolved starlight at "
                 "1:1 (docs/dead-ends.md), not by this profile alone.")}

os.makedirs(os.path.dirname(out), exist_ok=True)
fd, tmp = tempfile.mkstemp(dir=os.path.dirname(out), suffix=".tmp")
with os.fdopen(fd, "w") as fh:
    json.dump(rec, fh, indent=1)
os.replace(tmp, out)
sky = rec["measures"]["rendered_sky_stat_main"]
lin = rec["measures"]["stretched_layer_linear_stat_main_x100"]
prod = rec["measures"]["rendered_product_stat_main"]
r = lambda d, a, b: d[a]["median"] / d[b]["median"]
if sky and lin:
    print("  rendered SKY  R/G %.4f  B/G %.4f   |  same layer, LINEAR  R/G %.4f  B/G %.4f"
          % (r(sky, "R", "G"), r(sky, "B", "G"), r(lin, "R", "G"), r(lin, "B", "G")))
if prod:
    print("  recombined product median R/G %.4f  B/G %.4f  (stars included — not the sky)"
          % (r(prod, "R", "G"), r(prod, "B", "G")))
print(f"  record -> {out}")
PY
say "DONE -> $JUDGE.png"
