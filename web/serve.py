#!/usr/bin/env python3
"""Local web front end for the workspace — static file server + the framing
record endpoint. LOCAL-ONLY by construction (binds 127.0.0.1; no external
service — BACKLOG item 12's contract).

    python3 web/serve.py [--port=8321]

Serves the REPO ROOT read-only, so the browser reaches:
  /web/index.html                  the session/judge gallery
  /web/crop.html?...               the framing/crop UI (item 12)
  /web/results/<session>/...       durable outputs (previews, judge surfaces)
  /datasets/<session>/...          tracked records (read-only)

API:
  GET  /api/sessions   -> JSON inventory of web/results/* (sessions, judge
                          surfaces, previews manifest if generated)
  GET  /api/session/<name>
                       -> the session's joined READ-ONLY model: per-set records
                          (acquisition, frame QA normalized across the measured
                          schema drift, recipe cull policy, anomaly objects,
                          fingerprint, experiments ledger), surfaces (stacks
                          joined to wcs/spcc variants, judge surfaces, preview
                          manifest entries, STACKCNT/dims from the FITS header
                          — a metadata read, never pixels), recipe-vs-header
                          kept-count confirmation, framing records, coverage
                          maps on disk, and git-tag approvals (a surface is
                          "approved" only when a `<session>-all<N>-<tag>-approved`
                          tag matches its membership count and recipe tag).
                          The server joins and normalizes for display; records
                          are never rewritten.
  GET  /api/stages     -> the Tier-1 stage registry (fixed allowlist of the
                          repo's pinned scripts + their param specs)
  POST /api/run        -> {stage, args, dry_run?} — validate and (unless
                          dry_run, which returns the exact command) spawn ONE
                          gated run of a registry stage. USER-RATIFIED
                          AMENDMENT (web/README.md): fires only from an
                          explicit per-run user action — the operating loop's
                          DECIDE step made clickable; never automatic, never
                          on page load. One job at a time; argv only (no
                          shell); logs under sessions/.webjobs/.
  GET  /api/jobs, /api/jobs/<id>, /api/jobs/<id>/log?offset=N
                       -> job list / status / incremental log tail
  POST /api/jobs/<id>/kill -> SIGTERM the job's process group (user action)
  POST /api/mount      -> {session, set, mount: fixed|tracked, dry_run?} —
                          the second sanctioned record write: the human
                          mount declaration into the set's acquisition.json
                          (mount field only; exif stays tool-written)
  POST /api/framing    -> write the tracked framing record for a product
                          (datasets/<session>/framing_<product>.json).
                          The UI captures a HUMAN decision; this endpoint
                          moves it into the record — it reads no pixels and
                          decides nothing. Payload:
                            {session, product, canvas:{w,h},
                             rect_screen:{x,y,w,h},   # top-left-origin native px
                             dry_run?: true}
                          The record stores BOTH coordinate conventions
                          (screen top-left AND siril bottom-left: the
                          measured y-flip trap, docs/dead-ends.md) plus
                          RA/Dec corners when the product's _wcs.fit is
                          present (astropy — the tool does the WCS math).
                          Status starts "unverified"; web/verify_framing.py
                          stamps it after the Siril crop+stat check. The
                          render chain must refuse an unverified framing.

Judgment contract: everything served here is a NAVIGATION/SELECTION surface.
Aesthetic judgment happens ONLY on the full-frame lossless PNG16 files opened
in the user's own viewers (web/README.md).
"""
import json
import os
import re
import shlex
import signal
import subprocess
import sys
import threading
import time
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_+.-]*$")  # no /, no leading dot


def _safe(name, what):
    if not isinstance(name, str) or not NAME_RE.match(name) or ".." in name:
        raise ValueError(f"unsafe {what}: {name!r}")
    return name


def sessions_inventory():
    """Sessions = union of the results tree, the tracked records tree AND the
    raw staging tree, so a freshly staged session is navigable (and runnable
    from the Run page) before any record or output exists."""
    root = os.path.join(REPO, "web", "results")
    droot = os.path.join(REPO, "datasets")
    sroot = os.path.join(REPO, "sessions")
    names = set()
    for r in (root, droot, sroot):
        if os.path.isdir(r):
            names.update(s for s in os.listdir(r)
                         if os.path.isdir(os.path.join(r, s))
                         and not s.startswith("."))
    out = []
    for s in sorted(names):
        sdir = os.path.join(root, s)
        if not os.path.isdir(sdir):
            out.append({"session": s, "judge": [], "stacks": [],
                        "previews_manifest": None, "records_only": True})
            continue
        judge = sorted(os.listdir(os.path.join(sdir, "judge"))) \
            if os.path.isdir(os.path.join(sdir, "judge")) else []
        manifest = None
        mpath = os.path.join(sdir, "previews", "manifest.json")
        if os.path.exists(mpath):
            try:
                manifest = json.load(open(mpath))
            except ValueError:
                manifest = {"error": "unreadable manifest.json"}
        stacks = sorted(f for f in os.listdir(sdir)
                        if f.startswith("stack_") and f.endswith(".fit"))
        out.append({"session": s, "judge": judge, "stacks": stacks,
                    "previews_manifest": manifest})
    return out


