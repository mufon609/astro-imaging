#!/usr/bin/env python3
"""The portion-rule stage's measuring, planning and checking half (run_member_crop.sh
is the orchestrating half). Four subcommands, none of which touches an original:

  member_profile.py profile  <member.fit>... --out=<profiles.json> --work=<dir>
                             --stations=<px,px,...> --radius=<px> --top=<n>
                             [--cache=<tracked json>]
      Siril findstar at star_stations.py's own stations on every member — the
      centre and along +-<stations> px at the given radius, the open gate
      star_stations uses; the tool's per-star lists are KEPT under <work>/;
      per station the top-N-by-amplitude median of (FWHMx+FWHMy)/2 and of the
      min/max roundness (shape_at_sky's statistic). A station whose box does not
      fit is clamped inward by <= 300 px (the shift recorded) or SKIPPED. One
      Siril run per member through scripts/lib/siril_run (the flatpak lock).
      THE CACHE (--cache, tracked: datasets/corpus/member_selection/profiles.json):
      keyed by the member's canonical (real) path; an entry is REUSED only when
      the member's content sha256 AND the measuring geometry (stations/radius/
      top-N) both match — a geometry change re-profiles, because a profile at
      other stations answers a different question. A run profiles only new or
      changed members and SAYS which; an all-hit run never invokes Siril and
      leaves the cache file byte-identical. Station lists ('lst') are kept by
      the RUN that profiled the member; a cache hit's lists live where that run
      kept them and may be gone if its work dir was scratch.
  member_profile.py plan     --profiles=<json> --members=<list> --bar=<px>
                             --half-width=<px> --record=<json> --curated=<dir>
                             [--ref=<member>] [--allow-ref-crop] [--tag=<name>]
                             --plan=<json>
      Applies THE RULE, computes S_i, writes the tracked record and the crop
      plan. Station geometry (stations/radius/top-N) is read from the PROFILES
      file's own metadata — the rule can only be applied at the stations that
      were measured.
  member_profile.py verify   --plan=<json> --record=<json>
      Per-copy assertions after the Siril crops (below), written into the record.
      SIP IS ASSERTED TWO WAYS, NEVER BY EXACT EQUALITY (ruled after the GO #17B
      acceptance): (1) key sets and orders identical AND every coefficient equal
      to a RELATIVE tolerance of 1e-12 — MEASURED on this rig: Siril 1.4.4's
      crop+save writes SIP values at 15 significant digits, so 36 of 1107
      coefficients across 27 real cropped copies moved, none by more than
      4.49e-15 relative; 1e-12 is a thousandfold margin over that and a
      millionfold below any change a re-solve or a wrong crop makes; (2) the
      PHYSICAL assertion: pixel->world agreement between the original's WCS and
      the copy's at 5 kept-region points < 1e-9 deg (measured max 4.41e-13; at
      16.97"/px the bar is 2e-7 px). Exact equality was the criterion until 17B:
      it flagged 23/27 copies that are byte-identical in data to the
      owner-approved cropT copies, which carry the same re-serialized values and
      had passed a KEYS-level check that never measured values. MEMCROP, CRPIX/
      CRVAL and the matrix-form checks stay exact.
  member_profile.py fixtures --out=<dir>
      The selftest's synthetic members + their profile table, a cache seeded
      with their real sha256s, and a selftest recipe (no Siril).

THE RULE (the asymmetry rule, cropT — owner-approved, ledger lines 111/112/114):
  per member, onset = the smallest station dx where FWHM(+dx) - FWHM(-dx) > bar
  and stays above it outward; x_c = onset - half_width; the entry-side columns
  beyond round(W/2 + x_c) are removed from a COPY; a member with no station over
  the bar is untouched (a symlink). +x is the ENTRY side on every member of this
  corpus (RA rises with x; GO #6) — the side the lens's night-dependent
  asymmetric term smears (GO #7/#8).
  THE CONSTANTS (bar, stations, radius, top-N, half-width) live in
  datasets/corpus/recipe.json (member_selection.portion_rule) and arrive here as
  arguments — never hard-coded in this file; run_member_crop.sh loads and echoes
  them, and its --bar/--half-width override the recipe aloud.
  MEASURED WHY: on the 77-member corpus the band x10-x25 went 2.967/2.935/2.925/2.877
  -> 2.790/2.805/2.810/2.792 px at the canonical's depth and interior, no seam at
  any of the 27 crop boundaries (cropT_arm.json); the frame-level threshold on top
  of it was a NULL (cropTselT_arm.json, GO #16).
  S_i = mean of the top-N FWHM over the centre + exit-side stations (the
  interior) is REPORTED beside the rule as an ADVISORY only: GO #16 measured
  that dropping the 13 members with S_i > p25 + 0.20 whole changed no station by
  more than 0.024 px against cropT — their degrading part was the entry-side
  zone the portion rule had already taken. Not a gate.
  SKIPPED STATIONS VETO THE TAIL (ruled): the onset requires the asymmetry above
  the bar at EVERY station from the onset outward, and a station skipped for
  width reads as not-above — conservative: no crop on incomplete outward
  evidence. Every skip is WARNED aloud (member, stations, consequence); on this
  corpus every member (5828-5832 px wide) fits all stations unclamped, and the
  selftest's first shipped fixtures (3600 px) are the measured cost of ignoring
  the bound.
  THE REFUTED FORM, kept as the selftest's negative: an intrinsic gradient
  FWHM(+dx) - FWHM(centre) > bar trips on 66/77 members' entry side AND 67/77
  exit side — it measures the lens's radial term, present on both sides — so a
  member with a SYMMETRIC rise on both sides must NOT crop under this rule.
  CENTRE-ROW ONLY, AND MEASURED TO STAY SO: every station sits on the member's
  centre row; a member soft in its top/bottom rows passes. The rows were profiled
  (datasets/corpus/smear_attribution/row_profiles.json): the bottom row crosses the
  bar ~600 px earlier on 5/5 cropped members, and the row-resolved crop (x_c = min
  over rows, rowmin_arm.json) was a clean NULL at the corners it aimed at (probes
  −0.004..−0.033 px, corners <= 0.02, +1.2 % pixel-frames); the top row's SYMMETRIC
  0.4–0.5 px softness on the soft nights is the open case (blind by design).
  THE PINNED REFERENCE is refused for cropping unless --allow-ref-crop is given,
  and then the crop is said aloud: the compose's zero point is the reference's own
  IKSS location/scale (ANCLOC), and a cropped anchor is untested.

WHAT IS IN-HOUSE HERE. Every star is Siril findstar's; every crop, save and
MEMC* key is Siril's (crop / update_key / save, the .ssf run_member_crop.sh
writes); the rule, the medians, the sha256 bookkeeping and the record are
bookkeeping over the tool's numbers; `verify` READS pixels of the copy and the
original to assert identity — a diagnostic read (CLAUDE.md: diagnostics are not
the bright line), never a write. MEMCPROV (a path) is applied with
header_apply_keys (astropy fits.setval), not Siril update_key, because Siril
cuts a string value at `/` (stamp_headers.sh).

SCOPE: the corpus combine (run_corpus_combine.sh --portion-rule). The per-set
finals are not run through it until measured there: within one night the rule
crops every member alike, and the gain exists only where another member's better
columns cover the same sky.

SELFTEST COVERAGE (run_member_crop.sh --selftest): rule -> plan -> record ->
Siril crop + stamp -> verify on synthetic members with a PRE-WRITTEN profile
table (--profiles), plus the CACHE-HIT path (a seeded cache serves every member:
0 profiled, no findstar, verdicts identical). The SIP criterion has a positive
control in each direction: the fixture carries 17-significant-digit coefficients
that do NOT round-trip through Siril's 15-digit writer, so the crop re-serializes
them (the real-member effect: 36/1107 values moved <= 4.49e-15 on the 27
cropT/17B copies) and verify MUST pass with max_rel_sip > 0; and a NEGATIVE
copy with one coefficient altered by 1e-6 relative (the change a re-solve or a
wrong crop makes) MUST fail both assertions. Exercised at GO #17B on the real
77 (identity + determinism held), not by the selftest: `profile`'s Siril
findstar leg and the cache MISS-then-write path.

REMOVAL CONDITION: retire when Siril's compose accepts per-member weight maps or
a per-member region mask (a mask is the crop without the coverage cost).
"""
import hashlib
import json
import os
import statistics
import sys

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(REPO, "scripts", "qa"))
sys.path.insert(0, os.path.join(REPO, "scripts", "lib"))
T0_REQUIRED = ("DISTMODL", "DISTA", "DISTB", "DISTC", "DISTNORM", "DISTPROV", "DISTSRC", "CALSET",
               "BKGLIGHT", "STACKCNT", "EXPTIME", "LIVETIME", "FOCALLEN", "XPIXSZ", "DATE-OBS", "INSTRUME")
