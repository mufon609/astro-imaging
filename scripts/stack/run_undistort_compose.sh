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
#                   gate. It carries NO thresholds: the quantity mixes a real
#                   defect with one the compose itself makes.
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
# composite the finish stage receives, not the final colour. The reference's
# per-channel IKSS location/scale — the composite's own sky and dispersion by
# construction, now that the stack is not output-normalized — is stamped on
# the product as ANCLOC*/ANCSCL* (ANCREF, ANCSRC) from siril's own r_s_.seq
# M lines (the anchor stamp below).
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
source "$REPO/scripts/lib/siril_run.sh"   # serialized siril-cli invoker (BACKLOG:removal-conditions)
source "$REPO/scripts/stack/stamp_headers.sh"   # composite provenance + registration-model stamp
OUT= FRAMING=min WEIGHT= REF= GATEJSON= STARPAIR=0 REFSRC_DECL=auto KEEPWORK=0; SUBDIRS=()
for a in "$@"; do case "$a" in
  --out=*) OUT=${a#*=};; --framing=*) FRAMING=${a#*=};;
  --weight=nbstack|--weight=noise) WEIGHT="-weight=${a#*=}";;
  --ref=*) REF=${a#*=};;
  # --keep-work: do not delete the compose scratch at the end. The linked
  # members + the s_.seq the registration wrote are the ONLY inputs
  # member_separation.py needs, and they exist nowhere else — without this
  # flag, re-binning or re-measuring the member disagreement costs a full
  # re-compose. The r_ registered copies are the bulk and are NOT needed by
  # that measurement; delete them by hand if the space matters.
  --keep-work) KEEPWORK=1;;
  --gate-json=*) GATEJSON=${a#*=};;
  --starpair) STARPAIR=1;;
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
sir(){ siril_run_logged "$W" "$1" "$W/compose.log"; }

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
  REFSRC_DECL=pinned
  echo "reference PINNED: member $RIDX -> ${MEMBERS[$RIDX]}"
else
  # DERIVE IT WHEN THE MEMBERS SPAN MORE THAN ONE NIGHT. Siril's auto pick is
  # INDEX 0 — the first member in link order, measured across ten compose_gate
  # records at 13/17/22/25/52/77 members — so without this the reference, and
  # with it the composed canvas, is a function of ARGUMENT ORDER. Reordering the
  # session arguments re-bases the product with nothing in any record to show it.
  # No choice of reference is materially BETTER (SPCC absorbs the balance 64x and
  # -framing=max includes every member either way, so the sky union is identical);
  # what is defective is that it is undetermined. scripts/stack/derive_compose_ref.py
  # carries the rule, its measurements and its selftest. Single-night sets are
  # left on AUTO deliberately: their members share a balance family, and not
  # touching them keeps every single-night product bit-identical.
  DIDX=$(python3 "$REPO/scripts/stack/derive_compose_ref.py" "${MEMBERS[@]:1:$n}"            --json="$W/derive_ref.json") || {
    echo "ABORT: derive_compose_ref refused the members (above)" >&2; exit 3; }
  if [ "${DIDX:-0}" -gt 0 ] 2>/dev/null; then
    RIDX=$DIDX
    SETREF="setref s $RIDX\n"
    REFSRC_DECL=derived
    echo "reference DERIVED: member $RIDX -> ${MEMBERS[$RIDX]}"
    echo "  (multi-night; most-central member by centre-pixel pointing. Override"
    echo "   with --ref=<path|index>; the rule + its numbers are in"
    echo "   scripts/stack/derive_compose_ref.py)"
  else
    echo "reference: AUTO (siril picks it — measured to be index 0, the first"
    echo "  member in link order). Single night, or nothing measurable to derive"
    echo "  from; pin it with --ref= to override."
  fi
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
          "rebuild the member, or restore the retired backfill_substack_provenance.sh "
          "from git history (retired at its fired condition: 93/93 on-rig sub-stacks "
          "stamped). T2 still measures it; a header describes, only the measurement "
          "decides.")
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
# ---- REGISTRATION MODEL, and the guard that makes skipping it impossible ----
# `register -2pass` fits ONE star-pair homography per member against a common
# reference. Across sets/nights the members' optical axes span ~13 deg of RA and
# a single projective fit cannot carry that: MEASURED on the 28-member union at
# RA 294.86, star-pair reads FWHM 4.383 / roundness 0.458 where astrometric
# reads 2.678 / 0.974 — the clean band of the same union is 0.961-0.968, so the
# defect is REMOVED, not reduced, with no regression in the clean band, star
# counts within 1-2%, MORE sky covered (800.1 vs 773.5 sq.deg) and a north-up
# framing instead of the pinned member's arbitrary one.
# `seqplatesolve` derives registration from each member's OWN solution and
# `seqapplyreg` applies that member's OWN SIP undistortion before projecting —
# which requires every member to carry TAN+SIP. Siril does NOT complain when
# they do not; it registers what it can and exports a finished-looking product.
# So the chain asserts, twice: compose_preflight.py before, and the tool's own
# log lines after.
if [ "$STARPAIR" = 1 ]; then
  echo "" >&2
  echo "  *** STAR-PAIR REGRESSION ARM — register -2pass, NOT the shipped route ***" >&2
  echo "  *** measured at roundness 0.458 against astrometric's 0.974 on the    ***" >&2
  echo "  *** 28-member union. This is for A/B work only; it must never build   ***" >&2
  echo "  *** a product anyone judges or ships.                                 ***" >&2
  echo "" >&2
  REGCMD='register s -2pass -transf=homography'
  REGDESC='register -2pass -transf=homography [STAR-PAIR REGRESSION ARM]'
