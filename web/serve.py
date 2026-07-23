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
  GET  /api/paths/<session>
                       -> candidate repo-relative paths for the Run form's
                          path params, by class (masters/stacks/wcs/maps) —
                          directory listings only; POST /api/run revalidates
  POST /api/run        -> {stage, args, dry_run?} — validate and (unless
                          dry_run, which returns the exact command) spawn ONE
                          gated run of a registry stage. USER-RATIFIED
                          AMENDMENT (web/README.md): fires only from an
                          explicit per-run user action — the operating loop's
                          DECIDE step made clickable; never automatic, never
                          on page load. One job at a time; argv only (no
                          shell); logs under sessions/.webjobs/.
  GET  /api/jobs, /api/jobs/<id>, /api/jobs/<id>/log?offset=N
                       -> job list / status / incremental log tail. Every job
                          also persists a <id>.json record beside its log;
                          on startup, still-running records are re-adopted
                          (pid-checked) so a server restart cannot orphan a
                          run or silently reopen the one-job-at-a-time gate.
                          An adopted job whose process is gone reports status
                          "unknown" (its exit code is unrecoverable).
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


def _git_rev():
    try:
        r = subprocess.run(["git", "rev-parse", "--short", "HEAD"],
                           capture_output=True, text=True, cwd=REPO, timeout=10)
        rev = r.stdout.strip() or "unknown"
        d = subprocess.run(["git", "status", "--porcelain"],
                           capture_output=True, text=True, cwd=REPO, timeout=10)
        return rev + ("+dirty" if d.stdout.strip() else "")
    except Exception:
        return "unknown"


# Captured at import: this names the code THIS process is serving. A registry
# edit after startup is invisible to a running server, so the page shows this
# rev — when it trails the repo's HEAD, restart before the next run.
SERVER_REV = _git_rev()
SERVER_STARTED = time.strftime("%Y-%m-%dT%H:%M:%S")


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


def set_kind(name):
    """Staging-layout classification for a session dir. Fixed calibration
    names, per-filter flat siblings (flats_<name> — the filter-wheel staging
    shape the FITS stack path resolves by header identity), and the corpus
    answer key (reference/ — README "Adding a dataset" step 0) are never
    LIGHT sets; everything else is."""
    if name in CALIBRATION_DIRS or name.startswith("flats_"):
        return "calibration"
    if name == "reference":
        return "reference"
    return "lights"


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