SIP_REL_TOL = 1e-12        # verify's coefficient tolerance: 1000x the measured 4.49e-15 re-serialization (docstring)
SKY_SEP_TOL_DEG = 1e-9     # verify's physical bar: pixel->world agreement at 5 kept-region points (2e-7 px at 16.97"/px)


def sky_sep_deg(hi, ho):
    """Max pixel->world separation (deg) between the original's WCS and the copy's at the copy's
    four corners + centre (1-based FITS pixels; the crop starts at 0 0 so pixel frames coincide,
    which the CRPIX check asserts separately). Diagnostic astropy read of headers only."""
    import warnings
    import numpy as np
    from astropy.wcs import WCS
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        wi, wo = WCS(hi, naxis=2), WCS(ho, naxis=2)
    W, H = int(ho["NAXIS1"]), int(ho["NAXIS2"])
    pts = np.array([[1, 1], [W, 1], [1, H], [W, H], [W / 2.0, H / 2.0]], float)
    si, so = wi.all_pix2world(pts, 1), wo.all_pix2world(pts, 1)
    return float(np.hypot((si[:, 0] - so[:, 0]) * np.cos(np.radians(si[:, 1])), si[:, 1] - so[:, 1]).max())


def opts_of(argv):
    o = {}
    pos = []
    for a in argv:
        if a.startswith("--") and "=" in a:
            k, v = a[2:].split("=", 1); o[k] = v
        elif a.startswith("--"):
            o[a[2:]] = True
        else:
            pos.append(a)
    return o, pos