CALIBRATION_DIRS = {"darks", "biases", "flats", "darkflats", "calib"}


def _read_json(path):
    try:
        with open(path) as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def _norm_frame_qa(rec):
    """One display shape over the measured per-set schema drift:
    set-01 wrote flagged_defect_side_z3p5 + assessment; later sets wrote
    flagged_defect_side_z + cull_note. Records are never rewritten."""
    if not rec:
        return None
    return {
        "total": rec.get("frames_total"),
        "registered": rec.get("registered"),
        "match_failed": rec.get("match_failed"),
        "distribution": rec.get("distribution"),
        "blocks": rec.get("temporal_trend_contiguous_blocks"),
        "flagged": rec.get("flagged_defect_side_z3p5")
        or rec.get("flagged_defect_side_z") or [],
        "caveats": rec.get("caveats"),
        "method": rec.get("method"),
        "assessment": rec.get("assessment") or rec.get("cull_note"),
    }


def _anomaly_summary(rec):
    if not rec:
        return None
    uniq = rec.get("unique_objects") or []
    counts = {"satellite": 0, "aircraft": 0, "unknown": 0}
    for o in uniq:
        cls = o.get("cls")
        counts[cls if cls in counts else "unknown"] += 1
    detections = sum(len(f.get("objects") or [])
                     for f in rec.get("frames") or [])
    return {"counts": counts, "detections": detections,
            "unique": [{k: o.get(k) for k in
                        ("cls", "first", "last", "n", "pa", "files")}
                       for o in uniq]}


