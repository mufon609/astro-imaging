#!/usr/bin/env python3
"""ONE readiness surface for a set: every ratified criterion, evaluated up
front, colored GREEN/YELLOW/RED — so a run takes ONE approval and then runs
unattended, and anything undecidable is RED here instead of a stop discovered
hours into a build.

Usage:
  readiness_report.py <session-dir> <set> [--route=R] [--forced-route=F]
                      [--json-only] [--no-write]

The colour contract (user-ratified; PENDING added by ratified amendment):
  GREEN   — go. The criterion is met FROM THE DATA; the value and the
            instrument are stated, not just the tick.
  YELLOW  — met, but the user should SEE it (a derived mount, a thin dwell
            headroom, the sky-flat route's open defect). Never blocks.
  RED     — bad or missing. The only thing that stops a run, and it stops
            HERE. Exit 3.
  PENDING — not yet measured, and the RUN ITSELF produces it: the measure
            phase writes exactly these records before the chain ever calls
            this evaluator, so a pre-run absence is not a blocker and must
            not read as one. Derived from record absence, never asserted by
            the caller. The chain passes --post-measure (absence after the
            measure phase IS wrong and stays RED), so its own invocation can
            never see PENDING. Exit stays 0.

One evaluator feeds three surfaces: this CLI, run_set_chain.sh (which runs it
after the measure phase and takes the single approval), and the web set page
(GET /api/readiness — same data, same colours). The report is a RECORD,
written beside the other per-set records (datasets/<session>/<set>/
readiness.json, only when its content changes), so what was approved is
auditable afterwards.

Decision logic over tool outputs and tracked records ONLY — no pixel is read,
no measurement is made here; every number below is quoted from the record the
named instrument wrote. The single-pass-vs-groups fork is NOT a question here:
groups is the standing route and rides the route criterion (force_route() in
run_set_chain.sh; the run_undistort_groups.sh removal-register row).
"""
import argparse
import glob
import json
import math
import os
import re
import shutil
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RAW_EXT = (".nef", ".dng", ".cr2", ".cr3", ".arw", ".raf", ".fit", ".fits")

GREEN, YELLOW, RED, PENDING = "GREEN", "YELLOW", "RED", "PENDING"
# overall = worst row; PENDING outranks YELLOW (an unmeasured set's headline
# is "the run measures this", not a met-but-look), RED outranks everything
_RANK = {GREEN: 0, YELLOW: 1, PENDING: 2, RED: 3}


def _read(path):
    try:
        return json.load(open(path))
    except (OSError, ValueError):
        return None


def _frames(session, set_name):
    d = os.path.join(session, set_name)
    return sorted(f for f in glob.glob(os.path.join(d, "*"))
                  if os.path.splitext(f)[1].lower() in RAW_EXT)


def _gesd_fraction():
    """Read GESD's outlier fraction from stack_rejection.sh — the same single
    source the groups builder reads; never a re-written constant."""
    try:
        txt = open(os.path.join(REPO, "scripts", "stack",
                                "stack_rejection.sh")).read()
        m = re.search(r"rej g ([0-9.]+)", txt)
        if m:
            return float(m.group(1))
    except OSError:
        pass
    return 0.3