def need(o, cmd, *keys):
    for k in keys:
        if k not in o:
            sys.exit(f"{cmd}: --{k}= is required")


def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


# ---------------------------------------------------------------- profile
def stations_for(W, H, r, dxs):
    """star_stations' geometry — the centre and along +-dx boxes on the centre row —
    with GO #13's clamp rule: a box past the edge is shifted inward by <= 300 px
    (the shift recorded) or skipped."""
    cx, cy = W / 2.0, H / 2.0
    out = [{"name": "centre", "dx": 0.0, "box": [int(round(cx - r)), int(round(cy - r)), 2 * r, 2 * r], "shift_px": 0}]
    for d in dxs:
        for sgn, nm in ((1, "along+"), (-1, "along-")):
            dx = sgn * d; x = int(round(cx + dx - r)); y = int(round(cy - r)); shift = 0
            if x < 0:
                shift = -x; x = 0
            if x + 2 * r > W:
                shift = (x + 2 * r) - W; x = W - 2 * r
            if shift > 300:
                out.append({"name": f"{nm}{d}", "dx": float(dx), "skipped": f"does not fit: needs a {shift}-px inward clamp"}); continue
            out.append({"name": f"{nm}{d}", "dx": float(dx - sgn * shift), "dx_nominal": float(dx), "box": [x, y, 2 * r, 2 * r], "shift_px": shift})
    return out


def read_rows(path):
    rows = []
    with open(path) as f:
        for line in f:
            if line.startswith("#"):
                continue
            p = line.split()
            if len(p) < 13:
                continue
            rows.append((float(p[3]), float(p[7]), float(p[8])))   # A, FWHMx, FWHMy
    return rows