else
  "$REPO/scripts/stack/compose_preflight.py" "$W"/in/m_*.fit \
    --json="$W/compose_preflight.json" || {
      echo "" >&2
      echo "  compose_preflight REFUSED the members (above). Solve them, or pass" >&2
      echo "  --starpair to build the measured-worse regression arm deliberately." >&2
      exit 3; }
  REGCMD='seqplatesolve s'
  REGDESC='seqplatesolve (per-member astrometric, own SIP undistortion)'
fi
printf 'requires 1.2.0\nset32bits\nsetcompress 0\nsetext fit\ncd %s\nlink s -out=%s\ncd %s\n%s\n%bseqapplyreg s -framing=%s -prefix=r_ -interp=lanczos4\n' \
  "$W/in" "$W/seq" "$W/seq" "$REGCMD" "$SETREF" "$FRAMING" > "$W/compose.ssf"
# NO -output_norm. It is a global min-max rescale — ONE (min, max) over all three
# channels, (v − min)/(max − min) — so the product's level and R:G:B balance were
# set by a single darkest pixel (lanczos4 undershoot beside whichever bright star
# rings deepest: a geometry lottery) and the reference's level CANCELLED (four
# setref runs moved products ≤2.4% where "the reference is the anchor" predicted
# 1.7-2.3×). Without it the product's sky is the reference member's own IKSS
# location per channel (measured 0.3-0.5% under it, the coverage/gradient term)
# and values outside [0,1] clamp (measured: 4 pixels of 30.1 M, one saturated
# core). Registry: docs/dead-ends/stacking-compose.md, the -output_norm
# zero-point entry (mechanism, the shipped design, the accepted campaign).
# REMOVAL CONDITION: siril offers a reference-anchored (or per-channel,
# non-min-max) output normalization — then -output_norm returns and the ANC*
# anchor keys retire with it.
printf 'requires 1.2.0\nset32bits\nsetcompress 0\nsetext fit\ncd %s\nstack r_s mean none -norm=addscale %s -out=%s\n' \
  "$W/seq" "$WEIGHT" "$OUT" > "$W/stack.ssf"
# State the weighting explicitly: "plain mean" printed unconditionally would be
# a WRONG RECORD whenever --weight=nbstack was passed, and this log is the
# build's provenance.
case "$WEIGHT" in
  -weight=nbstack) WDESC="weighted by stacked-image count (nbstack)";;
  -weight=noise)   WDESC="weighted by member noise, inverse-variance (noise)";;
  *)               WDESC="unweighted";;
esac
echo "composing $n sub-stacks ($REGDESC -> ${SETREF:+setref $RIDX -> }-framing=$FRAMING -> mean, no rejection, $WDESC)"
sir "$W/compose.ssf"
ls "$W/seq"/r_s_*.fit >/dev/null 2>&1 || { echo "REGISTRATION FAILED — read $W/compose.log" >&2; exit 1; }
# POST-ASSERT: the preflight proves the members COULD carry it; only siril's own
# log proves it DID. Without this, a future siril that quietly falls back to a
# linear solution would regress the product with nothing to show for it.
if [ "$STARPAIR" != 1 ]; then
  grep -q "Astrometric registration computed" "$W/compose.log" || {
    echo "ABORT: siril did not report 'Astrometric registration computed' — the" >&2
    echo "  compose did NOT use per-member astrometric registration. Read $W/compose.log" >&2; exit 4; }
  grep -qi "undistortion will be applied" "$W/compose.log" || {
    echo "ABORT: siril did not report applying undistortion — the members' own SIP" >&2
    echo "  was DISCARDED, which is the whole point of this route. Read $W/compose.log" >&2; exit 4; }
  echo "compose: astrometric registration + per-member undistortion CONFIRMED in siril's log"
