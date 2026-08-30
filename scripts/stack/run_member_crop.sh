#!/usr/bin/env bash
# run_member_crop.sh — THE PORTION RULE AS A CHAIN STAGE: between the per-set
# sub-stacks and the compose, profile every member, crop the measured-bad
# entry-side zone off a COPY, and hand the compose a curated dir.
#
#   run_member_crop.sh <session-dir>... --out=<curated dir> [--bar=<px>] [--half-width=<px>]
#                      [--ref=<member path>] [--recipe=<json>] [--record=<json>]
#                      [--profiles=<json>] [--cache=<json>] [--tag=<name>]
#                      [--allow-ref-crop] [--members-dir=<dir holding sub_*.fit>]
#   run_member_crop.sh --selftest
#
# WHAT IT DOES (every pixel operation and every measurement is Siril's):
#   1. members  — the canonical member dirs of the sessions given, through the ONE
#                 enumerator run_corpus_combine.sh also uses (scripts/lib/member_dirs.sh);
#                 members in canonical order (session order as given, sub_*.fit sorted).
#   2. profile  — Siril findstar at star_stations.py's stations on every member
#                 (member_profile.py profile: one Siril run per member, lists kept),
#                 THROUGH THE TRACKED PROFILE CACHE (--cache, default
#                 datasets/corpus/member_selection/profiles.json): a member whose
#                 content sha256 and measuring geometry match its cache entry is
#                 served from the cache; only new/changed members are profiled, and
#                 the run SAYS which. --profiles=<json> bypasses both (a pre-written
#                 table; the selftest's rule/crop path).
#   3. rule     — the ASYMMETRY rule: onset = the smallest dx where FWHM(+dx) − FWHM(−dx)
#                 > bar and stays above outward; x_c = onset − half-width; no station
#                 over the bar → untouched. EVERY constant (bar, stations, radius,
#                 top-N, half-width) comes from the recipe
#                 (member_selection.portion_rule, datasets/corpus/recipe.json) and is
#                 echoed; --bar/--half-width override the recipe ALOUD. S_i (mean over
#                 the centre + exit-side stations) is REPORTED beside it as an
#                 advisory — never a gate (member_profile.py's docstring, GO #16).
#   4. curated  — <out>/sub_NNN_<night>_<set>_<sub>.fit: a SYMLINK to the original for
#                 an untouched member, a Siril-cropped 32-bit COPY (`crop 0 0
#                 round(W/2+x_c) H`) for a cropped one, stamped MEMCROP=<x_c>,
#                 MEMCRULE="asym>0.20px@r400 top30" (%.2f from the bar — the
#                 aggregation identity key, pinned), MEMCSCOR=<S_i> (Siril update_key)
#                 and MEMCPROV=<record path> (header_apply_keys — Siril's update_key cuts
#                 a string at `/`, stamp_headers.sh). Originals are never written.
#   5. verify   — per copy: kept pixels identical to the original's first kept_width
#                 columns, CRPIX/CRVAL/SIP unchanged, the T0 provenance keys present, a
#                 single matrix form, the four MEMC* keys; per symlink: resolves to the
#                 original, no MEMC* keys. The result lands in the tracked record.
#   6. record   — --record (default datasets/corpus/member_selection/<tag>.json): the
#                 per-member table with all stations, S_i, onset, x_c,
#                 cropped/untouched, the bar, the reference, the instrument line, the
#                 curated listing with each entry's target, the verification.
#
# MEASURED WHY (cropT_arm.json, cropTselT_arm.json; ledger 111-118): the corpus's
# left band went 2.967/2.935/2.925/2.877 → 2.790/2.805/2.810/2.792 px at the
# canonical's depth and interior with no seam at any of the 27 crop boundaries;
# the asymmetry keys on the night-dependent entry-side excess the raws carry; the
# frame-level rule on top of it was a NULL. SCOPE: the corpus combine only
# (run_corpus_combine.sh --portion-rule) — within one night the rule crops every
# member alike, and the gain exists only where another member's better columns
# cover the same sky; the per-set finals are not run through it until measured.
# CENTRE-ROW ONLY — MEASURED TO STAY SO: the stations sit on the member's centre
# row. The rows were profiled (datasets/corpus/smear_attribution/row_profiles.json):
# the bottom row crosses the bar ~600 px earlier on 5/5 cropped members, and the
# row-resolved crop built on that (x_c = min over rows, rowmin_arm.json) was a
# clean NULL — probes at the removed columns −0.004..−0.033 px, corners <= 0.02,
# at +1.2 % pixel-frames — so the centre row stands; the top row's SYMMETRIC
# 0.4–0.5 px softness on the soft nights is the open case this rule is blind to
# by design (docs/dead-ends/stacking-compose.md). A station skipped
# for member width VETOES the rule's outward tail (no crop on incomplete outward
# evidence) and is warned aloud per member. THE PINNED REFERENCE (--ref) is
# refused for cropping — exit 3 — unless --allow-ref-crop, and then the crop is
# said aloud (the compose's zero point is the reference's own sky; a cropped
# anchor is untested). Without --ref (the corpus combine derives its reference
# after this stage) no refusal applies; run_corpus_combine.sh reads the derived
# reference back against this record after the compose and marks
# reference_cropped=true in it, loudly, if the rule cropped that member.
#
# --selftest: synthetic members (member_profile.py fixtures) + a pre-written profile
# table exercise rule → plan → record → Siril crop + stamp → verify: a PLANTED member
# whose asymmetry crosses the bar at +1800 MUST come out cropped at 1500 with the
# four MEMC* keys and identical kept pixels; a FLAT one MUST be a symlink with no
# MEMC* keys; a member with a SYMMETRIC rise on both sides (the refuted intrinsic
# form) MUST NOT crop; the pinned-reference refusal MUST fire (exit 3) and
# --allow-ref-crop MUST lift it aloud; the CACHE path MUST serve a run entirely
# from a seeded cache (0 profiled, cache file byte-identical, verdicts equal to the
# table-driven run); and verify's SIP criterion has a positive control in BOTH
# directions — the fixture's 17-digit coefficients make the Siril crop re-serialize
# them at 15 digits (the real-member effect measured at GO #17B: 36/1107 values
# moved <= 4.49e-15 on the 27 copies) and verify MUST pass with max_rel_sip > 0,
# while a scratch copy with one coefficient altered by 1e-6 relative (the change a
# re-solve or a wrong crop makes) MUST fail both assertions. `profile`'s Siril
# findstar leg and the cache miss-then-write path were exercised at GO #17B on the
# real 77 (identity + determinism held), not here.
#
# REMOVAL CONDITION: retire when Siril's compose accepts per-member weight maps or a
# per-member region mask (a mask is the crop without the coverage cost). Registered
# in BACKLOG `removal-conditions`.
set -uo pipefail
REPO=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
. "$REPO/scripts/lib/member_dirs.sh"
. "$REPO/scripts/lib/siril_run.sh"
. "$REPO/scripts/stack/stamp_headers.sh"          # header_apply_keys (astropy setval; the `/` trap)
PROF="$REPO/scripts/stack/member_profile.py"