def profile(members, o):
    from astropy.io import fits
    need(o, "profile", "out", "work", "stations", "radius", "top")
    work = os.path.abspath(o["work"])
    dxs = tuple(int(x) for x in str(o["stations"]).split(",") if x)
    r = int(o["radius"]); top = int(o["top"])
    geo = {"stations_px": list(dxs), "radius_px": r, "top_n": top}
    cache_path = o.get("cache")
    cache = {"members": {}}
    if cache_path and os.path.exists(cache_path):
        cache = json.load(open(cache_path))
        cache.setdefault("members", {})
    res = {}; profiled = []; reused = []
    for m in members:
        m = os.path.realpath(m)
        sha = sha256_of(m)
        ent = cache["members"].get(m)
        if ent and ent.get("sha256") == sha and ent.get("geometry") == geo:
            res[m] = {"wh": ent["wh"], "stackcnt": ent.get("stackcnt"), "stations": ent["stations"]}
            reused.append(os.path.basename(m))
            print(f"  [profile] cached  {os.path.basename(m)} (sha+geometry match)")
            continue
        import star_stations as ss   # lazy: an all-hit run never touches Siril
        wd = os.path.join(work, os.path.basename(m)[:-4]); os.makedirs(wd, exist_ok=True)
        W, H = ss.image_dims(m, wd)
        sts = stations_for(W, H, r, dxs)
        live = [s for s in sts if "skipped" not in s]
        ss.measure(m, wd, live)                       # Siril crop + findstar per station; lists stay in wd
        for s in live:
            rows = read_rows(os.path.join(wd, f"{s['name']}.lst"))
            bright = sorted(rows, key=lambda t: -t[0])[:top]
            s["top30_fwhm"] = round(statistics.median((t[1] + t[2]) / 2 for t in bright), 3) if bright else None
            s["top30_round"] = round(statistics.median(min(t[1], t[2]) / max(t[1], t[2]) for t in bright), 3) if bright else None
            s["top_n"] = len(bright)
            s["lst"] = os.path.relpath(os.path.join(wd, f"{s['name']}.lst"), REPO)
        h = fits.getheader(m)
        res[m] = {"wh": [W, H], "stackcnt": int(h.get("STACKCNT", 0)), "stations": sts}
        cache["members"][m] = {"sha256": sha, "geometry": geo, **res[m]}
        profiled.append(os.path.basename(m))
        print(f"  [profile] {os.path.basename(m)} {W}x{H} " + " ".join(f"{s['name']}={s.get('top30_fwhm')}" for s in sts if "skipped" not in s and (s["name"] == "centre" or s["name"].startswith("along+"))))
    if cache_path and profiled:
        cache["_what"] = ("PER-MEMBER PROFILE CACHE (member_profile.py profile): keyed by the member's canonical path; "
                          "an entry is reused only when content sha256 AND geometry (stations/radius/top-N) match — a "
                          "geometry change re-profiles. 'lst' paths are the profiling run's own kept lists and may be "
                          "gone if that run's work dir was scratch; the station numbers here are the durable part.")
        os.makedirs(os.path.dirname(os.path.abspath(cache_path)), exist_ok=True)
        json.dump(cache, open(cache_path, "w"), indent=1)
    inst = ("Siril findstar via star_stations geometry (gate 'setfindstar reset -roundness=0.05 -sigma=0.5 -relax=on'), "
            f"centre and along +-{'/'.join(str(d) for d in dxs)} at radius {r}, "
            f"top-{top}-by-amplitude median of (FWHMx+FWHMy)/2 and min/max roundness; lists kept")
    json.dump({"instrument": inst, "stations_px": list(dxs), "radius_px": r, "top_n": top,
               "cache": os.path.abspath(cache_path) if cache_path else None,
               "profiled": profiled, "cached": reused, "members": res}, open(o["out"], "w"), indent=1)
    print(f"  [profile] {len(profiled)} profiled" + (f" ({', '.join(profiled)})" if profiled else "")
          + f", {len(reused)} cached" + (f" ({', '.join(reused)})" if reused else ""))
    return res


# ---------------------------------------------------------------- the rule
def apply_rule(stations, bar, half_width, dxs):
    st = {s["name"]: s for s in stations}
    def f(n):
        s = st.get(n); return None if s is None or "skipped" in s else s.get("top30_fwhm")
    entry = {d: f(f"along+{d}") for d in dxs}; exit_ = {d: f(f"along-{d}") for d in dxs}
    asym = {d: (round(entry[d] - exit_[d], 3) if entry[d] is not None and exit_[d] is not None else None) for d in dxs}
    onset = None
    for i, d in enumerate(dxs):
        tail = [asym[dd] for dd in dxs[i:]]
        if all(a is not None and a > bar for a in tail):
            onset = d; break
    xc = onset - half_width if onset else None
    interior = [f("centre")] + [exit_[d] for d in dxs]
    S = round(sum(v for v in interior) / len(interior), 4) if all(v is not None for v in interior) else None
    return {"centre": f("centre"), "entry": {str(d): entry[d] for d in dxs}, "exit": {str(d): exit_[d] for d in dxs},
            "asymmetry": {str(d): asym[d] for d in dxs}, "onset": onset, "x_c": xc, "cropped": xc is not None, "S_advisory": S,
            "clamps": {s["name"]: s.get("shift_px") for s in stations if s.get("shift_px")}, "skipped": [s["name"] for s in stations if "skipped" in s]}


