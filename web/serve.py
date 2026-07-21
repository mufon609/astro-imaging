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
