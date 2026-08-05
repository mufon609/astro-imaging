#!/usr/bin/env bash
# PRE-RELEASE / CI GUARD, two parts:
#   1-4. the chain is 32-bit float END TO END — no generated or templated .ssf
#        may pin `set16bits`, and every product builder must EMIT the pins.
#   4b-c. NOTHING is compressed and nothing is lossy — EVERY .ssf emitter pins
#        `setcompress 0` (discovered, not listed), and no script writes a JPEG.
#   5.   the web session model builds and serializes for every staged session.
# (The name still says bitdepth because that is where callers already invoke it;
# part 5 lives here so it actually runs. Split the file if it grows a third job.)
#
# WHY THIS GUARD EXISTS. 16-bit intermediates were a RAM/disk adaptation for a
# tight rig. Its removal condition fired when the chain moved to a machine with
# headroom, and the retirement was applied to the wide-field light path — but
# the CALIBRATION-MASTER templates (dark/bias/flat) and the standard chain's
# light template were missed, so the repo went on silently emitting 16-bit
# masters for an otherwise-float32 chain. It survived undetected because one
# session worked around it with a SESSION-LOCAL builder pinning set32bits whose
# own comment claimed it was "identical to" the repo template it contradicted.
# A guard, not a comment, is what makes that impossible to repeat.
#
# WHAT IT COSTS, measured, so the rule is not doctrine:
# - A master dark is a many-frame MEAN, so its precision is far finer than one
#   integer step. Rounding to 16 bits stores a SENSOR-FIXED quantization
#   pattern that is then subtracted identically into every light — the input to
#   walking noise, which no rejection or cosmetic correction removes. On a
#   200-frame master: quantization 0.2889 ADU RMS (uniform +-0.5, matching
#   1/sqrt(12) = 0.2887 to four figures) against a statistical floor of 0.4213
#   ADU (split-half measured), inflating the fixed-pattern residual
#   0.4213 -> 0.5109 ADU, i.e. +21%.
# - On the LIGHT path, integer round-tripping through calibrate/warp/register
#   kept only ~55-70% of the 32-bit arm's extended faint contrast (NAN-region
#   contrast 4.8/2.4/3.9 vs 8.5/2.9/5.6 % of local sky, R/G/B) — lost
#   structure, not merely added noise.
#
# If a future rig genuinely cannot afford 32-bit, that is a new adaptation and
# needs its own written removal condition in BACKLOG.md — not a silent edit.
#
# WHAT THIS GUARD DOES AND DOES NOT PROVE. It is a STATIC, per-FILE check over
# the whole scripts/ tree. It proves no product builder is missing the pin
# entirely. It does NOT prove that every individual generated .ssf inside a
# multi-.ssf builder carries it — a builder that already pins set32bits in one
# emission passes even if a newly added emission omits it. Per-emission-block
# granularity needs real parsing of the printf/heredoc blocks; it is BACKLOG.
# Two earlier holes are closed: the search root was `dirname $0` = scripts/stack,
# so FIVE live `set16bits` pins under scripts/qa and scripts/darktable were
# invisible to a check whose message claimed "no set16bits anywhere"; and the
# product-builder list named 2 of the 9 scripts that write image products, so
# spcc_run.py — which writes stack_<set>_spcc.fit, the render tier's own input —
# was unpinned and unchecked.
set -euo pipefail
cd "$(dirname "$0")/../.."          # repo root: the whole tree, not one stage dir
fail() { echo "FAIL: $*" >&2; exit 1; }
S=scripts

# 1. no script may pin set16bits, except these THREE, each for a stated reason
#    that makes 32-bit buy nothing. Anything else is a FAIL. An exemption is a
#    claim about where the leg TERMINATES, so re-check it if that changes.
#    - qa/coverage_probe.sh: the coverage MAP instrument. Its members are
#      `fill 1000` constant twins and the map is an integer count x 1000, which
#      16 bits holds exactly; it switches to set32bits before the sum stack. Not
#      a deliverable, and float would not make an integer count more exact.
#    - qa/run_frame_qa.sh: analysis-only `register -2pass` pass. It saves no
#      product — only the tool's regdata is kept — and the inputs are 14-bit
#      raws, which 16 bits holds exactly.
#    - darktable/fit_lens_model.sh: its calibrate leg terminates in `savetif8`
#      for Hugin's feature matcher, so the leg's precision is capped at 8 bits
#      downstream regardless. (The FITTED model does shape products, but through
#      star CORRESPONDENCE geometry, whose precision is SNR-limited, not
#      quantization-limited.)
EXEMPT='qa/coverage_probe\.sh|qa/run_frame_qa\.sh|darktable/fit_lens_model\.sh'
hits=$(grep -rn 'set16bits' --include='*.ssf' --include='*.tmpl' --include='*.sh' \
        --include='*.py' "$S" | grep -vE "check_bitdepth\.sh:|$EXEMPT" || true)