def canonical_name(i, path):
    """sub_NNN_<night>_<set>_<sub>.fit — the curated-dir name the compose links in canonical order."""
    parts = os.path.abspath(path).split("/")
    night = parts[-4]; st = parts[-2].replace("groups_", ""); sub = parts[-1][:-4]
    return f"sub_{i:03d}_{night}_{st}_{sub}.fit"


def plan(o):
    need(o, "plan", "profiles", "members", "bar", "half-width", "record", "curated", "plan")
    meta = json.load(open(o["profiles"]))
    prof = meta["members"]
    dxs = tuple(int(x) for x in meta["stations_px"])
    radius = int(meta["radius_px"]); top = int(meta["top_n"])
    members = [l.strip() for l in open(o["members"]) if l.strip()]
    bar = float(o["bar"]); hw = int(o["half-width"]); tag = o.get("tag", "portion")
    ref = os.path.realpath(o["ref"]) if o.get("ref") else None
    rows = {}; actions = []; n_crop = 0
    for i, m in enumerate(members, 1):
        key = os.path.abspath(m); real = os.path.realpath(m)
        p = prof.get(key) or prof.get(real)
        if p is None:
            sys.exit(f"plan: no profile for {m}")
        r = apply_rule(p["stations"], bar, hw, dxs)
        W, H = p["wh"]
        name = canonical_name(i, real) if "/groups_" in real else f"sub_{i:03d}_{os.path.basename(real)}"
        if r["skipped"]:
            print(f"WARNING: {name}: station(s) {', '.join(r['skipped'])} SKIPPED (box does not fit the {W}-px member width) — "
                  "the outward tail containing a skipped station can never satisfy the rule there; conservative: "
                  "no crop on incomplete outward evidence", file=sys.stderr)
        row = {"index": i, "member": real, "name": name, "wh": [W, H], "stackcnt": p.get("stackcnt"), **r}
        if r["cropped"]:
            w = int(round(W / 2.0 + r["x_c"]))
            row.update({"kept_width": w, "removed_columns": W - w, "removed_fraction": round((W - w) / W, 3)})
            if ref and real == ref:
                if not o.get("allow-ref-crop"):
                    msg = (f"REFUSED: the pinned reference {real} would be cropped by the rule (onset +{r['onset']}, x_c {r['x_c']}); "
                           "the compose's zero point is the reference's own sky and a cropped anchor is untested — pass --allow-ref-crop to proceed, and say so in the record")
                    print(msg, file=sys.stderr); sys.exit(3)
                print(f"WARNING: the pinned reference {real} IS CROPPED by the rule (onset +{r['onset']}, x_c {r['x_c']}) — allowed by --allow-ref-crop; the anchor's IKSS statistics change with its columns", file=sys.stderr)
                row["reference_cropped_allowed"] = True
            n_crop += 1
        actions.append({"name": name, "src": real, "action": "crop" if r["cropped"] else "symlink", "W": W, "H": H,
                        "kept_width": row.get("kept_width"), "x_c": r["x_c"], "S_advisory": r["S_advisory"], "is_reference": bool(ref and real == ref)})
        rows[name] = row
    p25 = None
    Ss = [r["S_advisory"] for r in rows.values() if r["S_advisory"] is not None]
    if Ss:
        s = sorted(Ss); k = 0.25 * (len(s) - 1); lo = int(k); p25 = round(s[lo] + (s[min(lo + 1, len(s) - 1)] - s[lo]) * (k - lo), 4)
    record = {"id": f"member_selection_{tag}", "stage": "run_member_crop.sh — the portion rule (asymmetry) as a chain stage; member_profile.py plan",
              "rule": {"form": "asymmetry", "bar_px": bar, "stations_px": list(dxs), "radius_px": radius, "top_n": top, "half_width_px": hw,
                       "text": "onset = smallest dx where FWHM(+dx) - FWHM(-dx) > bar and stays above outward; x_c = onset - half_width; entry-side columns beyond round(W/2 + x_c) removed from a copy; no station over the bar -> untouched; a station skipped for width vetoes the tail (no crop on incomplete outward evidence)"},
              "advisory_S": {"definition": "mean of the top-N FWHM over the centre + exit-side stations (interior) — REPORTED, not a gate (GO #16: the frame-level threshold on top of the portion rule was a NULL)", "p25": p25},
              "instrument": meta.get("instrument"), "profiles": o["profiles"], "profile_cache": meta.get("cache"), "reference": ref,
              "members": len(members), "cropped": n_crop, "untouched": len(members) - n_crop,
              "x_c_histogram": {str(x): sum(1 for r in rows.values() if r["cropped"] and r["x_c"] == x) for x in sorted({r["x_c"] for r in rows.values() if r["cropped"]})},
              "table": rows, "curated_dir": os.path.abspath(o["curated"]), "curated_listing": None, "verified": None}
    json.dump(record, open(o["record"], "w"), indent=1)
    json.dump({"bar": bar, "half_width": hw, "record": os.path.abspath(o["record"]), "curated": os.path.abspath(o["curated"]), "actions": actions}, open(o["plan"], "w"), indent=1)
    print(f"  [plan] {len(members)} members: {n_crop} to crop ({record['x_c_histogram']}), {len(members) - n_crop} untouched; p25(S) {p25}; record -> {o['record']}")