fi

# ---- T2: the member-disagreement MEASUREMENT, recorded before `stack` -------
# --prefix defaults to s_ (the members + the .seq holding register -2pass's own
# homographies). It is NOT r_: those copies do not share an origin.
# REPORT-ONLY, deliberately. It carries NO PASS/WARN/BLOCK bands (user-ratified):
# the number such a band would gate is a SUM OF TWO TERMS and one of them the
# compose itself creates — two internally healthy sets read 1.12 and 0.95 px
# composed among
# themselves and 3.02 and 3.38 px registered inside a 41-degree 28-member
# sequence. A band on that would have fired on every real compose, and a check
# that always fires trains the operator to bypass it — the same disease as a
# check that cannot fail (docs/dead-ends.md). The number is measured, printed
# and stamped on the product; what it means is not decided here.
python3 "$REPO/scripts/qa/member_separation.py" "$W/seq" \
  --json="$GATEJSON" --label="$(basename "$OUT")" \
  --regmodel="$([ "$STARPAIR" = 1 ] && echo starpair || echo astrometric)"

sir "$W/stack.ssf"
[ -f "$OUT.fit" ] || { echo "STACK MISSING — read $W/compose.log" >&2; exit 1; }
# POST-ASSERT on siril's OWN log line (the pattern of the astrometric greps
# above): `stack` prints exactly one of "Output normalization ...... enabled" /
# "...... disabled". Both siril runs of this compose append to compose.log and
# only `stack` prints the line; the scratch is recreated per run, so no stale
# line can reach this grep.
grep -q "Output normalization ...... disabled" "$W/compose.log" \
  && ! grep -q "Output normalization ...... enabled" "$W/compose.log" || {
  echo "ABORT: siril did not report 'Output normalization ...... disabled' — the" >&2
  echo "  product's zero point would be the min-max lottery this route retired" >&2
  echo "  (docs/dead-ends/stacking-compose.md). Read $W/compose.log" >&2; exit 4; }

# ---- STAMP THE COMPOSITE'S OWN IDENTITY -------------------------------------
# siril's `stack` propagates the REFERENCE member's header, so without this a
# 28-member cross-night union ships claiming `CALSET = july31/set-01` and that
# set's flat — one set's identity asserted for a composite of six sets across two
# nights. Worse than an absent stamp: a gate reading it is told a confident
# falsehood. This replaces the inherited keys with the composite's own — the
# common value where members agree, MIXED(n) where they do not — and records
# what registered it, which no header has ever carried.
if [ "$STARPAIR" = 1 ]; then REGM=starpair; else REGM=astrometric; fi
REGU=F
grep -qi "undistortion will be applied" "$W/compose.log" 2>/dev/null && REGU=T
# Applied with a FITS library, not siril `update_key`: CALSET/CALSETS are
# `<session>/<set>` and siril cuts a string value at the first `/` (it begins the
# FITS comment field). See header_apply_keys.
# THE REFERENCE SIRIL ACTUALLY USED, read from the sequence file IT wrote —
# never the value this script asked for. Under --ref the two agree; under AUTO
# nothing was asked and only siril knows, and that is exactly the case the
# record has been missing. The `.seq` S-line's 7th field is `reference_image`,
# 0-based (the same field scripts/qa/member_separation.py parses). This runs
# BEFORE the `rm -rf "$W"` at the end, which is the only window it exists in.
REFID= REFSRC=
REF0=$(awk '$1=="S" && NF>=7 {print $7; exit}' "$W/seq/s_.seq" 2>/dev/null || true)
if [ -n "${REF0:-}" ] && [ "$REF0" -ge 0 ] 2>/dev/null && [ "$REF0" -lt "$n" ]; then
  RM=${MEMBERS[$((REF0 + 1))]}
  # <1-based index>:<night>/<group dir>/<file> — a basename alone cannot identify
  # a member (sub_01.fit exists in every group dir), so the path tail rides along.
  REFID="$((REF0 + 1)):$(echo "$RM" | awk -F/ '{print $(NF-3)"/"$(NF-1)"/"$NF}')"
  REFSRC=${REFSRC_DECL:-auto}