[ -z "$hits" ] || { echo "$hits" >&2; fail "set16bits is pinned above (not an exempt instrument)"; }

# 2. every master-building template must pin set32bits explicitly. Siril
#    PERSISTS the bit-depth setting across runs, so an unpinned script inherits
#    whatever ran last — the same non-determinism setcompress 0 is pinned for.
for t in $S/stack/siril/master_dark.ssf $S/stack/siril/master_bias.ssf \
         $S/stack/siril/master_flat.ssf $S/stack/siril/lights.ssf.tmpl; do
  grep -q '^set32bits' "$t" || fail "$t does not pin set32bits"
  grep -q '^setcompress 0' "$t" || fail "$t does not pin setcompress 0"
done

# 3+4. EVERY script that generates an .ssf which WRITES an image product must pin
#    set32bits AND setcompress 0. This list was verified by reading what each
#    script emits, not by grepping for the word "stack" (which also appears in
#    every stack_*.fit path and in prose, and produced a false inventory).
#    COMMENT LINES ARE STRIPPED FIRST. Searching the raw file matches a pin that
#    only exists in prose — caught by mutation-testing this very guard: deleting
#    the real `"set32bits\n"` emission from spcc_run.py left the word in the
#    comment ABOVE it and the check still passed. That is the registry's own
#    lesson ("a corrected comment fails silently, a guard fails loudly") turned
#    on the guard itself, so it is asserted here rather than trusted.
#    ONE awk process, deliberately not `grep -v ... | grep -q`: under the
#    `set -o pipefail` this script runs with, `grep -q` exits as soon as it
#    matches, the upstream grep takes SIGPIPE (141), and the pipeline reports
#    FAILURE for a file that PASSES — nondeterministically, depending on how
#    early the match lands. That made this guard report a false FAIL on
#    render_tier.sh on one run and pass on the next.
emits() {   # emits <file> <needle> — needle present on a non-comment line
  awk -v n="$2" '!/^[[:space:]]*#/ && index($0, n) { found = 1 } END { exit !found }' "$1"
}
for b in stack/run_pipeline.sh stack/run_undistort_pipeline.sh \
         stack/run_undistort_groups.sh stack/run_undistort_compose.sh \
         stack/build_sky_flat.sh stack/compose.py stack/render_tier.sh \
         stack/finish_render.sh calibrate/spcc_run.py; do
  emits "$S/$b" 'set32bits'   || fail "$S/$b writes an image product but never EMITS set32bits (a mention in a comment does not count)"
  emits "$S/$b" 'setcompress 0' || fail "$S/$b does not EMIT setcompress 0"
done

# 4b. EVERY .ssf emitter must pin setcompress 0 — not just the product builders
#    of 3+4. The hand-maintained list above is scoped to scripts that write an
#    image PRODUCT, which left the QA instruments unchecked, and four of them
#    were emitting unpinned .ssf: star_stations.py (x2), star_shape.py and
#    anomaly_audit.py. The last one matters most — `extract_Green` WRITES a FITS,
#    so with compression left on by a previous run that leg emits Green_*.fit.fz.
#    Its cleanup already globbed `.fit*` to sweep up the .fz, i.e. the code was
#    working around the symptom rather than pinning the cause. `setcompress` is a
#    PERSISTED siril preference (config.1.4.ini `[compression] enabled=`), so an
#    unpinned script is not merely untidy: it inherits whatever ran last, and
#    "no compression anywhere in the pipeline" is a foundational rule (CLAUDE.md).
#    DISCOVERY, not a curated list: every file with `.ssf` on a non-comment line
#    must emit the pin, so a NEW instrument is covered the day it is written.
#    Three files name an .ssf without generating one — each exemption is a claim
#    about that file, so re-check it if the file changes:
#    - stack/build_master_dark.sh: RUNS the pinned template siril/master_dark.ssf
#      (asserted by check 2 above) and generates nothing itself.
#    - qa/baseline_guard.py: delegates every siril call to qa/regional_stat.py,
#      which pins; the word appears only in its docstring.
#    - setup/x86_bootstrap.sh: prose + a probe label, no .ssf generated.
SSF_NOT_EMITTERS='stack/build_master_dark\.sh|qa/baseline_guard\.py|setup/x86_bootstrap\.sh'
for f in $(grep -rl '\.ssf' --include='*.sh' --include='*.py' --include='*.ssf' \
             --include='*.tmpl' "$S" web | sort); do
  case "$f" in *check_bitdepth.sh) continue;; esac
  echo "$f" | grep -qE "$SSF_NOT_EMITTERS" && continue
  awk '!/^[[:space:]]*#/ && index($0, ".ssf")' "$f" | grep -q . || continue
  emits "$f" 'setcompress 0' \
    || fail "$f generates an .ssf but never EMITS setcompress 0 — siril PERSISTS the setting, so this run inherits whatever ran last"