# ---------------------------------------------------------------- verify
def verify(o):
    import numpy as np
    from astropy.io import fits
    need(o, "verify", "plan", "record")
    plan_ = json.load(open(o["plan"])); rec = json.load(open(o["record"]))
    D = plan_["curated"]; fails = []; listing = {}
    for a in plan_["actions"]:
        dst = os.path.join(D, a["name"])
        if a["action"] == "symlink":
            ok = os.path.islink(dst) and os.path.realpath(dst) == a["src"]
            h = fits.getheader(dst) if ok else None
            if ok and any(k in h for k in ("MEMCROP", "MEMCRULE", "MEMCPROV", "MEMCSCOR")):
                ok = False; fails.append(f"{a['name']}: an untouched member carries MEMC* keys")
            if not ok and not fails:
                fails.append(f"{a['name']}: symlink missing or pointing elsewhere")
            listing[a["name"]] = {"symlink_to": a["src"], "ok": ok}; continue
        hi = fits.getheader(a["src"]); ho = fits.getheader(dst)
        W = a["kept_width"]; checks = {}
        checks["naxis1==kept_width"] = ho["NAXIS1"] == W and ho["NAXIS2"] == hi["NAXIS2"] and ho.get("NAXIS3") == hi.get("NAXIS3")
        checks["bitpix-32"] = ho["BITPIX"] == -32
        checks["CRPIX/CRVAL unchanged"] = all(abs(float(ho[k]) - float(hi[k])) < 1e-6 for k in ("CRPIX1", "CRPIX2", "CRVAL1", "CRVAL2"))
        sipk = lambda h: sorted(k for k in h if k[:2] in ("A_", "B_", "AP", "BP"))
        ks = sipk(hi); same_keys = ks == sipk(ho)
        same_orders = same_keys and all(int(hi[k]) == int(ho[k]) for k in ks if k.endswith("ORDER"))
        rel = lambda a, b: (abs(a - b) / max(abs(a), abs(b))) if (a or b) else 0.0
        max_rel = max((rel(float(hi[k]), float(ho[k])) for k in ks if not k.endswith("ORDER")), default=0.0) if same_keys else None
        checks["SIP keys/orders identical, values within 1e-12 rel"] = same_orders and max_rel is not None and max_rel <= SIP_REL_TOL
        sky = sky_sep_deg(hi, ho)
        checks["pixel->world agreement < 1e-9 deg"] = sky < SKY_SEP_TOL_DEG
        checks["T0 provenance keys present"] = all(k in ho for k in T0_REQUIRED if k in hi)
        checks["single matrix form"] = ("CD1_1" in ho) != ("CDELT1" in ho)
        checks["MEMCROP==x_c"] = int(ho.get("MEMCROP", -999)) == int(a["x_c"])
        checks["MEMCRULE present"] = str(ho.get("MEMCRULE", "")).startswith("asym>")
        checks["MEMCPROV present"] = bool(ho.get("MEMCPROV"))
        checks["MEMCSCOR==S"] = abs(float(ho.get("MEMCSCOR", -999)) - float(a["S_advisory"])) < 1e-3 if a["S_advisory"] is not None else True
        di = fits.getdata(a["src"]); do = fits.getdata(dst)          # diagnostic READ of both
        checks["kept pixels identical"] = np.array_equal(di[..., :W], do)
        ok = all(checks.values())
        if not ok:
            fails.append(f"{a['name']}: " + ", ".join(k for k, v in checks.items() if not v))
        listing[a["name"]] = {"cropped_copy_of": a["src"], "kept_width": W, "ok": ok, "checks": checks, "max_rel_sip": max_rel, "max_sky_sep_deg": sky}
    copies = [v for v in listing.values() if "checks" in v]
    rec["curated_listing"] = listing; rec["verified"] = not fails; rec["verify_failures"] = fails
    rec["verify_criterion"] = {"sip_rel_tol": SIP_REL_TOL, "sky_sep_tol_deg": SKY_SEP_TOL_DEG,
                               "text": "SIP: key sets + orders identical and every coefficient within 1e-12 relative (Siril 1.4.4 re-serializes at 15 significant digits, measured max 4.49e-15); pixel->world agreement at the copy's 4 corners + centre < 1e-9 deg (measured max 4.41e-13); MEMCROP/CRPIX/CRVAL/matrix form exact; kept pixels identical"}
    rec["verify_max_rel_sip"] = max((v["max_rel_sip"] for v in copies if v["max_rel_sip"] is not None), default=0.0)
    rec["verify_max_sky_sep_deg"] = max((v["max_sky_sep_deg"] for v in copies), default=0.0)
    json.dump(rec, open(o["record"], "w"), indent=1)
    print(f"  [verify] {len(listing)} entries, failures {len(fails)}; max_rel_sip {rec['verify_max_rel_sip']:.2e}, max_sky_sep {rec['verify_max_sky_sep_deg']:.2e} deg" + (": " + "; ".join(fails) if fails else ""))
    sys.exit(0 if not fails else 2)