def _parse_product(base, known_sets=()):
    """Resolve a stack product name against the session's ACTUAL sets:
    '<set>' -> ([set], None); '<set>_<tag>' -> ([set], tag) on the longest
    known-set prefix (so 'lights_Blue' is the set, never set 'lights' +
    tag 'Blue'); the legacy compressed combo 'set-01+02+03_cov25frame' ->
    (['set-01','set-02','set-03'], 'cov25frame'). Unresolvable -> ([], base)."""
    for s in sorted(known_sets, key=len, reverse=True):
        if base == s:
            return [s], None
        if base.startswith(s + "_"):
            return [s], base[len(s) + 1:]
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
            comp = _read_json(os.path.join(sdir, "composition.json"))
            entry = {
                "set": name,
                # a composition record marks a VIRTUAL composed target — no
                # lights of its own; compose builds it from member stacks
                "kind": "composed" if comp else set_kind(name),
                "composition": comp,
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
                     "kind": set_kind(name),
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
        # judge surfaces pair to their stack product by NAME PREFIX — the
        # surface class varies (_spcc-linked for colour, _lum-autostretch
        # for mono), so no single class name may be hardcoded; a file pairs
        # to the LONGEST matching base so a shorter product cannot steal it
        judge_by_base = {}
        for j in model["judge"]:
            cands = [b for b in bases if j.startswith(b + "_")]
            if cands:
                judge_by_base.setdefault(max(cands, key=len), []).append(j)
        for base, variants in sorted(bases.items()):
            sets, tag = _parse_product(base, [s["set"] for s in model["sets"]])
            hdr = _stack_header(os.path.join(rroot, variants.get("base")
                                             or sorted(variants.values())[0]))
            jfiles = sorted(judge_by_base.get(base, []))
            judge_name = jfiles[0] if jfiles else None
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
                "judge": f"judge/{judge_name}" if judge_name else None,
                "thumb": f"previews/thumb_{judge_name}"
                if judge_name and os.path.exists(os.path.join(
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


def _job_public(j):
    return {k: v for k, v in j.items() if not k.startswith("_")}


def _job_persist(j):
    """Job state lives on disk (<jid>.json beside <jid>.log), not only in this
    process — the record is what lets a restarted server re-adopt a run."""
    try:
        path = os.path.join(REPO, j["log"])[:-len(".log")] + ".json"
        with open(path, "w") as f:
            json.dump(_job_public(j), f, indent=1)
            f.write("\n")
    except OSError:
        pass


def _log_tail(j, max_bytes=4096, max_lines=25):
    """Bounded tail of a job's log — attached to the record when a job does
    not end 'done', so the failure evidence travels with the job instead of
    requiring a log walk. An excerpt, verbatim; never a judgment."""
    try:
        with open(os.path.join(REPO, j["log"]), "rb") as f:
            f.seek(0, 2)
            f.seek(max(0, f.tell() - max_bytes))
            data = f.read().decode(errors="replace")
    except OSError:
        return None
    return "\n".join(data.splitlines()[-max_lines:]) or None


def _pid_alive(pid, cmd):
    """Best-effort liveness for an adopted job: the pid must exist AND its
    /proc cmdline must still contain the job's own command token (guards the
    common pid-reuse case; an unreadable /proc entry counts as alive)."""
    if not pid:
        return False
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    try:
        with open(f"/proc/{pid}/cmdline", "rb") as f:
            cmdline = f.read().replace(b"\0", b" ").decode(errors="replace")
    except OSError:
        return True
    tok = (cmd or "").split()[0] if cmd else ""
    return not tok or os.path.basename(tok) in cmdline


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


def _sets_list(session, raw):
    """'set-01,set-02' -> validated set names whose groups dirs exist."""
    names = [t.strip() for t in str(raw).replace(",", " ").split() if t.strip()]
    if len(names) < 2:
        raise ValueError("need at least two sets, comma-separated")
    out = []
    for n in names:
        _safe(n, "set")
        d = os.path.join(REPO, "sessions", session, "work", f"groups_{n}")
        if not os.path.isdir(d):
            raise ValueError(f"no group sub-stacks for {n} "
                             f"(sessions/{session}/work/groups_{n} absent)")
        out.append(n)
    return out


def _join_name(sets):
    """['set-01','set-02'] -> 'set-01+02' (the product naming convention)."""
    return sets[0] + "".join(
        "+" + (s[4:] if s.startswith("set-") else s) for s in sets[1:])


def _arg_framing(v):
    if v not in ("min", "max"):
        raise ValueError("framing must be min or max")
    return v


def _veil_threshold(session):
    """The coverage-veil threshold (members) the previews were generated
    with — the bound the user SAW while drawing. Read from the manifest;
    None when no veil preview exists."""
    man = _read_json(os.path.join(REPO, "web", "results", session,
                                  "previews", "manifest.json")) or {}
    for i in man.get("items") or []:
        if i.get("kind") == "coverage" and i.get("threshold_members"):
            return i["threshold_members"]
    return None


def _verify_framing_argv(a):
    """Mode pairing is validated HERE so a bad combination fails in the form
    (dry-run/Run click), never as a spawned job: map mode needs map_min
    (blank derives the drawn veil threshold); exactly one mode at a time."""
    argv = ["python3", "web/verify_framing.py",
            _arg_session(a["session"]), _safe(a["product"], "product")]
    has_map, has_floor = bool(a.get("map")), bool(a.get("min_floor"))
    if has_map and has_floor:
        raise ValueError("pick ONE mode: map (+ map_min) OR min_floor")
    if not has_map and not has_floor:
        raise ValueError("pick a mode: map (+ map_min) or min_floor")
    if has_map:
        mm = a.get("map_min") or _veil_threshold(a["session"])
        if not mm:
            raise ValueError("map mode needs map_min — no coverage-veil "
                             "threshold found in the previews manifest to "
                             "derive it from")
        argv += ["--map=" + _arg_repo_path(
                     a["map"], [os.path.join("web", "results")], ext=".fit"),
                 f"--map-min={_arg_int(mm, 1, 65)}"]
    else:
        argv.append(f"--min-floor={_arg_int(a['min_floor'], 0, 65535)}")
    return argv


def _derive_set(stack_rel, explicit, session=None):
    """The SPCC-routing set: explicit wins; else the stack name resolves
    against the session's ACTUAL sets (the combine precedent — routing only
    affects the recipe spec lookup and the K-factor record's name), so a
    composed product like stack_<target>_comp.fit routes by its target."""
    if explicit:
        return _arg_set(explicit)
    stem = os.path.basename(stack_rel)
    if stem.startswith("stack_") and stem.endswith(".fit"):
        known = []
        if session:
            m = session_model(session)
            known = [s["set"] for s in m["sets"]] if m else []
        sets, _tag = _parse_product(stem[len("stack_"):-len(".fit")], known)
        if sets:
            return sets[0]
    raise ValueError("cannot derive the SPCC-routing set from the stack "
                     "name — pass `set` explicitly")


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
                {"name": "dark", "kind": "path", "req": True, "choices": "masters_dark", "hint": "master dark under work/masters/"},
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
                {"name": "dark", "kind": "path", "req": True, "choices": "masters_dark"},
                {"name": "flat", "kind": "path", "req": True, "choices": "masters_flat"},
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
                {"name": "dark", "kind": "path", "req": True, "choices": "masters_dark"},
                {"name": "flat", "kind": "path", "req": True, "choices": "masters_flat"},
                {"name": "group", "kind": "int", "req": False, "hint": "frames per group (default 15)"},
            ],
            "build": lambda a: ["scripts/stack/run_undistort_groups.sh",
                                P("sessions", _arg_session(a["session"])), _arg_set(a["set"]),
                                "--dark=" + _arg_repo_path(a["dark"], ["sessions"], ext=".fit"),
                                "--flat=" + _arg_repo_path(a["flat"], ["sessions"], ext=".fit")]
            + ([f"--group={_arg_int(a['group'], 5, 200)}"] if a.get("group") else []),
        },
        "compose": {
            "desc": "compose already-built group sub-stacks across sets into one stack (register -2pass -> plain mean; valid post-undistort — homographies compose). framing=min keeps the all-members overlap, max the union",
            "phase": "execute",
            "params": [
                {"name": "session", "kind": "session", "req": True},
                {"name": "sets", "kind": "sets", "req": True, "hint": "sets with group sub-stacks; all pre-checked"},
                {"name": "framing", "kind": "enum", "options": ["min", "max"], "req": True, "hint": "min = all-members overlap · max = union"},
            ],
            "build": lambda a: (lambda ses, sets, fr:
                                ["scripts/stack/run_undistort_compose.sh",
                                 f"--out=web/results/{ses}/stack_{_join_name(sets)}_{fr}.fit",
                                 f"--framing={fr}"]
                                + [f"sessions/{ses}/work/groups_{n}" for n in sets])(
                _arg_session(a["session"]),
                _sets_list(_arg_session(a["session"]), a["sets"]),
                _arg_framing(a.get("framing"))),
        },
        "compose_channels": {
            "desc": "multi-channel target: member per-filter/per-line stacks -> ONE composed linear colour stack per its composition.json (mono-filters members are Siril-aligned to the reference member first)",
            "phase": "execute",
            "params": [
                {"name": "session", "kind": "session", "req": True},
                {"name": "target", "kind": "str", "req": True, "choices": "composed",
                 "hint": "composed target (datasets/<session>/<target>/composition.json)"},
            ],
            "build": lambda a: ["python3", "scripts/stack/compose.py",
                                P("sessions", _arg_session(a["session"])),
                                _arg_set(a["target"])],
        },
        "coverage_probe": {
            "desc": "per-pixel coverage map of a compose (constant twins through the stored registration; value/1000 = covering members; members*1000 must stay <= 65535)",
            "phase": "surfaces",
            "params": [
                {"name": "session", "kind": "session", "req": True},
                {"name": "sets", "kind": "sets", "req": True, "hint": "same sets and order as the compose it maps"},
                {"name": "framing", "kind": "enum", "options": ["min", "max"], "default": "max", "req": False, "hint": "match the compose (default max)"},
            ],
            "build": lambda a: (lambda ses, sets, fr:
                                ["scripts/qa/coverage_probe.sh",
                                 f"--out=web/results/{ses}/coverage_{_join_name(sets)}_{fr}.fit",
                                 f"--framing={fr}"]
                                + [f"sessions/{ses}/work/groups_{n}" for n in sets])(
                _arg_session(a["session"]),
                _sets_list(_arg_session(a["session"]), a["sets"]),
                _arg_framing(a.get("framing") or "max")),
        },
        "solve": {
            "desc": "blind astrometric solve (astrometry.net) + WCS inject -> unblocks SPCC",
            "phase": "finish",
            "params": [
                {"name": "stack", "kind": "path", "req": True, "choices": "stacks", "hint": "stack under web/results/"},
                {"name": "central", "kind": "float", "req": False, "hint": "restrict solve detection to the central fraction — defaults to 0.35 for max-tag (union) stacks, none otherwise; measured: a union solve without it starves on seam false-detections"},
            ],
            "build": lambda a: (lambda s: ["python3", "scripts/calibrate/solve_field.py", s,
                                           "--inject=" + s[:-4] + "_wcs.fit"]
            + ([f"--central={_arg_float(a['central'], 0.1, 1.0)}"] if a.get("central")
               else (["--central=0.35"] if _parse_product(
                   os.path.basename(s)[len("stack_"):-len(".fit")])[1]
                   .startswith("max") else [])))(
                _arg_repo_path(a["stack"], [os.path.join("web", "results")], ext=".fit")),
        },
        "spcc_cone": {
            "desc": "local Gaia chunk cover check for a solved field (--fetch downloads missing)",
            "phase": "finish",
            "params": [
                {"name": "wcs", "kind": "path", "req": True, "choices": "wcs", "hint": "solved _wcs.fit under web/results/"},
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
                {"name": "stack", "kind": "path", "req": True, "choices": "stacks"},
                {"name": "name", "kind": "str", "req": False, "hint": "judge surface stem — auto-derived from the stack (product stem, stack_ prefix stripped) when blank; crop-record runs append 'framed' so the framed product never lands on its source; a name that breaks the convention orphans the surface from its card"},
                {"name": "session", "kind": "session", "req": True},
                {"name": "set", "kind": "set", "req": False, "hint": "SPCC recipe routing + record naming — auto-derived from the stack name's first member when blank"},
                {"name": "central", "kind": "float", "req": False, "hint": "restrict solve detection to the central fraction — defaults to 0.35 for max-tag (union) stacks, none otherwise; measured: a union solve without it starves on seam false-detections"},
                {"name": "crop_record", "kind": "path", "req": False, "choices": "framings", "hint": "VERIFIED framing record — crops the LINEAR stack before solve/SPCC/stretch; refuses unverified"},
            ],
            "build": lambda a: (lambda stack: ["scripts/stack/finish_render.sh",
                                stack,
                                # a crop run writes stack_<name>.fit as a NEW
                                # product: the derived default gets a 'framed'
                                # suffix so it can never equal the input stem
                                _safe(re.sub(r"^stack_", "",
                                             a.get("name")
                                             or os.path.basename(stack)[:-len(".fit")]
                                             + ("framed" if a.get("crop_record") else "")),
                                      "name"),
                                "--session=" + P("sessions", _arg_session(a["session"])),
                                "--set=" + _derive_set(
                                    stack, a.get("set"),
                                    _arg_session(a["session"]))]
            + ([f"--central={_arg_float(a['central'], 0.1, 1.0)}"] if a.get("central")
               else (["--central=0.35"] if _parse_product(
                   os.path.basename(stack)[len("stack_"):-len(".fit")])[1]
                   .startswith("max") else []))
            + ([f"--crop-record={_arg_repo_path(a['crop_record'], ['datasets'], ext='.json')}"]
               if a.get("crop_record") else []))(
                _arg_repo_path(a["stack"], [os.path.join("web", "results")], ext=".fit")),
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
        "install_lens_model": {
            "desc": "install the fitted 24-70/4 distortion entry into the machine-local lensfun user DB and strip vignetting/tca (distortion-only enforcement); idempotent, stops loudly on upstream drift; RE-RUN after every lensfun-update-data",
            "phase": "setup",
            "params": [],
            "build": lambda a: ["scripts/darktable/install_lens_model.sh"],
        },
        "install_styles": {
            "desc": "install the pinned darktable lens styles into a session's work/dtcfg (the undistort driver also self-installs per run — this is manual verification)",
            "phase": "setup",
            "params": [
                {"name": "session", "kind": "session", "req": True},
            ],
            "build": lambda a: ["scripts/darktable/install_styles.sh",
                                P("sessions", _arg_session(a["session"]),
                                  "work", "dtcfg")],
        },
        "verify_framing": {
            "desc": "Siril crop+stat verification of a drawn framing record (map mode or sky-floor mode)",
            "phase": "surfaces",
            "params": [
                {"name": "session", "kind": "session", "req": True},
                {"name": "product", "kind": "str", "req": True, "choices": "framing_products", "hint": "product of a drawn framing record (unverified first)"},
                {"name": "map", "kind": "path", "req": False, "choices": "maps", "hint": "coverage map .fit (map mode)"},
                {"name": "map_min", "kind": "int", "req": False, "hint": "required members (map mode) — blank derives the veil threshold the previews were drawn against"},
                {"name": "min_floor", "kind": "int", "req": False, "hint": "sibling-class sky floor ADU (no-map mode)"},
            ],
            "build": _verify_framing_argv,
        },
    }


STAGES = _stage_registry()


def stages_public():
    return {name: {"desc": s["desc"], "phase": s["phase"], "params": s["params"]}
            for name, s in STAGES.items()}


def path_choices(session):
    """Candidate repo-relative paths for the Run form's path params, by class
    — a directory listing (names only), so path boxes can offer options the
    way the set box does. The server remains the validator on POST."""
    _arg_session(session)
    mdir = os.path.join(REPO, "sessions", session, "work", "masters")
    rdir = os.path.join(REPO, "web", "results", session)
    ls = lambda d, pred: sorted(
        f for f in (os.listdir(d) if os.path.isdir(d) else []) if pred(f))
    return {
        "masters": [f"sessions/{session}/work/masters/{f}"
                    for f in ls(mdir, lambda f: f.endswith(".fit"))],
        # class-split master lists so a --dark box never suggests a flat or
        # bias master and vice versa (bias_master is internal to the flat
        # build — no stage takes it, so no list offers it)
        "masters_dark": [f"sessions/{session}/work/masters/{f}"
                         for f in ls(mdir, lambda f: f.endswith(".fit")
                                     and f.startswith("dark"))],
        "masters_flat": [f"sessions/{session}/work/masters/{f}"
                         for f in ls(mdir, lambda f: f.endswith(".fit")
                                     and f.startswith(("flat", "skyflat")))],
        "stacks": [f"web/results/{session}/{f}"
                   for f in ls(rdir, lambda f: f.startswith("stack_")
                               and f.endswith(".fit")
                               and not f.endswith(("_wcs.fit", "_spcc.fit")))],
        "wcs": [f"web/results/{session}/{f}"
                for f in ls(rdir, lambda f: f.endswith("_wcs.fit"))],
        "maps": [f"web/results/{session}/{f}"
                 for f in ls(rdir, lambda f: f.startswith("coverage_")
                             and f.endswith(".fit"))],
        "framings": [f"datasets/{session}/{f}"
                     for f in ls(os.path.join(REPO, "datasets", session),
                                 lambda f: f.startswith("framing_")
                                 and f.endswith(".json"))],
        # bare product names of the drawn framing records, unverified first —
        # the verify_framing form offers these instead of free-typing
        "framing_products": [p for _, p in sorted(
            ((1 if (_read_json(os.path.join(REPO, "datasets", session, f))
                    or {}).get("status") == "verified" else 0,
              f[len("framing_"):-len(".json")])
             for f in ls(os.path.join(REPO, "datasets", session),
                         lambda f: f.startswith("framing_")
                         and f.endswith(".json"))))],
        "groupsets": sorted(
            d[len("groups_"):] for d in
            (os.listdir(os.path.join(REPO, "sessions", session, "work"))
             if os.path.isdir(os.path.join(REPO, "sessions", session, "work"))
             else [])
            if d.startswith("groups_") and os.path.isdir(
                os.path.join(REPO, "sessions", session, "work", d))),
        # composed virtual targets — set dirs under datasets/ carrying a
        # composition.json (the channel compose's unit)
        "composed": sorted(
            d for d in
            (os.listdir(os.path.join(REPO, "datasets", session))
             if os.path.isdir(os.path.join(REPO, "datasets", session)) else [])
            if os.path.exists(os.path.join(
                REPO, "datasets", session, d, "composition.json"))),
    }


LENSFUN_DB = os.path.expanduser(
    "~/.local/share/lensfun/updates/version_1/mil-nikon.xml")
LENSFUN_FITTED = ('<distortion model="ptlens" focal="70" '
                  'a="0.00350093" b="0.01453356" c="0.00043983"/>')


def env_status():
    """Rig-environment probes for the Environment page — read-only checks of
    the machine-local state the pipeline depends on. States: ok | missing |
    stale | low | info; each with its evidence. The darktable styles need no
    probe: the undistort driver self-installs them per run."""
    import importlib.util
    import shutil
    home = os.path.expanduser("~")
    out = {}

    def put(name, state, why):
        out[name] = {"state": state, "why": why}

    for name in ("exiftool", "darktable-cli", "lensfun-update-data"):
        w = shutil.which(name)
        put(name, "ok" if w else "missing", w or "not on PATH")
    try:
        r = subprocess.run(["flatpak", "info", "org.siril.Siril"],
                           capture_output=True, text=True, timeout=15)
        ver = next((line.split(":", 1)[1].strip()
                    for line in r.stdout.splitlines()
                    if line.strip().lower().startswith("version")), "?")
        put("siril", "ok" if r.returncode == 0 else "missing",
            f"flatpak org.siril.Siril {ver}" if r.returncode == 0
            else "flatpak app org.siril.Siril not found")
    except Exception as e:
        put("siril", "missing", f"flatpak probe failed: {e}")
    put("astropy", "ok" if importlib.util.find_spec("astropy") else "missing",
        "importable by python3" if importlib.util.find_spec("astropy")
        else "not importable")
    p = os.path.join(home, ".local/share/astrometry-venv")
    put("astrometry-venv", "ok" if os.path.isdir(p) else "missing",
        p if os.path.isdir(p) else f"{p} absent (auto-bootstraps on first solve)")
    p = os.path.join(home, ".local/share/siril/siril_catalogues")
    n = len(os.listdir(p)) if os.path.isdir(p) else 0
    put("gaia-catalogs", "ok" if n else "missing",
        f"{n} catalog files at {p}" if n else f"none at {p}")
    p = os.path.join(home, ".local/bin/graxpert")
    put("graxpert", "ok" if os.path.exists(p) else "missing", p)
    if not os.path.exists(LENSFUN_DB):
        put("lensfun-model", "missing",
            f"{LENSFUN_DB} absent — run lensfun-update-data, then install_lens_model")
    else:
        xml = open(LENSFUN_DB).read()
        m = re.search(r"<lens>(?:(?!</lens>).)*?24-70mm f/4 S"
                      r"(?:(?!</lens>).)*?</lens>", xml, re.S)
        if not m:
            put("lensfun-model", "missing",
                "24-70mm f/4 S lens block absent from the updates DB")
        else:
            blk = m.group(0)
            fitted = LENSFUN_FITTED in blk
            stripped = "<vignetting" not in blk and "<tca" not in blk
            if fitted and stripped:
                put("lensfun-model", "ok",
                    "fitted focal=70 entry present; vignetting/tca stripped "
                    "— distortion-only holds")
            elif fitted:
                put("lensfun-model", "stale",
                    "fitted entry present but vignetting/tca NOT stripped — "
                    "re-run install_lens_model (lensfun-update-data overwrote the strip)")
            else:
                put("lensfun-model", "stale",
                    "fitted focal=70 entry absent (community or drifted line) "
                    "— run install_lens_model")
    du = shutil.disk_usage(REPO)
    free_gb = du.free / 2 ** 30
    put("disk", "ok" if free_gb >= 20 else "low",
        f"{free_gb:.0f}G free of {du.total / 2 ** 30:.0f}G "
        f"(undistort peaks need ~20G+)")
    put("darktable-styles", "info",
        "no probe needed: the undistort driver installs the pinned styles "
        "into <session>/work/dtcfg on every run; the install_styles button "
        "is manual verification only")
    return out


def stage_status(session):
    """Per-stage pipeline state for the Run page chips: done | running |
    todo | na, each with its evidence. Derived from products on disk (the
    session model) refined by this server session's job table. Stack-route
    stages share family evidence (per-set stacks on disk) unless a specific
    stage's job ran — product files cannot testify WHICH route built them."""
    m = session_model(session)
    if m is None:
        raise ValueError(f"no such session: {session}")
    lights = [s for s in m["sets"] if s.get("kind") == "lights"]
    jobs = {}
    with JOBS_LOCK:
        for j in JOBS.values():
            st = _job_refresh(j)
            prev = jobs.get(st["stage"])
            if st["status"] == "running" or prev is None:
                jobs[st["stage"]] = st["status"]
    choices = path_choices(session)
    masters = choices["masters"]
    have_dark = any(p.endswith("dark_master.fit") for p in masters)
    darks_staged = any(s["set"] == "darks" for s in m["sets"])
    flats_staged = any(s["set"] in ("flats", "calib")
                       or s["set"].startswith("flats_") for s in m["sets"])
    per_set_stacks = {s["set"]: [su for su in m["surfaces"]
                                 if su["sets"] == [s["set"]]] for s in lights}

    out = {}

    def put(name, state, why):
        if jobs.get(name) == "running":
            state, why = "running", "job running now"
        elif state == "todo" and jobs.get(name) == "done":
            state, why = "done", "completed via a run this server session"
        out[name] = {"state": state, "why": why}

    def missing(pred):
        return [s["set"] for s in lights if not pred(s)]

    if not lights:
        for name in STAGES:
            put(name, "na", "no light sets in this session")
        return out

    miss = missing(lambda s: s.get("frame_qa"))
    put("frame_qa", "done" if not miss else "todo",
        "frame_metrics.json on every light set" if not miss
        else f"missing for: {', '.join(miss)}")
    miss = missing(lambda s: s.get("anomaly"))
    all_tracked = bool(lights) and all(
        ((s.get("acquisition") or {}).get("mount")) == "tracked"
        for s in lights)
    if miss and all_tracked:
        put("anomaly_audit", "na",
            "cross-frame linking assumes a FIXED mount by design "
            "(anomaly_audit.py contract); every light set declares tracked")
    else:
        put("anomaly_audit", "done" if not miss else "todo",
            "anomaly_audit.json on every light set" if not miss
            else f"missing for: {', '.join(miss)}")
    if have_dark:
        put("master_dark", "done", "work/masters/dark_master.fit on disk")
    elif darks_staged:
        put("master_dark", "todo", "darks staged, no master yet")
    else:
        put("master_dark", "na", "no darks/ staged and no master")
    if flats_staged:
        put("sky_flat", "na", "real flats staged — matched-flat path applies")
    else:
        miss = [s["set"] for s in lights if not any(
            p.endswith(f"skyflat_{s['set']}.fit") for p in masters)]
        put("sky_flat", "done" if not miss else "todo",
            "per-set sky flat built for every light set" if not miss
            else f"missing for: {', '.join(miss)}")
    miss = [n for n, stacks in per_set_stacks.items() if not stacks]
    fam = ("done" if not miss else "todo",
           "per-set stacks on disk (family evidence — files cannot testify "
           "which route built them)" if not miss
           else f"no stack yet for: {', '.join(miss)}")
    for name in ("stack_standard", "stack_undistort", "stack_undistort_groups"):
        put(name, *fam)
    composed = [s for s in m["sets"] if s.get("kind") == "composed"]
    if composed:
        # the astrometric/photometric chain applies to the COMPOSED colour
        # product; mono member stacks skip SPCC (README: a mono set has no
        # colour to calibrate)
        have_stacks = [su for su in m["surfaces"]
                       if any(su["product"] == c["set"]
                              or su["product"].startswith(f"{c['set']}_")
                              for c in composed)]
        none_why = "waiting on the composed stack (mono member stacks skip SPCC)"
    else:
        have_stacks = [su for stacks in per_set_stacks.values()
                       for su in stacks]
        none_why = "no stacks to solve yet"
    if not have_stacks:
        put("solve", "todo", none_why)
        put("spcc", "todo", none_why)
        put("finish_render", "todo", none_why)
    else:
        nowcs = [su["product"] for su in have_stacks if not su["files"].get("wcs")]
        put("solve", "done" if not nowcs else "todo",
            "every per-set stack carries a WCS variant" if not nowcs
            else f"unsolved: {', '.join(nowcs)} — runs standalone OR inside finish_render (the one-shot)")
        nospcc = [su["product"] for su in have_stacks
                  if not su["files"].get("spcc")]
        put("spcc", "done" if not nospcc else "todo",
            "every per-set stack has an SPCC variant" if not nospcc
            else f"uncalibrated: {', '.join(nospcc)} — runs standalone OR inside finish_render (the one-shot)")
        nojudge = [su["product"] for su in have_stacks if not su["judge"]]
        put("finish_render", "done" if not nojudge else "todo",
            "judge surface for every per-set stack" if not nojudge
            else f"no judge surface: {', '.join(nojudge)}")
    put("spcc_cone", "na", "coverage check for a new field — run before "
                           "SPCC when the sky region changes")
    multi = [su for su in m["surfaces"] if len(su["sets"]) > 1]
    if multi:
        put("compose", "done",
            f"combine(s) on disk: {', '.join(su['product'] for su in multi)}")
    elif not choices["groupsets"]:
        put("compose", "na",
            "no group sub-stacks — this compose is the undistort-groups "
            "route's cross-set combine; a multi-filter target composes via "
            "compose_channels")
    else:
        put("compose", "todo" if not miss else "na",
            "group sub-stacks ready to compose" if not miss
            else "waiting on per-set stacks")

    comp_built, comp_ready, comp_wait = [], [], []
    for c in composed:
        members = list((((c.get("composition") or {}).get("members"))
                        or {}).values())
        if os.path.exists(os.path.join(REPO, "web", "results", session,
                                       f"stack_{c['set']}_comp.fit")):
            comp_built.append(c["set"])
        elif members and all(per_set_stacks.get(mn) for mn in members):
            comp_ready.append(c["set"])
        else:
            comp_wait.append(c["set"])
    if not composed:
        put("compose_channels", "na",
            "no composition record — single-stack session")
    elif comp_ready or comp_wait:
        put("compose_channels", "todo",
            (f"member stacks ready — compose: {', '.join(comp_ready)}"
             if comp_ready else "")
            + ("; " if comp_ready and comp_wait else "")
            + (f"waiting on member stacks for: {', '.join(comp_wait)}"
               if comp_wait else ""))
    else:
        put("compose_channels", "done",
            f"composed stack(s) on disk: {', '.join(comp_built)}")
    put("coverage_probe", "done" if m.get("coverage_maps") else
        ("todo" if multi else "na"),
        f"map(s) on disk: {', '.join(c['file'] for c in m['coverage_maps'])}"
        if m.get("coverage_maps")
        else ("compose exists — probe its coverage for framing" if multi
              else "no compose to map yet"))
    put("previews", "done" if m.get("previews_manifest") else "todo",
        "previews manifest on disk" if m.get("previews_manifest")
        else "no previews manifest yet")
    fr = m.get("framing") or []
    if not fr:
        put("verify_framing", "na", "no framing records drawn yet")
    else:
        unv = [f["product"] for f in fr if f.get("status") != "verified"]
        put("verify_framing", "done" if not unv else "todo",
            "every framing record verified" if not unv
            else f"unverified: {', '.join(map(str, unv))}")
    return out


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
                     "status": "running", "rc": None, "pid": proc.pid,
                     "started": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                     "ended": None, "log": os.path.relpath(log_path, REPO),
                     "_proc": proc, "_logf": log_f}
        _job_persist(JOBS[jid])
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
            if j["status"] != "done":
                j["tail"] = _log_tail(j)
            _job_persist(j)
    elif j.get("_adopted") and j["status"] == "running":
        # re-adopted from a previous server process: no Popen handle, so
        # liveness is the pid; if it is gone the exit code is unrecoverable
        if not _pid_alive(j.get("pid"), j.get("cmd")):
            j["status"] = "unknown"
            j["ended"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            j["tail"] = _log_tail(j)
            _job_persist(j)
    return _job_public(j)


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
        if j["status"] == "running" and (j.get("_proc") or j.get("pid")):
            pid = j["_proc"].pid if j.get("_proc") else j["pid"]
            try:
                os.killpg(os.getpgid(pid), signal.SIGTERM)
            except (ProcessLookupError, PermissionError):
                pass
        return _job_refresh(j)


def _load_jobs():
    """Re-adopt persisted job records on startup: finished ones for the list,
    still-running ones pid-checked so the one-at-a-time gate keeps holding
    across a server restart (start_new_session detaches the process group,
    so the run itself survives the server)."""
    try:
        names = sorted(os.listdir(WEBJOBS_DIR))
    except OSError:
        return
    for n in names:
        if not (n.startswith("j") and n.endswith(".json")):
            continue
        rec = _read_json(os.path.join(WEBJOBS_DIR, n))
        if not rec or not isinstance(rec, dict) or "id" not in rec:
            continue
        j = dict(rec)
        if j.get("status") == "running":
            j["_adopted"] = True
        JOBS[j["id"]] = j


_load_jobs()


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
        if self.path == "/favicon.ico":
            # no icon shipped; 204 answers the browser's automatic probe
            # without a 404 (and without the error-body write a hung-up
            # client turns into a BrokenPipe traceback)
            self.send_response(204)
            self.send_header("Content-Length", "0")
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
        if self.path.startswith("/api/paths/"):
            try:
                return self._json(200, path_choices(
                    _safe(self.path[len("/api/paths/"):], "session")))
            except ValueError as e:
                return self._json(400, {"error": str(e)})
        if self.path.startswith("/api/status/"):
            try:
                return self._json(200, stage_status(
                    _safe(self.path[len("/api/status/"):], "session")))
            except ValueError as e:
                return self._json(400, {"error": str(e)})
        if self.path == "/api/env":
            return self._json(200, env_status())
        if self.path == "/api/version":
            return self._json(200, {"rev": SERVER_REV,
                                    "started": SERVER_STARTED})
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


class Server(ThreadingHTTPServer):
    def handle_error(self, request, client_address):
        # A client closing its socket mid-response (tab closed, favicon
        # probe abandoned) surfaces as BrokenPipe/ConnectionReset in the
        # handler thread — client behavior, not a server fault. Suppress
        # only those; every other error stays loud.
        exc = sys.exc_info()[0]
        if exc is not None and issubclass(exc, (BrokenPipeError,
                                                ConnectionResetError)):
            return
        super().handle_error(request, client_address)


def main():
    port = 8321
    for a in sys.argv[1:]:
        if a.startswith("--port="):
            port = int(a.split("=", 1)[1])
    srv = Server(("127.0.0.1", port), Handler)
    print(f"[serve] http://127.0.0.1:{port}/web/index.html  (root: {REPO})")
    print("[serve] local-only; Ctrl-C to stop")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