else
  echo "WARNING: could not read the reference from $W/seq/s_.seq — REGREF unstamped" >&2
fi
# THE NORMALIZATION ANCHOR, from the statistics siril itself wrote. `stack
# -norm=addscale` maps every member onto the r_s_ sequence's REFERENCE — its
# IKSS location and scale per channel (normalization.c
# compute_factors_from_estimators), computed on the registered r_ copies and
# cached in r_s_.seq as `M<layer>-<image0>` lines: total ngoodpix mean median
# sigma avgDev mad sqrtbwmv location scale min max normValue bgnoise. With
# -output_norm gone the product's sky IS that location, so the anchor is a
# recorded physical number. The index is r_s_.seq's OWN S-line reference
# (field 7, 0-based) — the sequence `stack` normalized against (a `setref r_s N`
# before `stack` moved the normalization, measured) — never s_.seq's: whether
# `setref s N` propagates into r_s_ on the --ref/derived path is unmeasured, so a
# disagreement is printed, and what r_s_.seq says is what is stamped. Same
# window as REGREF: r_s_.seq exists only until the `rm -rf "$W"` below. Values
# are siril's own [0,1] floats as written; ×65535 for ADU16.
ANCHOR= ANCREF=
RS0=$(awk '$1=="S" && NF>=7 {print $7; exit}' "$W/seq/r_s_.seq" 2>/dev/null || true)
if [ -n "${RS0:-}" ] && [ "$RS0" -ge 0 ] 2>/dev/null && [ "$RS0" -lt "$n" ]; then
  [ "$RS0" = "${REF0:-}" ] || echo "WARNING: r_s_.seq reference $RS0 != s_.seq reference ${REF0:-?} (0-based) — the stack normalized against $RS0; ANCREF stamps that, REGREF stamps the registration's" >&2
  ANCREF=$((RS0 + 1))
  ANCHOR=$(awk -v r="$RS0" '$1=="M0-"r{l0=$10;s0=$11} $1=="M1-"r{l1=$10;s1=$11} $1=="M2-"r{l2=$10;s2=$11}
    END{ if (l0!="" && l1!="" && l2!="") printf "update_key ANCLOCR %s\nupdate_key ANCLOCG %s\nupdate_key ANCLOCB %s\nupdate_key ANCSCLR %s\nupdate_key ANCSCLG %s\nupdate_key ANCSCLB %s\n", l0, l1, l2, s0, s1, s2 }' "$W/seq/r_s_.seq")
  [ -n "$ANCHOR" ] || echo "WARNING: no M lines for reference $RS0 in $W/seq/r_s_.seq — ANCLOC*/ANCSCL* unstamped" >&2
else
  echo "WARNING: could not read the reference from $W/seq/r_s_.seq — anchor unstamped" >&2
fi
header_apply_keys "$OUT.fit" "$(header_composite_provenance_lines "$REPO" "${MEMBERS[@]}")
$(header_registration_lines "$REGM" "$REGU" "$REFID" "$REFSRC")
update_key STACKNRM addscale
update_key ANCSRC \"r_s_.seq M-line IKSS loc/scale of ANCREF; [0,1] float, x65535=ADU16\"
${ANCREF:+update_key ANCREF $ANCREF}
$ANCHOR"
echo "stamped composite provenance onto $(basename "$OUT.fit") (REGMODEL=$REGM REGUNDIS=$REGU, ${#MEMBERS[@]} members${REFID:+, REGREF=$REFID [$REFSRC]}, STACKNRM=addscale${ANCREF:+, ANCREF=$ANCREF}${ANCHOR:+ + ANCLOC/ANCSCL R,G,B})"
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
                comment="worst member sep px (H-only; incl member SIP if astrometric)")
models = {tuple(v.get(k) for k in ("DISTA", "DISTB", "DISTC"))
          for v in (d.get("optics") or {}).values()}
fits.setval(sys.argv[1], "NDISTMOD", value=len(models),
            comment="distinct distortion models composed")
fits.setval(sys.argv[1], "MSEPVERD", value=str(d.get("verdict", ""))[:20],
            comment="compose gate verdict")
PY
[ "$KEEPWORK" = 1 ] && echo "compose scratch KEPT at $W (--keep-work): s_*.fit + s_.seq are what member_separation.py reads" || rm -rf "$W"
echo "=== DONE: $OUT.fit ($n sub-stacks, framing=$FRAMING) ==="
ls -la "$OUT.fit"