OUT= BAR= HW= REF= RECIPE="$REPO/datasets/corpus/recipe.json" RECORD= PROFILES= TAG= ALLOWREF= MDIR=
CACHE="$REPO/datasets/corpus/member_selection/profiles.json"; SESSIONS=()
for a in "$@"; do case "$a" in
  --selftest) SELFTEST=1;;
  --out=*) OUT=${a#*=};; --bar=*) BAR=${a#*=};; --half-width=*) HW=${a#*=};; --ref=*) REF=${a#*=};;
  --recipe=*) RECIPE=${a#*=};; --record=*) RECORD=${a#*=};; --profiles=*) PROFILES=${a#*=};;
  --cache=*) CACHE=${a#*=};; --tag=*) TAG=${a#*=};;
  --allow-ref-crop) ALLOWREF=1;; --members-dir=*) MDIR=${a#*=};;
  --*) echo "unknown arg $a" >&2; exit 1;;
  *) SESSIONS+=("$a");;
esac; done

selftest() {
  local T="$HOME/.cache/astro-imaging/member_crop_selftest" fails=0 rc
  rm -rf "$T"; mkdir -p "$T"
  python3 "$PROF" fixtures --out="$T/fx" || { echo "  FAIL  fixtures"; return 1; }
  local D="$T/fx/groups_set-01" P="$T/fx/profiles.json" RC="$T/fx/recipe.json" CJ="$T/fx/cache.json"
  check() { local name=$1 cond=$2 detail=${3:-}; if [ "$cond" = 1 ]; then echo "  PASS  $name $detail"; else echo "  FAIL  $name $detail"; fails=$((fails+1)); fi; }
  # A. the pinned reference is the planted (cropped) member -> REFUSED, exit 3, nothing written
  "$0" --members-dir="$D" --out="$T/curA" --bar=0.20 --recipe="$RC" --profiles="$P" --ref="$D/sub_01.fit" --record="$T/recA.json" --tag=selftestA >"$T/A.log" 2>&1; rc=$?
  check "A: pinned reference cropped by the rule -> REFUSED (exit 3)" "$([ $rc -eq 3 ] && grep -q REFUSED "$T/A.log" && ! ls "$T/curA"/sub_*.fit >/dev/null 2>&1 && echo 1 || echo 0)" "rc=$rc"
  # B. the normal run, reference = the flat member
  "$0" --members-dir="$D" --out="$T/curB" --bar=0.20 --recipe="$RC" --profiles="$P" --ref="$D/sub_02.fit" --record="$T/recB.json" --tag=selftestB >"$T/B.log" 2>&1; rc=$?
  check "B: stage runs (rule -> plan -> Siril crop+stamp -> verify), exit 0" "$([ $rc -eq 0 ] && echo 1 || echo 0)" "rc=$rc $(tail -1 "$T/B.log")"
  python3 - "$T" "$D" <<'PY' || fails=$((fails+1))
import json, os, sys
import numpy as np
from astropy.io import fits
T, D = sys.argv[1], sys.argv[2]
rec = json.load(open(f"{T}/recB.json")); cur = f"{T}/curB"; ok = True
def check(name, cond, detail=""):
    global ok
    print(f"  {'PASS' if cond else 'FAIL'}  {name} {detail}"); ok = ok and cond
listing = rec.get("curated_listing") or {}
tab = rec["table"]; byname = {v["member"].split("/")[-1]: (k, v) for k, v in tab.items()}
k1, r1 = byname["sub_01.fit"]; k2, r2 = byname["sub_02.fit"]; k3, r3 = byname["sub_03.fit"]
check("B: planted member cropped at onset 1800 -> x_c 1500", r1["cropped"] and r1["onset"] == 1800 and r1["x_c"] == 1500, f"onset {r1['onset']} x_c {r1['x_c']}")
copy = os.path.join(cur, k1); check("B: the copy is a FILE, not a link", os.path.isfile(copy) and not os.path.islink(copy))
h = fits.getheader(copy) if os.path.isfile(copy) else {}
check("B: kept width = round(W/2 + x_c) = 4500", h.get("NAXIS1") == 4500, f"NAXIS1 {h.get('NAXIS1')}")
check("B: MEMCROP 1500, MEMCRULE the pinned literal, MEMCSCOR, MEMCPROV", int(h.get("MEMCROP", -1)) == 1500 and str(h.get("MEMCRULE", "")) == "asym>0.20px@r400 top30" and h.get("MEMCSCOR") is not None and bool(h.get("MEMCPROV")), f"{h.get('MEMCROP')} {h.get('MEMCRULE')!r} {h.get('MEMCSCOR')} {h.get('MEMCPROV')!r}")
check("B: kept pixels identical to the original's first 4500 columns", os.path.isfile(copy) and np.array_equal(fits.getdata(f"{D}/sub_01.fit")[..., :4500], fits.getdata(copy)))
check("B: CRPIX/CRVAL unchanged, SIP within tolerance, T0 keys present, single matrix form", listing.get(k1, {}).get("ok") is True, str([k for k, v in listing.get(k1, {}).get("checks", {}).items() if not v]))
l1 = listing.get(k1, {}); c1 = l1.get("checks", {})
check("B: Siril's 15-digit SIP re-serialization EXERCISED (max_rel_sip > 0) and PASSES both assertions", (l1.get("max_rel_sip") or 0) > 0 and c1.get("SIP keys/orders identical, values within 1e-12 rel") is True and c1.get("pixel->world agreement < 1e-9 deg") is True, f"max_rel_sip {l1.get('max_rel_sip')} max_sky_sep_deg {l1.get('max_sky_sep_deg')}")
check("B: flat member untouched -> symlink, no MEMC* keys", (not r2["cropped"]) and os.path.islink(os.path.join(cur, k2)) and listing.get(k2, {}).get("ok") is True)
check("B: SYMMETRIC rise on both sides (the refuted intrinsic form) -> NOT cropped", (not r3["cropped"]) and os.path.islink(os.path.join(cur, k3)), f"asym {r3['asymmetry']}")
check("B: advisory S_i reported for every member, never gating", all(v["S_advisory"] is not None for v in tab.values()) and rec["advisory_S"]["p25"] is not None, f"S {[v['S_advisory'] for v in tab.values()]}")
check("B: record verified, 1 cropped / 2 untouched", rec["verified"] is True and rec["cropped"] == 1 and rec["untouched"] == 2)
sys.exit(0 if ok else 1)
PY
  # C. the same reference, allowed -> runs, cropped, said aloud
  "$0" --members-dir="$D" --out="$T/curC" --bar=0.20 --recipe="$RC" --profiles="$P" --ref="$D/sub_01.fit" --allow-ref-crop --record="$T/recC.json" --tag=selftestC >"$T/C.log" 2>&1; rc=$?
  check "C: --allow-ref-crop lifts the refusal, the crop is said aloud" "$([ $rc -eq 0 ] && grep -q 'WARNING: the pinned reference' "$T/C.log" && python3 -c "import json,sys; r=json.load(open('$T/recC.json')); sys.exit(0 if any(v.get('reference_cropped_allowed') for v in r['table'].values()) else 1)" && echo 1 || echo 0)" "rc=$rc"
  # D. THE CACHE PATH: no --profiles; the seeded cache (real sha256s + matching
  # geometry) serves all three members — 0 profiled, the cache file byte-identical,
  # verdicts equal to case B's.
  local CSHA; CSHA=$(sha256sum "$CJ" | awk '{print $1}')
  "$0" --members-dir="$D" --out="$T/curD" --bar=0.20 --recipe="$RC" --cache="$CJ" --ref="$D/sub_02.fit" --record="$T/recD.json" --tag=selftestD >"$T/D.log" 2>&1; rc=$?
  check "D: cache-served run exits 0" "$([ $rc -eq 0 ] && echo 1 || echo 0)" "rc=$rc $(tail -1 "$T/D.log")"
  check "D: 0 profiled, 3 cached (no findstar run)" "$(grep -q '0 profiled' "$T/D.log" && grep -q '3 cached' "$T/D.log" && echo 1 || echo 0)"
  check "D: an all-hit run leaves the cache byte-identical" "$([ "$(sha256sum "$CJ" | awk '{print $1}')" = "$CSHA" ] && echo 1 || echo 0)"
  python3 - "$T" <<'PY' || fails=$((fails+1))
import json, sys
T = sys.argv[1]
b = json.load(open(f"{T}/recB.json"))["table"]; d = json.load(open(f"{T}/recD.json"))["table"]
same = set(b) == set(d) and all(b[k]["onset"] == d[k]["onset"] and b[k]["x_c"] == d[k]["x_c"] and b[k]["cropped"] == d[k]["cropped"] for k in b)
print(f"  {'PASS' if same else 'FAIL'}  D: cache-served verdicts identical to case B (onset/x_c/cropped per member)")
sys.exit(0 if same else 1)
PY
  # E. NEGATIVE control for the SIP criterion: a scratch copy of case B's cropped member
  # with ONE coefficient altered by 1e-6 RELATIVE (astropy header write — the change a
  # re-solve or a wrong crop would make) MUST FAIL both assertions and exit verify 2.
  python3 - "$T" "$PROF" <<'PY' || fails=$((fails+1))
import json, os, shutil, subprocess, sys
from astropy.io import fits
T, PROF = sys.argv[1], sys.argv[2]
plan = json.load(open(f"{T}/curB/.stage/plan.json"))
crop = [a for a in plan["actions"] if a["action"] == "crop"]
neg = f"{T}/neg"; os.makedirs(neg, exist_ok=True)
for a in crop:
    shutil.copy2(os.path.join(plan["curated"], a["name"]), os.path.join(neg, a["name"]))
    with fits.open(os.path.join(neg, a["name"]), mode="update") as hd:
        hd[0].header["A_2_0"] = float(hd[0].header["A_2_0"]) * (1 + 1e-6)
json.dump({**plan, "curated": neg, "actions": crop}, open(f"{T}/neg_plan.json", "w"))
shutil.copy2(f"{T}/recB.json", f"{T}/recE.json")
rc = subprocess.run([sys.executable, PROF, "verify", f"--plan={T}/neg_plan.json", f"--record={T}/recE.json"], capture_output=True, text=True).returncode
r = json.load(open(f"{T}/recE.json")); l = [v for v in r["curated_listing"].values() if "checks" in v][0]; c = l["checks"]
ok = rc == 2 and c["SIP keys/orders identical, values within 1e-12 rel"] is False and c["pixel->world agreement < 1e-9 deg"] is False
print(f"  {'PASS' if ok else 'FAIL'}  E: NEGATIVE — one coefficient altered by 1e-6 relative FAILS both SIP assertions, verify exit 2 rc={rc} max_rel_sip {l['max_rel_sip']:.2e} max_sky_sep_deg {l['max_sky_sep_deg']:.2e}")
sys.exit(0 if ok else 1)
PY
  echo "run_member_crop --selftest: $([ $fails -eq 0 ] && echo PASS || echo "$fails FAILED")  (scratch: $T)"
  return $fails
}
if [ -n "${SELFTEST:-}" ]; then selftest; exit $?; fi

