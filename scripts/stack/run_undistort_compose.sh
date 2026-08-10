#!/usr/bin/env bash
# Compose already-built undistort SUB-STACKS into one deep stack — the cross-set
# final for the wide-field UNTRACKED class. run_undistort_groups.sh builds a
# set's sub-stacks (calibrate -> warp -> register -> reject, per group) and
# composes its OWN into stack_<set>_full; this composes sub-stacks from SEVERAL
# sets (or group dirs) into a single deeper stack, reusing the warping already
# done — no frame is re-processed.
#
#   run_undistort_compose.sh --out=<stack.fit> <subdir>... [--framing=min|max] [--weight=nbstack|noise]
#                            [--ref=<sub-stack path>|<1-based index>]
#
# e.g. run_undistort_compose.sh --out=web/results/july14/stack_set-01+02_full.fit \
#        july14/work/groups_set-01 july14/work/groups_set-02
#
# WHEN IT COMPOSES CLEANLY ACROSS SETS, AND WHEN IT DOES NOT. This block used to
# assert, without qualification, that "after the lens-distortion warp every
# frame-to-frame map is a pure homography, and homographies COMPOSE". That is
# true only while every member was warped by the SAME, CORRECT map. The premise
# stopped holding the moment the optical model became per-set, and nothing
# noticed: three aug06 sets were warped under three different models and composed
# into a union whose corner stars are visibly doubled.
#
# MEASURED (docs/dead-ends.md; docs/combine-contract.md) — the px
# separation of the SAME star as two registered members place it, at the composed
# canvas corner:
#   same set, same model, same state ............ 0.14 / 0.19 px   (the floor)
#   cross-set, ONE model, state matched ......... 0.35 px          (user PASSED)
#   cross-set, ONE model, state mismatched ...... 0.93 px          (round at 1:1)
#   cross-set, DIFFERENT models ................. 2.99 / 2.11 px   (user FAILED)
#   cross-NIGHT, one shared model ............... 4.07 px          (worse still)
# The residual a global homography cannot absorb is the radial one, and two
# different distortion models differ by exactly that (up to 8.19 px through the
# production warp) — so the mean of the members doubles the stars.
#
# The compose therefore GATES on model COMPATIBILITY (not identity: identical is
# only the cheap safe case, and identical-across-nights is the 4.07 px failure).
# See "THE COMPOSE GATE" below. Un-warped frames remain a separate, registered
# dead end (the residual distortion re-enters at the sub-stack join).
#
# THE COMPOSE GATE, three tiers, only the third decides:
#   T0 identity   — every member's DISTA/B/C + DISTNORM equal. Free, recorded,
#                   and it does NOT skip T2, because a shared model across nights
#                   is precisely the measured 4.07 px failure.
#   T1 prediction — the ptlens displacement difference between each member's
#                   model and the reference's, out to rho = 1.80 (the frame
#                   corner under the MEASURED half-short-side normalisation).
#                   A SCREEN ONLY: the homography absorbs part of any smooth
#                   field, so T1 over-predicts (8.19 predicted vs 2.99 realised).
#                   Its job is to name the offending pair before an hour of
#                   registration, never to pass one.
#   T2 measure    — scripts/qa/member_separation.py on the UNREGISTERED members
#                   plus the homographies `register -2pass` wrote into s_.seq,
#                   binned by each member's OWN field radius. REPORT-ONLY: it
#                   measures, prints and stamps the disagreement; it does not
#                   gate. The thresholds it used to carry were retired because
#                   the quantity mixes a real defect with one the compose makes.
#                   It reads the members, NOT the r_ copies: `seqapplyreg
#                   -framing=max` on a variable-size sequence gives each output
#                   its own origin (MEASURED 611.9 px apart on the 28-member
#                   union), so their pixel coordinates are not comparable and
#                   cross-matching them returned chance neighbours — 67 of 2000
#                   within 12 px between two members of ONE set, against 1721
#                   once the homographies re-base them (docs/dead-ends.md).
#                   Everything it needs exists straight after `register -2pass`,
#                   so this gate could run before seqapplyreg writes n full-size
#                   copies; it is left here so this change reorders nothing.
# A member with no DIST* keys (built before the stamp existed) is UNKNOWN, never
# compatible: T0/T1 report it as such and T2 still measures it.
#
# -framing=min keeps the area common to ALL sub-stacks — across sets that is the
# re-aim OVERLAP, so measure the re-aim scatter first (a large re-aim shrinks it;
# the compose work). -framing=max keeps the union (edges covered by fewer
# sub-stacks; depth/SNR fall off outward). Re-run with the same dirs to switch
# framing without recomputing sub-stacks.
#
# --ref PINS THE REFERENCE, and on a multi-night compose it must be pinned.
# `register -2pass`'s AUTO reference sets the output canvas ORIENTATION and,
# through `-norm=addscale`, the composite's raw channel BALANCE: a compose
# referenced to the wrong family measured K_B 0.846 (that member's own balance)
# with a rotated frame map, where the right reference gave 0.951 and an exact
# map. Within one night the members share a balance family and the auto pick is
# harmless. Across NIGHTS the families genuinely differ (measured on this rig:
# K_G 0.662-0.668 one night vs 0.697 another, both chain-clean — a transparency
# difference, not a defect), so whichever member the auto pick lands on silently
# decides the composite's starting balance and orientation. Pinning it makes
# that a recorded choice instead of a function of argument order. SPCC
# afterwards re-derives colour from the catalogue, so this governs the LINEAR
# composite the finish stage receives, not the final colour.
# Pick the member whose canvas the product should inherit — normally the
# deepest/most-central one. Accepts a sub-stack PATH (preferred; resolved to
# its linked index) or a bare 1-based index into the linked order.
#
# The compose is a PLAIN MEAN, never sigma rejection: sub-stacks are clean
# ~group-size means whose mutual scatter is ~sqrt(group) below per-frame noise,
# so a sigma gate across them clips real structure (star cores, MW lanes) along
# steep gradients instead of outliers (measured; docs/dead-ends.md). Rejection
# already happened WITHIN each group, at full per-frame strength.
#
# NOTHING is compressed; the generated .ssf pins setcompress 0. The flatpak
# sandbox has a private /tmp, so the scratch dir lives beside --out (under $HOME).
# WEIGHTING (--weight=nbstack | --weight=noise; default unweighted).
# A sub-stack of n frames each with per-frame variance s^2 has variance
# s^2/n, so the inverse-variance weight is n/s^2:
# - `nbstack` weights by stacked-image COUNT, i.e. by n. That IS the
#   inverse-variance weight — but ONLY while every member's per-frame noise s
#   is the same. True for members from one night/sky; the Siril doctrine that
#   nbstack is "for stacks-of-stacks" is about that regime.
# - `noise` weights by the MEMBER's measured noise, which already carries
#   s/sqrt(n) — so it yields n/s^2 in BOTH regimes and is strictly more
#   general. Prefer it for a MULTI-NIGHT compose, where sky brightness (and
#   therefore per-frame noise for a fixed object flux) differs between members
#   and count-weighting would over-weight the noisier night's frames.
#   Caveat: Siril's noise estimator conflates revealed texture with noise
#   (docs/dead-ends.md), which is tolerable here only because every member
#   shows the SAME field, so the texture term is common and largely cancels in
#   the relative weights. On members of different fields, do not trust it.
set -euo pipefail
REPO=$(cd "$(dirname "${BASH_SOURCE[0]}")"/../.. && pwd)
source "$REPO/scripts/lib/siril_run.sh"   # serialized siril-cli invoker (BACKLOG item 18)
OUT= FRAMING=min WEIGHT= REF= GATEJSON=; SUBDIRS=()
for a in "$@"; do case "$a" in
  --out=*) OUT=${a#*=};; --framing=*) FRAMING=${a#*=};;
  --weight=nbstack|--weight=noise) WEIGHT="-weight=${a#*=}";;
  --ref=*) REF=${a#*=};;
  --gate-json=*) GATEJSON=${a#*=};;
  --*) echo "unknown arg $a" >&2; exit 1;;
  *) SUBDIRS+=("$a");;