def _derived_group(n):
    """Same derivation as run_undistort_groups.sh (keep in sync): target
    ~100/group via K_TARGET = N//100 (min 2), group = ceil(N/K)."""
    k = max(2, n // 100)
    return math.ceil(n / k) if n else None


def _singlepass_peak_gib(session, set_name, nframes):
    r = subprocess.run(
        ["bash", "-c",
         'source "$1/scripts/stack/disk_budget.sh"; undistort_peak_gib "$2" "$3" "$4"',
         "_", REPO, session, set_name, str(nframes)],
        capture_output=True, text=True)
    try:
        return int(r.stdout.strip())
    except ValueError:
        return None


def _spcc_env():
    db = os.path.expanduser("~/.var/app/org.siril.Siril/data/siril-spcc-database")
    chunks = os.path.expanduser("~/.local/share/siril/siril_catalogues/spcc")
    db_ok = os.path.isdir(db) and bool(os.listdir(db))
    chunks_ok = os.path.isdir(chunks) and bool(os.listdir(chunks))
    cfg_ok = None   # None = could not verify (YELLOW note, never a guess)
    for cfg in glob.glob(os.path.expanduser(
            "~/.var/app/org.siril.Siril/config/siril/*")):
        try:
            txt = open(cfg, errors="ignore").read()
        except OSError:
            continue
        if "catalogue_gaia_photo" in txt:
            m = re.search(r"catalogue_gaia_photo\s*=\s*(.+)", txt)
            cfg_ok = bool(m and "siril_catalogues/spcc" in m.group(1))
            break
    return db_ok, chunks_ok, cfg_ok


def _row(name, status, value, instrument, detail=""):
    return {"criterion": name, "status": status, "value": value,
            "instrument": instrument, "detail": detail}


def evaluate(session, set_name, route=None, forced_route=None,
             post_measure=False):
    session = os.path.abspath(session)
    sname = os.path.basename(os.path.normpath(session))
    droot = os.path.join(REPO, "datasets", sname, set_name)
    acq = _read(os.path.join(droot, "acquisition.json")) or {}
    fp = _read(os.path.join(droot, "fingerprint.json")) or {}
    qa = _read(os.path.join(droot, "qa_work", "frame_metrics.json"))
    aud = _read(os.path.join(droot, "audit_work", "anomaly_audit.json"))
    recipe = _read(os.path.join(droot, "recipe.json")) or {}
    lp = _read(os.path.join(droot, "qa_work", "lens_preflight.json"))
    flatqa = _read(os.path.join(droot, "qa_work",
                                f"skyflat_{set_name}_qa.json"))
    baseline = os.path.exists(os.path.join(droot, "baseline.json"))
    frames = _frames(session, set_name)
    excl = (recipe.get("stack") or {}).get("exclude") or []
    n_stack = max(0, len(frames) - len(excl))
    rows = []
    # what an absent measure-phase record means depends on WHEN we are asked:
    # after the measure phase (the chain) absence is genuinely wrong — RED;
    # before any run (web rail, ad-hoc CLI) the run itself produces it — PENDING
    miss = RED if post_measure else PENDING

    # -- mount ---------------------------------------------------------------
    mount, msrc = acq.get("mount"), acq.get("mount_source")
    mc = fp.get("mount_check") or {}
    verdict, method = mc.get("verdict"), mc.get("method")
    if mount and verdict == "CONTRADICT":
        rows.append(_row("mount", RED, f"{mount} ({msrc}) vs measured "
                         f"{mc.get('measured')}", method or "fingerprint",
                         mc.get("reason", "")))
    elif mount and verdict == "CONFIRM":
        rows.append(_row("mount", GREEN, f"{mount} ({msrc})",
                         method or "fingerprint", mc.get("reason", "")))
    elif mount:
        rows.append(_row("mount", YELLOW, f"{mount} ({msrc}) — unchecked",
                         method or "no decisive instrument yet",
                         mc.get("reason", "")))
    elif mc.get("method"):
        # the instruments RAN and produced a cross-check that could not decide
        # (disagreement nulls `measured`) — that genuinely stops, exit 4
        rows.append(_row("mount", RED, "instruments could not decide",
                         mc.get("method"), mc.get("reason", "")))
    else:
        rows.append(_row("mount", miss, "not measured yet",
                         "fingerprint (drift probe / trail-vs-roundness)",
                         "the run's measure phase derives it — a decisive "
                         "signature adopts as mount_source=derived"))

    # -- route ---------------------------------------------------------------
    fov = (acq.get("exif") or {}).get("fov_deg") or 0
    derived = route
    if derived in (None, "", "stop-undeclared", "derive-after-preflight",
                   "stop-unroutable"):
        derived = ("standard" if mount == "tracked" else
                   "undistort-groups" if (mount == "fixed" and fov >= 10)
                   else None)
    mount_pending = not mount and not mc.get("method")
    if derived is None and mount_pending and not post_measure:
        rows.append(_row("route", PENDING, "derives once the mount is measured",
                         "fingerprint (mount x field width)", ""))
    elif derived is None:
        rows.append(_row("route", RED, "unroutable",
                         "fingerprint (mount x field width)",
                         f"mount '{mount}', fov '{fov}' — neither tracked nor "
                         "fixed+wide; the user picks"))
    elif forced_route:
        rows.append(_row("route", YELLOW, f"{derived} (OPERATOR-FORCED "
                         f"--route={forced_route})", "operator override",
                         "the derived route is stated in the chain plan"))
    else:
        why = ("tracked: no inter-frame drift" if derived == "standard" else
               f"fixed + {fov} deg field; groups is the standing route "
               "(sub-stacks keep the cross-set combine buildable)")
        rows.append(_row("route", GREEN, derived,
                         "fingerprint (mount x field width)", why))

    # -- frame QA + cull -----------------------------------------------------
    if qa is None:
        rows.append(_row("frame_qa", miss, "not measured yet",
                         "Siril register regdata (run_frame_qa.sh)",
                         "the run's measure phase runs it before the report"))
    else:
        flags = qa.get("flagged_defect_side_z") or []
        block = recipe.get("stack")
        if block and flags:
            auto = str(block.get("why", "")).startswith("auto-cull")
            rows.append(_row("frame_qa",
                             YELLOW if auto else GREEN,
                             f"{len(flags)} flag(s); {len(excl)} excluded "
                             f"({'standing auto-cull' if auto else 'hand-ratified'})",
                             "Siril register regdata; robust z >= 3.5",
                             block.get("why", "")[:200]))
        elif flags:
            rows.append(_row("frame_qa", YELLOW,
                             f"{len(flags)} flag(s) — standing auto-cull will "
                             "exclude them", "Siril register regdata", ""))
        else:
            rows.append(_row("frame_qa", GREEN,
                             f"0 defect flags over {qa.get('frames_total')} frames",
                             "Siril register regdata", ""))

    # -- obstruction audit + dwell floor -------------------------------------
    if aud is None:
        rows.append(_row("obstruction_audit", miss, "not measured yet",
                         "anomaly_audit.py (Siril-measured)",
                         "the run's measure phase runs it before the report"))
    else:
        objs = aud.get("unique_objects") or []
        unknown = sum(1 for o in objs
                      if o.get("cls") not in ("aircraft", "satellite"))
        dwell = max((o.get("n") or 0) for o in objs) if objs else 0
        frac = _gesd_fraction()
        floor = math.ceil(dwell / frac) if dwell else 0
        detail = f"{len(objs)} object(s), longest dwell {dwell} frame(s)"
        if derived == "undistort-groups" and n_stack:
            group = max(_derived_group(n_stack) or 0, floor)
            if floor and floor > n_stack // 2:
                rows.append(_row("obstruction_audit", RED,
                                 f"dwell floor {floor} exceeds any 2-group "
                                 f"split of {n_stack} frames",
                                 "anomaly_audit + GESD fraction "
                                 f"{frac} (stack_rejection.sh)", detail))
            else:
                headroom = (100 * (1 - floor / group)) if group else 100
                status = (YELLOW if (unknown or headroom < 20) else GREEN)
                note = (f"; {unknown} UNKNOWN — human eyes" if unknown else "")
                rows.append(_row("obstruction_audit", status,
                                 f"floor {floor} vs group {group} "
                                 f"({headroom:.0f}% headroom){note}",
                                 "anomaly_audit + GESD fraction "
                                 f"{frac} (stack_rejection.sh)", detail))
        elif derived in ("undistort", "standard") and n_stack > 50 and floor:
            # single-pass GESD regime (>50 subs, stack_rejection.sh): the whole
            # set is one group, so the same fraction cap binds — a dweller at or
            # past frac of n_stack is not eligible for rejection AT ALL. Without
            # this branch a forced --route=single silently skipped the check the
            # groups branch enforces (23/135 = 17% passed here by luck).
            if floor > n_stack:
                rows.append(_row("obstruction_audit", RED,
                                 f"dwell floor {floor} exceeds the whole set "
                                 f"({n_stack} frames): the {dwell}-frame "
                                 "transient is past the GESD outlier-fraction "
                                 "cap and cannot reject — cull its frames",
                                 "anomaly_audit + GESD fraction "
                                 f"{frac} (stack_rejection.sh)", detail))
            else:
                headroom = 100 * (1 - floor / n_stack)
                status = (YELLOW if (unknown or headroom < 20) else GREEN)
                note = (f"; {unknown} UNKNOWN — human eyes" if unknown else "")
                rows.append(_row("obstruction_audit", status,
                                 f"floor {floor} vs single-pass set {n_stack} "
                                 f"({headroom:.0f}% headroom){note}",
                                 "anomaly_audit + GESD fraction "
                                 f"{frac} (stack_rejection.sh)", detail))
        else:
            rows.append(_row("obstruction_audit",
                             YELLOW if unknown else GREEN,
                             detail + (f"; {unknown} UNKNOWN — human eyes"
                                       if unknown else "; all classified"),
                             "anomaly_audit.py (Siril-measured)", ""))

    # -- optics --------------------------------------------------------------
    if derived == "standard":
        rows.append(_row("optics", GREEN, "n/a — standard route (no lens warp)",
                         "route", ""))
    elif derived is None and not post_measure:
        rows.append(_row("optics", PENDING, "awaits the route",
                         "lens_preflight.py --require-profile",
                         "runs in the measure phase once the route is known"))
    elif lp is None:
        rows.append(_row("optics", miss, "preflight not run",
                         "lens_preflight.py --require-profile",
                         "the run's measure phase runs it before the report"))
    else:
        spread = lp.get("spread") or {}
        mixed = any(len(v) > 1 for v in spread.values())
        proof = (lp.get("profile_proof") or {}).get("corrected")
        pinned = (lp.get("pinned_model") or {}).get("state")
        if mixed or proof is False or pinned not in (None, "ok", "candidate"):
            rows.append(_row("optics", RED,
                             ("MIXED optics" if mixed else
                              "warp not proven" if proof is False else
                              f"pinned model: {pinned}"),
                             "lens_preflight.py (exiftool + darktable render "
                             "diff via Siril stat)", ""))
        elif pinned == "candidate":
            # the --from-fit A/B state: installed == the set's OWN recorded
            # fit, deliberately not the pinned incumbent — met, but SEE it
            rows.append(_row("optics", YELLOW,
                             "uniform; installed == this set's OWN fitted "
                             "model (candidate A/B state, not the pinned "
                             "incumbent); warp proven",
                             "lens_preflight.py (exiftool + darktable render "
                             "diff via Siril stat)", ""))
        elif pinned is None:
            rows.append(_row("optics", YELLOW,
                             "warp proven; pinned-model state not recorded "
                             "(community entry?)", "lens_preflight.py", ""))
        else:
            key = (lp.get("pinned_model") or {}).get("key", "")
            rows.append(_row("optics", GREEN,
                             f"uniform; installed == pinned ({key}); warp proven",
                             "lens_preflight.py (exiftool + darktable render "
                             "diff via Siril stat)", ""))

    # -- masters -------------------------------------------------------------
    dark = os.path.join(session, "work", "masters", "dark_master.fit")
    darks_staged = any(os.path.isdir(os.path.join(session, d))
                       for d in ("darks", "dark"))
    real_flats = (bool(glob.glob(os.path.join(session, "flats*")))
                  or os.path.isdir(os.path.join(session, "calib")))
    if real_flats and derived != "standard":
        rows.append(_row("masters", RED,
                         "real flats staged on the undistort route",
                         "session staging",
                         "master-flat wiring for this route is a documented "
                         "gap — resolve the flat manually (chain exit 6)"))
    elif not (os.path.exists(dark) or darks_staged):
        rows.append(_row("masters", RED, "no darks staged and no master dark",
                         "session staging", "shoot/stage matched darks"))
    else:
        d = ("master dark present" if os.path.exists(dark)
             else "darks staged — master builds this run")
        f = ("real flats staged" if real_flats else
             "flatless: per-set sky flat route (carries the open sky x V "
             "object tilt, 3.11% at 241 sigma — real flats fix it)")
        rows.append(_row("masters", GREEN if real_flats else YELLOW,
                         f"{d}; {f}", "session staging + build_sky_flat.sh", ""))

    # -- flat quality --------------------------------------------------------
    if derived == "standard":
        rows.append(_row("flat_quality", GREEN,
                         "n/a — standard route resolves its own masters",
                         "run_pipeline.sh preflight", ""))
    elif flatqa is None:
        rows.append(_row("flat_quality", GREEN,
                         "builds this run — builder validation gates enforce "
                         "(regional stat, speck count, preview)",
                         "build_sky_flat.sh gates", ""))
    else:
        asym = flatqa.get("corner_asymmetry")
        ratio = asym.get("ratio") if isinstance(asym, dict) else asym
        status = YELLOW if (isinstance(ratio, (int, float)) and ratio > 1.20) \
            else GREEN
        rows.append(_row("flat_quality", status,
                         f"built; corner asymmetry ratio {ratio} "
                         f"(WARN over 1.20)",
                         "build_sky_flat.sh (Siril stat + findstar)",
                         "above-WARN asymmetry is the open sky x V defect, "
                         "stated not hidden" if status == YELLOW else ""))

    # -- disk ----------------------------------------------------------------
    if not os.path.isdir(session):
        # records-only session (raws freed / not yet staged): every other row
        # still reads the tracked records, but nothing can RUN
        rows.append(_row("disk", RED,
                         "session dir absent — raws not staged",
                         "filesystem",
                         "re-stage the session tree to run; the tracked "
                         "records remain the durable state"))
    else:
        free_gb = shutil.disk_usage(session).free // 2**30
        peak = (_singlepass_peak_gib(session, set_name, len(frames))
                if frames else None)
        if peak is None:
            rows.append(_row("disk", YELLOW,
                             f"{free_gb}G free; peak underivable (fresh "
                             "geometry)", "df + disk_budget.sh",
                             "the builders derive and enforce their own "
                             "budgets"))
        else:
            grp = _derived_group(n_stack) or n_stack or 1
            groups_est = max(1, math.ceil(peak * grp / max(1, len(frames))))
            if free_gb >= peak:
                rows.append(_row("disk", GREEN,
                                 f"{free_gb}G free covers even the {peak}G "
                                 "single-pass peak",
                                 "df + disk_budget.sh (undistort_peak_gib)", ""))
            elif free_gb >= groups_est:
                rows.append(_row("disk", YELLOW,
                                 f"{free_gb}G free < single-pass {peak}G but "
                                 f"covers the ~{groups_est}G groups working set",
                                 "df + disk_budget.sh", "groups is the standing "
                                 "route; the builder re-checks before every "
                                 "group"))
            else:
                rows.append(_row("disk", RED,
                                 f"{free_gb}G free is below even the "
                                 f"~{groups_est}G groups working set",
                                 "df + disk_budget.sh",
                                 "free disk or stage less"))

    # -- SPCC ----------------------------------------------------------------
    db_ok, chunks_ok, cfg_ok = _spcc_env()
    sensor = bool(recipe.get("spcc"))
    if not db_ok:
        rows.append(_row("spcc", RED, "siril-spcc-database MISSING",
                         "filesystem check",
                         "without it SPCC SEGFAULTS silently (exit 139) — "
                         "clone gitlab.com/free-astro/siril-spcc-database "
                         "(docs/dead-ends.md)"))
    else:
        bits, status = [], GREEN
        if not chunks_ok:
            bits.append("Gaia xpsamp chunks not staged (spcc_cone --fetch "
                        "resolves)")
            status = YELLOW
        if cfg_ok is False:
            bits.append("catalogue_gaia_photo config points elsewhere — "
                        "siril will range-read online and 429")
            status = YELLOW
        elif cfg_ok is None:
            bits.append("config not verified")
            status = YELLOW
        if not sensor:
            bits.append("sensor-null generic curve (no recipe spcc block)")
            status = YELLOW
        rows.append(_row("spcc", status,
                         "database present" + ("; " + "; ".join(bits) if bits
                                               else "; chunks + config + "
                                               "sensor spec all present"),
                         "filesystem + siril config + recipe.json", ""))

    # -- baseline ------------------------------------------------------------
    rows.append(_row("baseline",
                     GREEN if baseline else YELLOW,
                     ("present — the product is compared after the build "
                      "(exit 8 on mismatch)") if baseline else
                     "none yet — nothing to regress against; the first "
                     "accepted product seeds it",
                     "baseline_guard.py (Siril stat)", ""))

    overall = max((r["status"] for r in rows), key=lambda s: _RANK[s])
    return {"session": sname, "set": set_name, "route": derived,
            "overall": overall, "criteria": rows,
            "generated_by": "scripts/qa/readiness_report.py — decision logic "
                            "over tool outputs and tracked records; no pixel "
                            "read, no measurement made here"}


def _print_report(rep, color=None):
    if color is None:
        color = sys.stdout.isatty()
    paint = {GREEN: "\033[32m", YELLOW: "\033[33m", RED: "\033[31m",
             PENDING: "\033[2m"}
    reset = "\033[0m"

    def c(s):
        return f"{paint[s]}{s:<7}{reset}" if color else f"{s:<7}"
    print(f"READINESS {rep['session']}/{rep['set']} — route: {rep['route']}"
          f" — overall: {c(rep['overall']).strip()}")
    for r in rep["criteria"]:
        print(f"  {c(r['status'])} {r['criterion']:<18} {r['value']}")
        print(f"         {'':<18} [{r['instrument']}]"
              + (f" {r['detail']}" if r["detail"] else ""))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("session")
    ap.add_argument("set")
    ap.add_argument("--route", default=None,
                    help="route context from the chain (else derived here)")
    ap.add_argument("--forced-route", default=None)
    ap.add_argument("--post-measure", action="store_true",
                    help="the caller has run the measure phase: an absent "
                         "measure record is RED, never PENDING (the chain)")
    ap.add_argument("--json-only", action="store_true")
    ap.add_argument("--no-write", action="store_true")
    a = ap.parse_args()
    rep = evaluate(a.session, a.set, route=a.route,
                   forced_route=a.forced_route, post_measure=a.post_measure)
    if not a.no_write:
        droot = os.path.join(REPO, "datasets",
                             os.path.basename(os.path.normpath(a.session)),
                             a.set)
        os.makedirs(droot, exist_ok=True)
        p = os.path.join(droot, "readiness.json")
        if _read(p) != rep:
            json.dump(rep, open(p, "w"), indent=1)
    if a.json_only:
        print(json.dumps(rep, indent=1))
    else:
        _print_report(rep)
    return 3 if rep["overall"] == RED else 0


if __name__ == "__main__":
    sys.exit(main())