# ---------------------------------------------------------------- fixtures (selftest)
def fixtures(o):
    import numpy as np
    from astropy.io import fits
    need(o, "fixtures", "out")
    out = os.path.abspath(o["out"]); d = os.path.join(out, "groups_set-01"); os.makedirs(d, exist_ok=True)
    # W >= 5600 REQUIRED: at the corpus stations (max dx 2400, radius 400) a narrower
    # member SKIPS outer stations (the clamp bound is 300 px), and a skipped station
    # vetoes the rule's tail — the first shipped fixtures (3600 px) skipped +-1800
    # AND +-2400, so the planted onset at +1800 could never fire and the whole
    # selftest passed vacuously green paths and red everything else. 5600 is the
    # zero-clamp bound; real members run 5828-5832 px.
    W, H = 6000, 200
    # The planted scenario's own geometry — mirrors datasets/corpus/recipe.json today
    # and is written into fx recipe.json/profiles.json/cache.json below, so the
    # selftest is hermetic: it exercises the stage AS CONFIGURED BY ITS OWN files,
    # not whatever the tracked recipe says this week.
    FXDX = (600, 1200, 1800, 2400); FXR = 400; FXTOP = 30
    rng = np.random.default_rng(7)
    def header():
        h = fits.Header()
        for k, v in {"CTYPE1": "RA---TAN-SIP", "CTYPE2": "DEC--TAN-SIP", "CRVAL1": 310.0, "CRVAL2": 43.0, "CRPIX1": W / 2, "CRPIX2": H / 2,
                     "CD1_1": 0.0047, "CD1_2": -0.0012, "CD2_1": -0.0012, "CD2_2": -0.0047, "EQUINOX": 2000.0,
                     # SIP written DENSE (every coefficient for i+j <= order, zeros explicit):
                     # MEASURED on this rig's Siril 1.4.4 — crop+save densifies a sparse
                     # SIP grid (adds the 0.0 terms) while round-tripping the nonzero
                     # terms exactly, so a sparse fixture fails "SIP unchanged" for the
                     # tool's reason, not the stage's. Real members are dense already
                     # (their headers are Siril products; GO #12/#13 measured SIP
                     # identical through the same crop).
                     # ... and with 17-significant-digit coefficients that do NOT round-trip through
                     # Siril's 15-digit SIP writer (AP_0_0 is the measured real-member value, GO #17B):
                     # the crop MUST re-serialize them, so verify's tolerance criterion is EXERCISED by
                     # the positive case — a fixture whose values round-trip would test nothing, and
                     # the selftest asserts max_rel_sip > 0 on the cropped copy.
                     "A_ORDER": 2, "A_0_0": 0.0, "A_0_1": 0.0, "A_0_2": -2.3456789012345678e-7, "A_1_0": 0.0, "A_1_1": 0.0, "A_2_0": 1.2345678901234567e-6,
                     "B_ORDER": 2, "B_0_0": 0.0, "B_0_1": 0.0, "B_0_2": 1.0987654321098765e-7, "B_1_0": 0.0, "B_1_1": 0.0, "B_2_0": 2.3456789012345679e-7,
                     "AP_ORDER": 2, "AP_0_0": -0.01198645646714617, "AP_0_1": 0.0, "AP_0_2": 0.0, "AP_1_0": 0.0, "AP_1_1": 0.0, "AP_2_0": -1.1234567890123456e-7,
                     "BP_ORDER": 2, "BP_0_0": 0.0, "BP_0_1": 0.0, "BP_0_2": -1.3456789012345678e-7, "BP_1_0": 0.0, "BP_1_1": 0.0, "BP_2_0": 0.0,
                     "DISTMODL": "ptlens", "DISTA": 0.005185, "DISTB": 0.010655, "DISTC": 0.004969, "DISTNORM": "half-diagonal", "DISTPROV": "stamped",
                     "DISTSRC": "selftest", "CALSET": "selftest/set-01", "BKGLIGHT": "none", "STACKCNT": 100, "EXPTIME": 2.5, "LIVETIME": 250.0,
                     "FOCALLEN": 70.0, "XPIXSZ": 5.94, "DATE-OBS": "2026-08-29T00:00:00", "INSTRUME": "selftest"}.items():
            h[k] = v
        return h
    for name in ("sub_01", "sub_02", "sub_03"):
        data = rng.normal(0.001, 0.0001, (3, H, W)).astype(np.float32)
        fits.PrimaryHDU(data, header=header()).writeto(os.path.join(d, f"{name}.fit"), overwrite=True)
    # profile tables (no Siril): sub_01 = PLANTED — asymmetry crosses the bar at +1800 and stays -> onset 1800, x_c 1500;
    # sub_02 = FLAT; sub_03 = SYMMETRIC rise on both sides (the refuted intrinsic form's victim) -> must NOT crop
    def prof(centre, entry, exit_):
        sts = stations_for(W, H, FXR, FXDX)
        vals = {"centre": centre}
        for d_, e, x in zip(FXDX, entry, exit_):
            vals[f"along+{d_}"] = e; vals[f"along-{d_}"] = x
        for s in sts:
            if "skipped" in s: continue
            s["top30_fwhm"] = vals[s["name"]]; s["top30_round"] = 0.9; s["top_n"] = FXTOP
        return {"wh": [W, H], "stackcnt": 100, "stations": sts}
    members = {os.path.realpath(os.path.join(d, "sub_01.fit")): prof(2.40, [2.45, 2.55, 2.90, 3.05], [2.45, 2.50, 2.55, 2.60]),
               os.path.realpath(os.path.join(d, "sub_02.fit")): prof(2.40, [2.42, 2.45, 2.50, 2.55], [2.42, 2.45, 2.50, 2.55]),
               os.path.realpath(os.path.join(d, "sub_03.fit")): prof(2.40, [2.70, 3.00, 3.20, 3.40], [2.70, 3.00, 3.20, 3.40])}
    geo = {"stations_px": list(FXDX), "radius_px": FXR, "top_n": FXTOP}
    json.dump({"instrument": "SELFTEST planted profile table (no Siril)", **geo, "cache": None,
               "members": members}, open(os.path.join(out, "profiles.json"), "w"), indent=1)
    json.dump({"_what": "SELFTEST seeded profile cache: real sha256s of the fixture members + the planted stations",
               "members": {m: {"sha256": sha256_of(m), "geometry": geo, **p} for m, p in members.items()}},
              open(os.path.join(out, "cache.json"), "w"), indent=1)
    json.dump({"member_selection": {"portion_rule": {
        "bar_px": 0.20, "stations_px": list(FXDX), "radius_px": FXR, "top_n": FXTOP, "half_width_px": 300,
        "instrument": "SELFTEST planted profile table (no Siril)",
        "rule": "selftest copy of the corpus rule — the real constants live in datasets/corpus/recipe.json",
        "provenance": "member_profile.py fixtures"}}}, open(os.path.join(out, "recipe.json"), "w"), indent=1)
    with open(os.path.join(out, "members.txt"), "w") as f:
        f.write("\n".join(sorted(members)) + "\n")
    print(f"  [fixtures] 3 synthetic members ({W}x{H}x3, WCS TAN-SIP + T0 keys) + profiles.json + cache.json + recipe.json under {out}")


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    cmd = sys.argv[1]; o, pos = opts_of(sys.argv[2:])
    if cmd == "profile":
        profile(pos, o)
    elif cmd == "plan":
        plan(o)
    elif cmd == "verify":
        verify(o)
    elif cmd == "fixtures":
        fixtures(o)
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