done

# 4c. NOTHING in the pipeline writes a lossy image. Project policy is 16-bit PNG
#    only — no JPEG, no PNG8 (CLAUDE.md, README review contract). qa/diag_flat.ssf
#    shipped `savejpg flatmaster_check 85`: a q85 JPEG of a calibration master,
#    written by a diagnostic nobody re-read. `savetif8` is NOT banned here — the
#    one use (darktable/fit_lens_model.sh) feeds Hugin's feature matcher, whose
#    leg is 8-bit-capped downstream anyway and is exempted in check 1 for the
#    same reason.
hits=$(grep -rn 'savejpg' --include='*.ssf' --include='*.tmpl' --include='*.sh' \
        --include='*.py' "$S" web | grep -v "check_bitdepth\.sh:" || true)
[ -z "$hits" ] || { echo "$hits" >&2; fail "savejpg writes a LOSSY image (project policy: 16-bit PNG only)"; }

# 5. WEB SESSION SMOKE TEST. `/api/session/<name>` returned 500 for an entire
#    branch because one tracked record was a JSON ARRAY and the model called
#    .get() on it — taking out every page for that session (frames, culled,
#    surfaces, sky objects, experiments, framing, records). Nothing exercised the
#    API, so it stayed dark. This builds the model IN-PROCESS for every staged
#    session and serializes it. In-process on purpose: it needs no port, no sleep
#    and no running server, so it cannot flake and cannot be quietly skipped, and
#    it exercises the exact function that broke. json.dumps is part of the
#    assertion because a non-serializable value fails the endpoint just as hard
#    as an exception does.
python3 - <<'PYSMOKE' || fail "the web session model does not build for every staged session"
import json, os, sys
sys.path.insert(0, "web")
import serve

names = [n for n in sorted(os.listdir("datasets"))
         if os.path.isdir(os.path.join("datasets", n))]
if not names:
    sys.exit("no staged sessions under datasets/ — the smoke test asserted nothing")

bad = []
for n in names:
    try:
        m = serve.session_model(n)
        if m is None:
            bad.append((n, "session_model returned None")); continue
        json.dumps(m)
        print(f"  [web] {n}: model builds + serializes ({len(m['sets'])} sets, "
              f"{len(m['surfaces'])} surfaces, {len(m['renders'])} renders, "
              f"{len(m['session_records'])} session records)")
    except Exception as e:
        bad.append((n, f"{type(e).__name__}: {e}"))

# the stage registry must load and every entry be well formed — otherwise a
# broken build lambda is discovered only when a user clicks it
try:
    for name, spec in sorted(serve.STAGES.items()):
        for k in ("desc", "phase", "params", "build"):
            if k not in spec:
                bad.append((f"stage:{name}", f"missing {k}"))
        if not callable(spec.get("build")):
            bad.append((f"stage:{name}", "build is not callable"))
    print(f"  [web] stage registry: {len(serve.STAGES)} stages, all well formed")
except Exception as e:
    bad.append(("stages", f"{type(e).__name__}: {e}"))

for n, why in bad:
    print(f"  [web] FAIL {n}: {why}", file=sys.stderr)
sys.exit(1 if bad else 0)
PYSMOKE

cat <<EOF
OK: no set16bits outside the 3 documented instrument exemptions;
    4 master templates pin set32bits + setcompress 0;
    9 product builders pin set32bits + setcompress 0;
    every discovered .ssf emitter pins setcompress 0; no savejpg anywhere.
    Scope: per-FILE and static — it does not prove every individual generated
    .ssf inside a multi-.ssf builder carries the pin (BACKLOG).
    Web: every staged session's model builds + serializes; stage registry sane.
EOF
