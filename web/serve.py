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
import sys
import time
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_+.-]*$")  # no /, no leading dot


def _safe(name, what):
    if not isinstance(name, str) or not NAME_RE.match(name) or ".." in name:
        raise ValueError(f"unsafe {what}: {name!r}")
    return name


def sessions_inventory():
    root = os.path.join(REPO, "web", "results")
    out = []
    if not os.path.isdir(root):
        return out
    for s in sorted(os.listdir(root)):
        sdir = os.path.join(root, s)
        if not os.path.isdir(sdir) or s.startswith("."):
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
    if not (os.path.isdir(droot) or os.path.isdir(rroot)):
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
        return super().do_GET()

    def do_POST(self):
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