def _experiments(path):
    out = []
    try:
        with open(path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    e = json.loads(line)
                except ValueError:
                    continue
                out.append({"param": e.get("param"),
                            "verdict": e.get("verdict")})
    except OSError:
        pass
    return out


def _stack_header(path):
    """Dims + integrated-frame count from the FITS header — metadata only
    (the make_previews.sh pattern); never reads pixel data."""
    try:
        from astropy.io import fits
        h = fits.getheader(path)
        return {"naxis": [int(h.get("NAXIS1", 0)), int(h.get("NAXIS2", 0))],
                "stackcnt": int(h["STACKCNT"]) if "STACKCNT" in h else None}
    except Exception:
        return {"naxis": None, "stackcnt": None}


def _parse_product(base):
    """'set-01+02+03_cov25frame' -> (['set-01','set-02','set-03'], 'cov25frame')."""
    m = re.match(r"^(set-\d+(?:\+\d+)*)_(.+)$", base)
    if not m:
        return [], base
    toks = m.group(1).split("+")
    sets = [toks[0]] + [f"set-{t}" for t in toks[1:]]
    return sets, m.group(2)


def _session_tags(session):
    import subprocess
    try:
        r = subprocess.run(["git", "tag", "--list", f"{session}-*"],
                           capture_output=True, text=True, cwd=REPO, timeout=10)
        return [t for t in r.stdout.split() if t]
    except Exception:
        return []


def session_model(session):
    droot = os.path.join(REPO, "datasets", session)
    rroot = os.path.join(REPO, "web", "results", session)
    stroot = os.path.join(REPO, "sessions", session)
    if not (os.path.isdir(droot) or os.path.isdir(rroot)
            or os.path.isdir(stroot)):
        return None
    model = {"session": session, "tags": _session_tags(session),
             "sets": [], "session_records": [], "surfaces": [],
             "judge": [], "previews_manifest": None, "framing": [],
             "coverage_maps": []}

    # --- per-set records ---
    light_sets = []
    if os.path.isdir(droot):
        for name in sorted(os.listdir(droot)):
            sdir = os.path.join(droot, name)
            if not os.path.isdir(sdir):
                if name.startswith("framing_") and name.endswith(".json"):
                    rec = _read_json(os.path.join(droot, name)) or {}
                    model["framing"].append(
                        {"file": f"datasets/{session}/{name}",
                         "product": rec.get("product"),
                         "status": rec.get("status")})
                elif name.endswith(".json"):
                    rec = _read_json(os.path.join(droot, name)) or {}
                    model["session_records"].append(
                        {"name": name, "path": f"datasets/{session}/{name}",
                         "status": rec.get("status")})
                continue
            qa = _read_json(os.path.join(sdir, "qa_work", "frame_metrics.json"))
            recipe = _read_json(os.path.join(sdir, "recipe.json"))
            entry = {
                "set": name,
                "kind": "calibration" if name in CALIBRATION_DIRS else "lights",
                "acquisition": _read_json(os.path.join(sdir, "acquisition.json")),
                "recipe": (recipe or {}).get("stack"),
                "anomaly": _anomaly_summary(_read_json(
                    os.path.join(sdir, "audit_work", "anomaly_audit.json"))),
                "fingerprint": _read_json(os.path.join(sdir, "fingerprint.json")),
                "experiments": _experiments(os.path.join(sdir, "experiments.jsonl")),
                "records": sorted(
                    os.path.relpath(os.path.join(dp, f), REPO)
                    for dp, _, fs in os.walk(sdir) for f in fs
                    if f.endswith((".json", ".jsonl"))),
            }
            if qa and "dark_level_pedestal_ADU" in qa:
                entry["dark_qa"] = qa          # calibration-group QA shape
            else:
                entry["frame_qa"] = _norm_frame_qa(qa)
            excl = (entry["recipe"] or {}).get("exclude")
            total = (entry.get("frame_qa") or {}).get("total") if qa else None
            entry["kept"] = (total - len(excl)) \
                if (total is not None and excl is not None) else None
            if entry["kind"] == "lights":
                light_sets.append(entry)
            model["sets"].append(entry)
    # staged raw dirs — a fresh session shows its sets (with raw counts, a
    # directory listing only) before any record exists; kind from the
    # staging-layout names. Merges into recorded sets when both exist.
    if os.path.isdir(stroot):
        known = {s["set"]: s for s in model["sets"]}
        for name in sorted(os.listdir(stroot)):
            d = os.path.join(stroot, name)
            if name == "work" or name.startswith(".") or not os.path.isdir(d):
                continue
            n_raw = sum(1 for f in os.listdir(d) if f.lower().endswith(
                (".nef", ".dng", ".cr2", ".cr3", ".arw", ".raf",
                 ".fit", ".fits")))
            if name in known:
                known[name]["staged_frames"] = n_raw
                continue
            entry = {"set": name,
                     "kind": "calibration" if name in CALIBRATION_DIRS
                     else "lights",
                     "staged_only": True, "staged_frames": n_raw,
                     "acquisition": None, "frame_qa": None, "recipe": None,
                     "anomaly": None, "fingerprint": None, "experiments": [],
                     "records": [], "kept": None}
            model["sets"].append(entry)
            if entry["kind"] == "lights":
                light_sets.append(entry)

    kept_by_set = {s["set"]: s["kept"] for s in light_sets}
    n_lights = len(light_sets)

    # --- approvals: <session>-all<N>-<tag>-approved ---
    approved = []
    for t in model["tags"]:
        m = re.match(rf"^{re.escape(session)}-all(\d+)-(.+)-approved$", t)
        if m:
            approved.append((int(m.group(1)), m.group(2), t))

    # --- surfaces: stacks joined to variants, judge, previews, headers ---
    if os.path.isdir(rroot):
        model["judge"] = sorted(os.listdir(os.path.join(rroot, "judge"))) \
            if os.path.isdir(os.path.join(rroot, "judge")) else []
        model["previews_manifest"] = _read_json(
            os.path.join(rroot, "previews", "manifest.json"))
        model["coverage_maps"] = [
            {"file": f, **_stack_header(os.path.join(rroot, f))}
            for f in sorted(os.listdir(rroot))
            if f.startswith("coverage_") and f.endswith(".fit")]
        stacks = sorted(f for f in os.listdir(rroot)
                        if f.startswith("stack_") and f.endswith(".fit"))
        bases = {}
        for f in stacks:
            stem = f[len("stack_"):-len(".fit")]
            base, variant = stem, "base"
            for suf in ("_wcs", "_spcc"):
                if stem.endswith(suf):
                    base, variant = stem[:-len(suf)], suf[1:]
            bases.setdefault(base, {})[variant] = f
        prev = {i.get("product"): i for i in
                (model["previews_manifest"] or {}).get("items", [])
                if i.get("kind") == "selection"}
        for base, variants in sorted(bases.items()):
            sets, tag = _parse_product(base)
            hdr = _stack_header(os.path.join(rroot, variants.get("base")
                                             or sorted(variants.values())[0]))
            judge_name = f"{base}_spcc-linked.png"
            kept = [kept_by_set.get(s) for s in sets]
            expected = sum(kept) if kept and all(k is not None for k in kept) \
                else None
            # "differs" is a neutral measurement: a deliberate-subset render
            # (e.g. a stride tag) differs legitimately; only a full-depth tag
            # differing is a policy error — the UI phrases severity by tag.
            confirm = "unknown"
            if expected is not None and hdr["stackcnt"] is not None:
                confirm = "ok" if expected == hdr["stackcnt"] else "differs"
            is_approved = any(n == len(sets) and atag == tag
                              for n, atag, _ in approved) if sets else False
            sel = prev.get(f"stack_{base}_spcc")
            model["surfaces"].append({
                "product": base, "sets": sets, "recipe_tag": tag,
                "files": variants, "naxis": hdr["naxis"],
                "stackcnt": hdr["stackcnt"], "expected_kept": expected,
                "confirm": confirm,
                "judge": f"judge/{judge_name}"
                if judge_name in model["judge"] else None,
                "thumb": f"previews/thumb_{judge_name}"
                if os.path.exists(os.path.join(
                    rroot, "previews", f"thumb_{judge_name}")) else None,
                "selection": {"preview": sel.get("preview"),
                              "native_wh": sel.get("native_wh"),
                              "reference_boxes": sel.get("reference_boxes")}
                if sel else None,
                "solve": _read_json(os.path.join(
                    rroot, f"solve_stack_{base}.json")),
                "approved": is_approved,
                "approved_tag": next((t for n, atag, t in approved
                                      if n == len(sets) and atag == tag), None),
            })
    return model


# ---------------------------------------------------------------------------
# Tier-1 job execution (user-ratified contract amendment, web/README.md):
# the site EXECUTES a pipeline stage only from an explicit per-run user action
# — the operating loop's DECIDE step made clickable. Never automatic, never on
# page load. The registry below is a fixed allowlist of the repo's own pinned
# scripts; args are validated per stage and passed as argv (no shell), one job
# runs at a time, and every run leaves its log under sessions/.webjobs/.
# ---------------------------------------------------------------------------

JOBS = {}
JOBS_LOCK = threading.Lock()
WEBJOBS_DIR = os.path.join(REPO, "sessions", ".webjobs")


def _arg_session(v):
    _safe(v, "session")
    if not (os.path.isdir(os.path.join(REPO, "sessions", v))
            or os.path.isdir(os.path.join(REPO, "datasets", v))):
        raise ValueError(f"unknown session: {v}")
    return v


def _arg_set(v):
    return _safe(v, "set")


def _arg_repo_path(v, roots, must_exist=True, ext=None):
    if not isinstance(v, str) or v.startswith("/") or ".." in v:
        raise ValueError(f"path must be repo-relative without '..': {v!r}")
    norm = os.path.normpath(v)
    if not any(norm == r or norm.startswith(r + os.sep) for r in roots):
        raise ValueError(f"path must live under {roots}: {v}")
    if ext and not norm.endswith(ext):
        raise ValueError(f"path must end with {ext}: {v}")
    if must_exist and not os.path.exists(os.path.join(REPO, norm)):
        raise ValueError(f"no such file: {v}")
    return norm


def _arg_int(v, lo, hi):
    i = int(v)
    if not lo <= i <= hi:
        raise ValueError(f"out of range [{lo},{hi}]: {v}")
    return i


def _arg_float(v, lo, hi):
    f = float(v)
    if not lo <= f <= hi:
        raise ValueError(f"out of range [{lo},{hi}]: {v}")
    return f


# Each stage: description, loop phase, param specs (served to the UI), and a
# builder returning the argv (repo-relative cwd). Params marked opt are
# omitted when blank. Adding a stage = adding a row here; the UI renders it.
def _stage_registry():
    P = os.path.join
    return {
        "frame_qa": {
            "desc": "per-frame registration QA (Siril regdata) -> tracked frame_metrics.json + kept per-frame records",
            "phase": "measure",
            "params": [
                {"name": "session", "kind": "session", "req": True},
                {"name": "set", "kind": "set", "req": True},
                {"name": "batch", "kind": "int", "req": False, "hint": "frames per disk-bounded batch (default 76)"},
                {"name": "z", "kind": "float", "req": False, "hint": "defect-side robust-z flag threshold (default 3.5)"},
            ],
            "build": lambda a: ["scripts/qa/run_frame_qa.sh",
                                P("sessions", _arg_session(a["session"])), _arg_set(a["set"])]
            + ([f"--batch={_arg_int(a['batch'], 8, 500)}"] if a.get("batch") else [])
            + ([f"--z={_arg_float(a['z'], 1.0, 10.0)}"] if a.get("z") else []),
        },
        "anomaly_audit": {
            "desc": "transient-obstruction classifier (aircraft/satellite/unknown) -> audit_work/anomaly_audit.json",
            "phase": "measure",
            "params": [
                {"name": "session", "kind": "session", "req": True},
                {"name": "set", "kind": "set", "req": True},
            ],
            "build": lambda a: ["python3", "scripts/qa/anomaly_audit.py",
                                P("sessions", _arg_session(a["session"]), _arg_set(a["set"]))],
        },
        "master_dark": {
            "desc": "session master dark from raw darks/ (pinned Siril template: rej 3 3 stack, -nonorm) -> work/masters/dark_master.fit",
            "phase": "calibrate",
            "params": [
                {"name": "session", "kind": "session", "req": True},
                {"name": "force", "kind": "bool", "req": False, "hint": "rebuild over an existing master"},
            ],
            "build": lambda a: ["scripts/stack/build_master_dark.sh",
                                P("sessions", _arg_session(a["session"]))]
            + (["--force"] if a.get("force") else []),
        },
        "sky_flat": {
            "desc": "PER-SET sky flat for a flatless set (validation gates built in) -> work/masters/",
            "phase": "calibrate",
            "params": [
                {"name": "session", "kind": "session", "req": True},
                {"name": "set", "kind": "set", "req": True},
                {"name": "dark", "kind": "path", "req": True, "hint": "master dark, repo-relative under sessions/"},
            ],
            "build": lambda a: ["scripts/stack/build_sky_flat.sh",
                                P("sessions", _arg_session(a["session"])), _arg_set(a["set"]),
                                "--dark=" + _arg_repo_path(a["dark"], ["sessions"], ext=".fit"),
                                "--out=" + P("sessions", _arg_session(a["session"]), "work",
                                             "masters", f"skyflat_{_arg_set(a['set'])}.fit")],
        },
        "stack_standard": {
            "desc": "standard class: calibrate -> register -> rejection stack (matched flats; flatless hard-stops)",
            "phase": "execute",
            "params": [
                {"name": "session", "kind": "session", "req": True},
                {"name": "set", "kind": "set", "req": True},
            ],
            "build": lambda a: ["scripts/stack/run_pipeline.sh",
                                P("sessions", _arg_session(a["session"])), _arg_set(a["set"])],
        },
        "stack_undistort": {
            "desc": "wide-field UNTRACKED class: calibrate -> undistort (darktable/lensfun) -> register -> stack",
            "phase": "execute",
            "params": [
                {"name": "session", "kind": "session", "req": True},
                {"name": "set", "kind": "set", "req": True},
                {"name": "dark", "kind": "path", "req": True},
                {"name": "flat", "kind": "path", "req": True},
                {"name": "frames", "kind": "int", "req": False, "hint": "even-stride subset preserving the time span"},
            ],
            "build": lambda a: ["scripts/stack/run_undistort_pipeline.sh",
                                P("sessions", _arg_session(a["session"])), _arg_set(a["set"]),
                                "--dark=" + _arg_repo_path(a["dark"], ["sessions"], ext=".fit"),
                                "--flat=" + _arg_repo_path(a["flat"], ["sessions"], ext=".fit")]
            + ([f"--frames={_arg_int(a['frames'], 8, 5000)}"] if a.get("frames") else []),
        },
        "stack_undistort_groups": {
            "desc": "same class at FULL depth on tight disk: balanced groups -> per-group stacks -> compose",
            "phase": "execute",
            "params": [
                {"name": "session", "kind": "session", "req": True},
                {"name": "set", "kind": "set", "req": True},
                {"name": "dark", "kind": "path", "req": True},
                {"name": "flat", "kind": "path", "req": True},
                {"name": "group", "kind": "int", "req": False, "hint": "frames per group (default 15)"},
            ],
            "build": lambda a: ["scripts/stack/run_undistort_groups.sh",
                                P("sessions", _arg_session(a["session"])), _arg_set(a["set"]),
                                "--dark=" + _arg_repo_path(a["dark"], ["sessions"], ext=".fit"),
                                "--flat=" + _arg_repo_path(a["flat"], ["sessions"], ext=".fit")]
            + ([f"--group={_arg_int(a['group'], 5, 200)}"] if a.get("group") else []),
        },
        "solve": {
            "desc": "blind astrometric solve (astrometry.net) + WCS inject -> unblocks SPCC",
            "phase": "finish",
            "params": [
                {"name": "stack", "kind": "path", "req": True, "hint": "stack under web/results/, .fit"},
            ],
            "build": lambda a: (lambda s: ["python3", "scripts/calibrate/solve_field.py", s,
                                           "--inject=" + s[:-4] + "_wcs.fit"])(
                _arg_repo_path(a["stack"], [os.path.join("web", "results")], ext=".fit")),
        },
        "spcc_cone": {
            "desc": "local Gaia chunk cover check for a solved field (--fetch downloads missing)",
            "phase": "finish",
            "params": [
                {"name": "wcs", "kind": "path", "req": True, "hint": "solved _wcs.fit under web/results/"},
                {"name": "fetch", "kind": "bool", "req": False},
            ],
            "build": lambda a: ["python3", "scripts/calibrate/spcc_cone.py",
                                _arg_repo_path(a["wcs"], [os.path.join("web", "results")], ext=".fit")]
            + (["--fetch"] if a.get("fetch") else []),
        },
        "spcc": {
            "desc": "Siril SPCC on the solved stack; K factors captured to work/spcc_<set>.json",
            "phase": "finish",
            "params": [
                {"name": "session", "kind": "session", "req": True},
                {"name": "set", "kind": "set", "req": True},
                {"name": "tag", "kind": "str", "req": False, "hint": "suffix so an experiment never overwrites the canonical record"},
            ],
            "build": lambda a: ["python3", "scripts/calibrate/spcc_run.py",
                                P("sessions", _arg_session(a["session"])), _arg_set(a["set"])]
            + ([f"--tag={_safe(a['tag'], 'tag')}"] if a.get("tag") else []),
        },
        "finish_render": {
            "desc": "stack -> solve -> SPCC -> linked autostretch -> judge/ PNG16 (the diagnostic judge surface)",
            "phase": "finish",
            "params": [
                {"name": "stack", "kind": "path", "req": True},
                {"name": "name", "kind": "str", "req": True, "hint": "judge surface stem, e.g. set-01_full"},
                {"name": "session", "kind": "session", "req": True},
                {"name": "set", "kind": "set", "req": True},
            ],
            "build": lambda a: ["scripts/stack/finish_render.sh",
                                _arg_repo_path(a["stack"], [os.path.join("web", "results")], ext=".fit"),
                                _safe(a["name"], "name"),
                                "--session=" + P("sessions", _arg_session(a["session"])),
                                "--set=" + _arg_set(a["set"])],
        },
        "previews": {
            "desc": "Siril-made navigation previews + manifest (thumbs, selection surfaces, coverage veils)",
            "phase": "surfaces",
            "params": [
                {"name": "session", "kind": "session", "req": True},
                {"name": "cov_min", "kind": "int", "req": False, "hint": "coverage veil threshold in members (default 25)"},
            ],
            "build": lambda a: ["web/make_previews.sh", _arg_session(a["session"])]
            + ([f"--cov-min={_arg_int(a['cov_min'], 1, 65)}"] if a.get("cov_min") else []),
        },
        "verify_framing": {
            "desc": "Siril crop+stat verification of a drawn framing record (map mode or sky-floor mode)",
            "phase": "surfaces",
            "params": [
                {"name": "session", "kind": "session", "req": True},
                {"name": "product", "kind": "str", "req": True},
                {"name": "map", "kind": "path", "req": False, "hint": "coverage map .fit (map mode)"},
                {"name": "map_min", "kind": "int", "req": False, "hint": "required members (map mode)"},
                {"name": "min_floor", "kind": "int", "req": False, "hint": "sibling-class sky floor ADU (no-map mode)"},
            ],
            "build": lambda a: ["python3", "web/verify_framing.py",
                                _arg_session(a["session"]), _safe(a["product"], "product")]
            + ([f"--map={_arg_repo_path(a['map'], [os.path.join('web', 'results')], ext='.fit')}"]
               if a.get("map") else [])
            + ([f"--map-min={_arg_int(a['map_min'], 1, 65)}"] if a.get("map_min") else [])
            + ([f"--min-floor={_arg_int(a['min_floor'], 0, 65535)}"] if a.get("min_floor") else []),
        },
    }


STAGES = _stage_registry()


def stages_public():
    return {name: {"desc": s["desc"], "phase": s["phase"], "params": s["params"]}
            for name, s in STAGES.items()}


def start_job(stage, args, dry_run=False):
    if stage not in STAGES:
        raise ValueError(f"unknown stage: {stage}")
    argv = STAGES[stage]["build"](args or {})
    cmd = " ".join(shlex.quote(c) for c in argv)
    if dry_run:
        return {"dry_run": True, "stage": stage, "cmd": cmd}
    with JOBS_LOCK:
        running = [j for j in JOBS.values() if j["status"] == "running"]
        if running:
            raise RuntimeError(
                f"a job is already running ({running[0]['id']} — {running[0]['stage']}); "
                "one gated run at a time")
        jid = f"j{time.strftime('%Y%m%d-%H%M%S')}-{stage}"
        os.makedirs(WEBJOBS_DIR, exist_ok=True)
        log_path = os.path.join(WEBJOBS_DIR, jid + ".log")
        log_f = open(log_path, "w")
        log_f.write(f"$ {cmd}\n")
        log_f.flush()
        proc = subprocess.Popen(argv, cwd=REPO, stdout=log_f,
                                stderr=subprocess.STDOUT,
                                start_new_session=True)
        JOBS[jid] = {"id": jid, "stage": stage, "cmd": cmd,
                     "status": "running", "rc": None,
                     "started": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                     "ended": None, "log": os.path.relpath(log_path, REPO),
                     "_proc": proc, "_logf": log_f}
    return {"id": jid, "stage": stage, "cmd": cmd, "status": "running"}


def _job_refresh(j):
    p = j.get("_proc")
    if p and j["status"] == "running":
        rc = p.poll()
        if rc is not None:
            j["status"] = "done" if rc == 0 else "failed"
            j["rc"] = rc
            j["ended"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            try:
                j["_logf"].close()
            except OSError:
                pass
    return {k: v for k, v in j.items() if not k.startswith("_")}


def jobs_list():
    with JOBS_LOCK:
        return [_job_refresh(j) for j in
                sorted(JOBS.values(), key=lambda x: x["id"], reverse=True)]


def job_get(jid):
    with JOBS_LOCK:
        j = JOBS.get(jid)
        return _job_refresh(j) if j else None


def job_log(jid, offset):
    with JOBS_LOCK:
        j = JOBS.get(jid)
        if not j:
            return None
        state = _job_refresh(j)
        path = os.path.join(REPO, j["log"])
    try:
        with open(path) as f:
            f.seek(offset)
            data = f.read()
    except OSError:
        data = ""
    return {"offset": offset + len(data), "data": data,
            "status": state["status"], "rc": state["rc"]}


def job_kill(jid):
    with JOBS_LOCK:
        j = JOBS.get(jid)
        if not j:
            return None
        if j["status"] == "running" and j.get("_proc"):
            try:
                os.killpg(os.getpgid(j["_proc"].pid), signal.SIGTERM)
            except ProcessLookupError:
                pass
        return _job_refresh(j)


def radec_corners(wcs_path, rect_screen, canvas_h):
    """RA/Dec of the rect's corners via astropy from the solved header.
    rect_screen is top-left-origin; FITS pixel y counts from the bottom, so
    convert before pix->world. Returns None when astropy/WCS is unavailable."""
    try:
        from astropy.io import fits
        from astropy.wcs import WCS
    except ImportError:
        return None
    if not os.path.exists(wcs_path):
        return None
    with fits.open(wcs_path) as hdul:
        w = WCS(hdul[0].header, naxis=2)
    x, y, bw, bh = (rect_screen[k] for k in ("x", "y", "w", "h"))
    y_fits_bottom = canvas_h - (y + bh)          # screen top-left -> FITS bottom-left
    corners_pix = [(x, y_fits_bottom), (x + bw, y_fits_bottom),
                   (x, y_fits_bottom + bh), (x + bw, y_fits_bottom + bh)]
    out = []
    for cx, cy in corners_pix:
        sky = w.pixel_to_world(cx, cy)
        out.append([round(float(sky.ra.deg), 6), round(float(sky.dec.deg), 6)])
    return out


MOUNTS = ("fixed", "tracked")
ACQ_NOTE = ("`mount` is the one acquisition fact EXIF cannot record and a "
            "consumer must be told; `exif` is auto-derived by "
            "scripts/lib/acquisition.py — do not hand-edit it.")


def build_mount_record(payload):
    """The second sanctioned record write (web/README amendment): capture the
    human-declared mount into datasets/<session>/<set>/acquisition.json.
    Writes ONLY the `mount` field — `exif` stays tool-written; a mount-only
    pre-declaration is exactly what acquisition.resolve() expects (it
    preserves the declared mount and fills/refreshes exif around it)."""
    session = _arg_session(payload["session"])
    set_name = _safe(payload["set"], "set")
    mount = str(payload.get("mount", "")).strip().lower()
    if mount not in MOUNTS:
        raise ValueError(f"mount must be one of {MOUNTS}")
    path = os.path.join(REPO, "datasets", session, set_name,
                        "acquisition.json")
    record = _read_json(path) or {"_note": ACQ_NOTE}
    record["mount"] = mount
    return path, record


def build_framing_record(payload):
    session = _safe(payload["session"], "session")
    product = _safe(payload["product"], "product")
    canvas = payload["canvas"]
    rs = payload["rect_screen"]
    for k in ("x", "y", "w", "h"):
        if not isinstance(rs.get(k), int) or (k in "wh" and rs[k] <= 0):
            raise ValueError(f"rect_screen.{k} must be a positive int")
    cw, ch = int(canvas["w"]), int(canvas["h"])
    if not (0 <= rs["x"] and 0 <= rs["y"]
            and rs["x"] + rs["w"] <= cw and rs["y"] + rs["h"] <= ch):
        raise ValueError("rect_screen exceeds the canvas")
    # Siril crop's y-origin is the OPPOSITE end from screen/numpy row order —
    # the measured trap (docs/dead-ends.md): y_siril = H - y_screen - h.
    rect_siril = {"x": rs["x"], "y": ch - rs["y"] - rs["h"],
                  "w": rs["w"], "h": rs["h"]}
    wcs_path = os.path.join(REPO, "web", "results", session,
                            f"{product}_wcs.fit")
    if not os.path.exists(wcs_path) and product.endswith("_spcc"):
        wcs_path = os.path.join(REPO, "web", "results", session,
                                product[:-5] + "_wcs.fit")
    corners = radec_corners(wcs_path, rs, ch)
    record = {
        "purpose": "user-drawn product framing (BACKLOG item 12) — the "
                   "record IS the product; nothing renders from an "
                   "unrecorded or unverified box",
        "session": session,
        "product": product,
        "canvas_wh": [cw, ch],
        "rect_screen_topleft": rs,
        "rect_siril_crop_args": [rect_siril["x"], rect_siril["y"],
                                 rect_siril["w"], rect_siril["h"]],
        "coordinate_note": "rect_screen is top-left-origin (browser/numpy row "
                           "order); rect_siril_crop_args is Siril crop's "
                           "bottom-left origin (y_siril = H - y_screen - h — "
                           "the measured y-flip trap). Verification must use "
                           "the siril args.",
        "radec_corners_deg": corners,
        "radec_source": os.path.relpath(wcs_path, REPO)
        if corners else None,
        "status": "unverified",
        "verification": "run web/verify_framing.py — Siril crop+stat on the "
                        "coverage map (min >= threshold) or the stack's "
                        "sibling-class sky floor; a render must refuse an "
                        "unverified framing",
        "drawn_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    path = os.path.join(REPO, "datasets", session, f"framing_{product}.json")
    return path, record


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=REPO, **kw)

    def _json(self, code, obj):
        body = json.dumps(obj, indent=1).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/" or self.path == "/web":
            self.send_response(302)
            self.send_header("Location", "/web/index.html")
            self.end_headers()
            return
        if self.path == "/api/sessions":
            return self._json(200, sessions_inventory())
        if self.path.startswith("/api/session/"):
            try:
                name = _safe(self.path[len("/api/session/"):], "session")
            except ValueError as e:
                return self._json(400, {"error": str(e)})
            model = session_model(name)
            if model is None:
                return self._json(404, {"error": f"no such session: {name}"})
            return self._json(200, model)
        if self.path == "/api/stages":
            return self._json(200, stages_public())
        if self.path == "/api/jobs":
            return self._json(200, jobs_list())
        m = re.match(r"^/api/jobs/([A-Za-z0-9_-]+)/log(?:\?offset=(\d+))?$",
                     self.path)
        if m:
            out = job_log(m.group(1), int(m.group(2) or 0))
            return self._json(200, out) if out else \
                self._json(404, {"error": "no such job"})
        m = re.match(r"^/api/jobs/([A-Za-z0-9_-]+)$", self.path)
        if m:
            out = job_get(m.group(1))
            return self._json(200, out) if out else \
                self._json(404, {"error": "no such job"})
        return super().do_GET()

    def do_POST(self):
        if self.path == "/api/run":
            # Tier-1 gate: this endpoint only ever fires from an explicit
            # user action in the UI (the DECIDE click) — see the amendment
            # in web/README.md. Stage allowlist + per-stage arg validation.
            try:
                n = int(self.headers.get("Content-Length", 0))
                payload = json.loads(self.rfile.read(n))
                out = start_job(payload.get("stage"), payload.get("args"),
                                dry_run=bool(payload.get("dry_run")))
                return self._json(200, out)
            except (KeyError, ValueError, TypeError) as e:
                return self._json(400, {"error": str(e)})
            except RuntimeError as e:
                return self._json(409, {"error": str(e)})
        m = re.match(r"^/api/jobs/([A-Za-z0-9_-]+)/kill$", self.path)
        if m:
            out = job_kill(m.group(1))
            return self._json(200, out) if out else \
                self._json(404, {"error": "no such job"})
        if self.path == "/api/mount":
            try:
                n = int(self.headers.get("Content-Length", 0))
                payload = json.loads(self.rfile.read(n))
                path, record = build_mount_record(payload)
                if payload.get("dry_run"):
                    return self._json(200, {"dry_run": True, "path": path,
                                            "record": record})
                os.makedirs(os.path.dirname(path), exist_ok=True)
                with open(path, "w") as f:
                    json.dump(record, f, indent=1)
                    f.write("\n")
                return self._json(200, {"written": os.path.relpath(path, REPO),
                                        "record": record})
            except (KeyError, ValueError, TypeError) as e:
                return self._json(400, {"error": str(e)})
        if self.path != "/api/framing":
            return self._json(404, {"error": "unknown endpoint"})
        try:
            n = int(self.headers.get("Content-Length", 0))
            payload = json.loads(self.rfile.read(n))
            path, record = build_framing_record(payload)
            if payload.get("dry_run"):
                return self._json(200, {"dry_run": True, "path": path,
                                        "record": record})
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w") as f:
                json.dump(record, f, indent=1)
                f.write("\n")
            return self._json(200, {"written": os.path.relpath(path, REPO),
                                    "record": record})
        except (KeyError, ValueError, TypeError) as e:
            return self._json(400, {"error": str(e)})


def main():
    port = 8321
    for a in sys.argv[1:]:
        if a.startswith("--port="):
            port = int(a.split("=", 1)[1])
    srv = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    print(f"[serve] http://127.0.0.1:{port}/web/index.html  (root: {REPO})")
    print("[serve] local-only; Ctrl-C to stop")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