esac; done
[ -n "$OUT" ] || { echo "need --out=<stack.fit>" >&2; exit 1; }
case "$FRAMING" in min|max) ;; *) echo "--framing must be min or max" >&2; exit 1;; esac
[ ${#SUBDIRS[@]} -ge 1 ] || { echo "give at least one sub-stack dir (holding sub_*.fit)" >&2; exit 1; }
OUT=${OUT%.fit}
mkdir -p "$(dirname "$OUT")"
# Absolutize: the flatpak Siril sandbox resolves -s/-d and every `cd` in the
# .ssf from its OWN cwd, so a relative --out makes it miss the generated script.
OUT="$(cd "$(dirname "$OUT")" && pwd)/$(basename "$OUT")"
W="$(dirname "$OUT")/.compose_$(basename "$OUT")"
rm -rf "$W"; mkdir -p "$W/in" "$W/seq"
sir(){ siril_cli -d "$W" -s "$1" >> "$W/compose.log" 2>&1; }

# Gather every sub-stack into one dir as uniquely-named symlinks (siril `link`
# takes ALL images in the CWD, so the dir must hold ONLY the members; the
# per-set names collide, hence the global index). Order is immaterial to a mean.
n=0; MEMBERS=()
for d in "${SUBDIRS[@]}"; do
  [ -d "$d" ] || { echo "no such sub-stack dir: $d" >&2; exit 1; }
  shopt -s nullglob; subs=("$d"/sub_*.fit); shopt -u nullglob
  [ ${#subs[@]} -ge 1 ] || { echo "no sub_*.fit in $d" >&2; exit 1; }
  for s in "${subs[@]}"; do
    n=$((n + 1))
    MEMBERS[$n]=$(readlink -f "$s")
    ln -sf "${MEMBERS[$n]}" "$W/in/m_$(printf %05d "$n").fit"
  done
  echo "linked ${#subs[@]} sub-stacks from $(basename "$d")"
done
[ "$n" -ge 2 ] || { echo "ABORT: need >=2 sub-stacks total to register+stack, have $n" >&2; exit 1; }

# resolve --ref to a 1-based sequence index (m_ names are zero-padded in link
# order, so the linked index IS the sequence index)
SETREF=
if [ -n "$REF" ]; then
  RIDX=
  if [[ "$REF" =~ ^[0-9]+$ ]]; then
    RIDX=$REF
    [ "$RIDX" -ge 1 ] && [ "$RIDX" -le "$n" ] || {
      echo "ABORT: --ref=$REF out of range (1..$n)" >&2; exit 1; }
  else
    RP=$(readlink -f "$REF" 2>/dev/null || true)
    [ -n "$RP" ] || { echo "ABORT: --ref path does not resolve: $REF" >&2; exit 1; }
    for ((i=1; i<=n; i++)); do [ "${MEMBERS[$i]}" = "$RP" ] && RIDX=$i && break; done
    [ -n "$RIDX" ] || {
      echo "ABORT: --ref=$REF is not one of the $n linked sub-stacks" >&2
      for ((i=1; i<=n; i++)); do echo "   $i  ${MEMBERS[$i]}" >&2; done; exit 1; }
  fi
  SETREF="setref s $RIDX\n"
  echo "reference PINNED: member $RIDX -> ${MEMBERS[$RIDX]}"
else
  echo "reference: AUTO (register -2pass picks it) — pin it with --ref= for a"
  echo "  multi-night compose; the auto pick decides canvas orientation and the"
  echo "  composite's raw channel balance"
fi

# ---- T0/T1: the members' own optics provenance, from THEIR OWN HEADERS -------
# No external lookup and no machine state: that is what makes an archived
# sub-stack composable months later (stamp_headers.sh, header_provenance_lines).
GATEJSON=${GATEJSON:-$(dirname "$OUT")/compose_gate_$(basename "$OUT").json}
python3 - "$W" "${MEMBERS[@]}" <<'PY' || exit 1
import json, os, sys
import numpy as np
from astropy.io import fits             # header READ only

W, members = sys.argv[1], sys.argv[2:]
# Exactly what THIS compose consumes, and nothing aspirational: the optics the
# gate reasons on, the depth `-weight=nbstack` reads, the identity the record
# needs, the acquisition keys the product carries forward to the solve.
REQUIRED = ("DISTMODL", "DISTA", "DISTB", "DISTC", "DISTNORM", "DISTPROV",
            "DISTSRC", "CALSET", "BKGLIGHT", "STACKCNT", "EXPTIME", "LIVETIME",
            "FOCALLEN", "XPIXSZ", "DATE-OBS", "INSTRUME")
rows = []
for m in members:
    try:
        h = fits.getheader(m)
    except OSError:
        h = {}
    rows.append({"file": os.path.basename(m),
                 "set": h.get("CALSET"), "src": h.get("DISTSRC"),
                 "abc": tuple(h.get(k) for k in ("DISTA", "DISTB", "DISTC")),
                 "norm": h.get("DISTNORM"), "rho": h.get("DISTRHO"),
                 "prov": h.get("DISTPROV"), "bkg": h.get("BKGLIGHT"),
                 "missing": [k for k in REQUIRED if h.get(k) is None]})

# THE DEPENDENCY RULE, checked rather than asserted: combining must need ONLY the
# stamped files. Every input this compose consumes comes from a member's own
# header or its own pixels — T0/T1 from DIST*, `-weight=nbstack` from STACKCNT,
# `-norm=addscale` and `register`/`seqapplyreg` from pixels, T2 from pixels. No
# record, no machine state, no repo. REQUIRED is that consumption list; a member
# missing any of it is OUTSIDE THE CONTRACT and is named as such.
# DISTRHO is deliberately NOT required: "unmeasured" is a legitimate value for an
# inherited state whose fit artifacts do not exist, and a required key with a
# legitimate empty value teaches readers to ignore the check.
outside = [r for r in rows if r["missing"]]
print(f"compose gate T0: {len(rows) - len(outside)}/{len(rows)} members are "
      "self-describing (contract-complete)")
for r in outside:
    print(f"  OUTSIDE THE CONTRACT: {r['file']} missing {','.join(r['missing'])} — "
          "run scripts/stack/backfill_substack_provenance.sh. T2 still measures it; "
          "a header describes, only the measurement decides.")
prov = sorted({r["prov"] or "unstamped" for r in rows})
if prov != ["stamped"]:
    print(f"  provenance class: {', '.join(prov)} — `backfill` values were "
          "reconstructed from committed records, not stamped from the model "
          "verified live at warp time")
# Background state is a PROCESSING state exactly like optical state: members
# carrying different sky baselines are being averaged together. Surfaced the same
# way, and NOT auto-blocked — the one measured arm (subsky_lights_restoration)
# came out judge-equivalent on the corners, so there is no measurement that
# supports blocking, and inventing a threshold here would be the guessing this
# repo forbids. Named loudly so the operator decides with it in view.
bkg = sorted({r["bkg"] or "unstamped" for r in rows})
if len(bkg) > 1:
    print(f"  !! MIXED BACKGROUND TREATMENT across members: {', '.join(bkg)}")
    for b in bkg:
        who = ", ".join(r["set"] or r["file"] for r in rows if (r["bkg"] or "unstamped") == b)
        print(f"       {b}: {who}")
    print("     These members do not share a sky baseline. Not blocked (no "
          "measurement supports a threshold), but a level step in the union is "
          "the expected consequence — judge the surface at 1:1.")
elif bkg:
    print(f"  background treatment: {bkg[0]} (uniform)")
known = [r for r in rows if None not in r["abc"] and r["norm"]]
unknown = [r for r in rows if r not in known]
for r in unknown:
    print(f"  UNKNOWN optics: {r['file']} — no usable DIST* keys. "
          "Treated as UNKNOWN, never as compatible; T2 still measures it.")
states = sorted({(r["abc"], r["norm"]) for r in known})
if len(states) == 1 and not unknown:
    print("  T0: IDENTICAL model across every member (the cheap safe case)")
elif known:
    print(f"  T0: {len(states)} DISTINCT models across the members:")
    for s in states:
        who = ", ".join(r["set"] or r["file"] for r in known if (r["abc"], r["norm"]) == s)
        print(f"       a={s[0][0]:.8g} b={s[0][1]:.8g} c={s[0][2]:.8g}  <- {who}")

# T1 — SCREEN ONLY. Predicted radial displacement difference between each
# model and the first, out to rho = 1.80 (the frame corner under the MEASURED
# half-short-side normalisation). Over-predicts by construction, because the
# compose's homography absorbs part of any smooth field: 8.19 px predicted
# against 2.99 px realised on the aug06 union. Never passes anything.
t1 = None
if len(states) > 1:
    def disp_px(abc, norm):
        """ptlens displacement in PX at physical radius r, evaluated on the grid
        r = 0 .. 1.80 x norm (the frame corner). Each model uses its own norm."""
        a, b, c = (float(x) for x in abc)
        d = 1 - a - b - c
        r = np.linspace(0, 1.80 * float(norm), 181)
        rho = r / float(norm)
        return r * (1 - (a*rho**3 + b*rho**2 + c*rho + d))
    ref = disp_px(*states[0])
    t1 = max(float(np.max(np.abs(disp_px(*s) - ref))) for s in states[1:])
    print(f"  T1 (screen only, over-predicts): peak predicted model divergence "
          f"{t1:.2f} px out to the corner (rho=1.80)")
json.dump({"members": rows, "distinct_models": len(states),
           "required_keys": list(REQUIRED),
           "outside_contract": [r["file"] for r in outside],
           "provenance_classes": prov, "background_states": bkg,
           "unknown_optics": [r["file"] for r in unknown],
           "t1_predicted_peak_px": t1},
          open(os.path.join(W, "gate_t0t1.json"), "w"), indent=1)
PY

# %b (not %s) for the setref line: it carries its own trailing newline as an
# escape, and collapses to nothing when the reference is left AUTO.
# SPLIT IN TWO: the registration must finish and be MEASURED (T2) before
# anything is stacked, because a smearing compose has to be impossible to build,
# not merely detectable afterwards.
printf 'requires 1.2.0\nset32bits\nsetcompress 0\nsetext fit\ncd %s\nlink s -out=%s\ncd %s\nregister s -2pass\n%bseqapplyreg s -framing=%s -prefix=r_\n' \
  "$W/in" "$W/seq" "$W/seq" "$SETREF" "$FRAMING" > "$W/compose.ssf"
printf 'requires 1.2.0\nset32bits\nsetcompress 0\nsetext fit\ncd %s\nstack r_s mean none -norm=addscale %s -output_norm -out=%s\n' \
  "$W/seq" "$WEIGHT" "$OUT" > "$W/stack.ssf"
# State the weighting explicitly: "plain mean" printed unconditionally would be
# a WRONG RECORD whenever --weight=nbstack was passed, and this log is the
# build's provenance.
case "$WEIGHT" in
  -weight=nbstack) WDESC="weighted by stacked-image count (nbstack)";;
  -weight=noise)   WDESC="weighted by member noise, inverse-variance (noise)";;
  *)               WDESC="unweighted";;
esac
echo "composing $n sub-stacks (register -2pass -> ${SETREF:+setref $RIDX -> }-framing=$FRAMING -> mean, no rejection, $WDESC)"
sir "$W/compose.ssf"
ls "$W/seq"/r_s_*.fit >/dev/null 2>&1 || { echo "REGISTRATION FAILED — read $W/compose.log" >&2; exit 1; }

# ---- T2: the member-disagreement MEASUREMENT, recorded before `stack` -------
# --prefix defaults to s_ (the members + the .seq holding register -2pass's own
# homographies). It is NOT r_: those copies do not share an origin.
# REPORT-ONLY, deliberately. It carried PASS/WARN/BLOCK bands anchored to six
# products the owner judged, and they were retired (user-ratified) because the
# number they gated is a SUM OF TWO TERMS and one of them the compose itself
# creates: two internally healthy sets read 1.12 and 0.95 px composed among
# themselves and 3.02 and 3.38 px registered inside a 41-degree 28-member
# sequence. A band on that would have fired on every real compose, and a check
# that always fires trains the operator to bypass it — the same disease as a
# check that cannot fail (docs/dead-ends.md). The number is measured, printed
# and stamped on the product; what it means is not decided here.
python3 "$REPO/scripts/qa/member_separation.py" "$W/seq" \
  --json="$GATEJSON" --label="$(basename "$OUT")"

sir "$W/stack.ssf"
[ -f "$OUT.fit" ] || { echo "STACK FAILED — read $W/compose.log" >&2; exit 1; }
# the gate's worst measured separation rides ON the product, not only beside it
python3 - "$OUT.fit" "$GATEJSON" <<'PY'
import json, sys
from astropy.io import fits
try:
    d = json.load(open(sys.argv[2]))
except (OSError, ValueError):
    sys.exit(0)
w = (d.get("worst") or {}).get("max_px")
if w is not None:
    fits.setval(sys.argv[1], "MAXMSEP", value=float(w),
                comment="worst member separation px (compose gate)")
models = {tuple(v.get(k) for k in ("DISTA", "DISTB", "DISTC"))
          for v in (d.get("optics") or {}).values()}
fits.setval(sys.argv[1], "NDISTMOD", value=len(models),
            comment="distinct distortion models composed")
fits.setval(sys.argv[1], "MSEPVERD", value=str(d.get("verdict", ""))[:20],
            comment="compose gate verdict")
PY
rm -rf "$W"
echo "=== DONE: $OUT.fit ($n sub-stacks, framing=$FRAMING) ==="
ls -la "$OUT.fit"