[ -n "$OUT" ] || { sed -n '6,10p' "$0" >&2; exit 1; }
if [ -n "$MDIR" ]; then DIRS=("$(cd "$MDIR" && pwd)")
else
  [ ${#SESSIONS[@]} -ge 1 ] || { sed -n '6,10p' "$0" >&2; exit 1; }
  DIRS=(); while IFS= read -r gd; do [ -n "$gd" ] && DIRS+=("$gd"); done < <(canonical_member_dirs "${SESSIONS[@]}") || exit 1
  [ ${#DIRS[@]} -ge 1 ] || { echo "no canonical member dir under: ${SESSIONS[*]}" >&2; exit 1; }
fi
# THE CONSTANTS — the recipe is their single source: all five load and are echoed;
# --bar/--half-width override aloud. A missing key is a hard stop naming it.
read -r RBAR RHW RSTATIONS RRADIUS RTOP < <(python3 - "$RECIPE" <<'PY'
import json, sys
p = sys.argv[1]
try:
    r = json.load(open(p))["member_selection"]["portion_rule"]
except Exception as e:
    sys.exit(f"cannot read member_selection.portion_rule from {p}: {e}")
for k in ("bar_px", "half_width_px", "stations_px", "radius_px", "top_n"):
    if k not in r:
        sys.exit(f"{p}: member_selection.portion_rule.{k} missing — the recipe is the constants' single source")
print(r["bar_px"], int(r["half_width_px"]), ",".join(str(int(x)) for x in r["stations_px"]), int(r["radius_px"]), int(r["top_n"]))
PY
) || { echo "[member_crop] recipe read FAILED ($RECIPE)" >&2; exit 1; }
[ -n "$BAR" ] && echo "[member_crop] bar ${BAR} px (--bar overrides the recipe's ${RBAR})" || BAR=$RBAR
[ -n "$HW" ] && echo "[member_crop] half-width ${HW} px (--half-width overrides the recipe's ${RHW})" || HW=$RHW
echo "[member_crop] rule constants: bar ${BAR} px, half-width ${HW} px, stations ${RSTATIONS} px, radius ${RRADIUS} px, top ${RTOP} (recipe $RECIPE)"
TAG=${TAG:-$(basename "$OUT")}
RECORD=${RECORD:-$REPO/datasets/corpus/member_selection/$TAG.json}; mkdir -p "$(dirname "$RECORD")"
mkdir -p "$OUT"; OUT=$(cd "$OUT" && pwd); W="$OUT/.stage"; mkdir -p "$W"
: > "$W/members.txt"
for d in "${DIRS[@]}"; do for s in "$d"/sub_*.fit; do readlink -f "$s" >> "$W/members.txt"; done; done
N=$(wc -l < "$W/members.txt"); echo "[member_crop] $N members from ${#DIRS[@]} dir(s) -> $OUT (record $RECORD)"

# ---- profile (Siril through the tracked cache) unless a table is given
if [ -n "$PROFILES" ]; then PROFILES=$(readlink -f "$PROFILES"); echo "[member_crop] profiles from $PROFILES (no Siril profiling, no cache)"
else
  PROFILES="$W/profiles.json"
  readarray -t MLIST < "$W/members.txt"
  python3 "$PROF" profile "${MLIST[@]}" --out="$PROFILES" --work="$W/profiles" \
    --stations="$RSTATIONS" --radius="$RRADIUS" --top="$RTOP" --cache="$CACHE" \
    || { echo "[member_crop] profiling FAILED" >&2; exit 1; }
fi
# ---- the rule -> plan + record (exit 3 = the pinned reference would be cropped)
python3 "$PROF" plan --profiles="$PROFILES" --members="$W/members.txt" --bar="$BAR" --half-width="$HW" --record="$RECORD" --curated="$OUT" --plan="$W/plan.json" --tag="$TAG" ${REF:+--ref="$REF"} ${ALLOWREF:+--allow-ref-crop}; rc=$?
[ $rc -eq 0 ] || exit $rc
# ---- crop the copies (one Siril script), then the symlinks
python3 - "$W/plan.json" "$OUT" "$BAR" "$RRADIUS" "$RTOP" > "$W/crop.ssf" <<'PY'
import json, sys
plan, out = json.load(open(sys.argv[1])), sys.argv[2]
bar, radius, top = float(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5])
print("requires 1.4.4\nset32bits\nsetcompress 0\nsetext fit")
for a in plan["actions"]:
    if a["action"] != "crop": continue
    print(f"load {a['src']}\ncrop 0 0 {a['kept_width']} {a['H']}\nupdate_key MEMCROP {int(a['x_c'])}\nupdate_key MEMCRULE \"asym>{bar:.2f}px@r{radius} top{top}\"\nupdate_key MEMCSCOR {a['S_advisory']}\nsave {out}/{a['name'][:-4]}")
PY
if grep -q '^crop ' "$W/crop.ssf"; then
  siril_run_logged "$W" "$W/crop.ssf" "$W/siril.log" || { echo "[member_crop] Siril crop FAILED — read $W/siril.log" >&2; exit 1; }
  RECREL=$(python3 -c "import os,sys; print(os.path.relpath(sys.argv[1], sys.argv[2]))" "$RECORD" "$REPO")
  python3 - "$W/plan.json" <<'PY' | while read -r name; do header_apply_keys "$OUT/$name" "update_key MEMCPROV \"$RECREL\""; done
import json, sys
for a in json.load(open(sys.argv[1]))["actions"]:
    if a["action"] == "crop": print(a["name"])
PY
fi
python3 - "$W/plan.json" "$OUT" <<'PY'
import json, os, sys
plan, out = json.load(open(sys.argv[1])), sys.argv[2]
for a in plan["actions"]:
    dst = os.path.join(out, a["name"])
    if a["action"] == "symlink":
        if os.path.lexists(dst): os.remove(dst)
        os.symlink(a["src"], dst)
PY
# ---- verify every entry; the record carries the verdict
python3 "$PROF" verify --plan="$W/plan.json" --record="$RECORD"; rc=$?
NC=$(python3 -c "import json,sys; r=json.load(open(sys.argv[1])); print(f\"{r['cropped']} cropped ({r['x_c_histogram']}), {r['untouched']} untouched\")" "$RECORD")
echo "[member_crop] DONE: $NC; curated dir $OUT; record $RECORD; verified=$([ $rc -eq 0 ] && echo true || echo FALSE)"
exit $rc
