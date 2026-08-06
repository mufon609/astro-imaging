#!/usr/bin/env python3
"""Per-dataset acquisition record — the facts a tool needs about HOW a set was
shot, split by provenance and kept honest:

  exif.*  DERIVED from the frames' metadata: photo-EXIF via exiftool for
          camera raws (camera, lens, focal length, exposure, ISO, image size,
          field of view + pixel scale, cadence / time span); for
          dedicated-astrocam FITS frames the SAME facts from the FITS header
          (INSTRUME/TELESCOP/FOCALLEN/XPIXSZ/GAIN/DATE-OBS — `iso` is null,
          there is no such concept; `gain` and `binning` are recorded).
  mount   DECLARED by a human — "fixed" (tripod) or "tracked" (driven mount).
          EXIF does not record it, and no single frame settles it (a short
          enough exposure hides the drift), so a consumer must be TOLD.
          It IS measurable across frames — scripts/qa/mount_probe.sh solves two
          windows and fingerprint.py reads the RA rate against sidereal — and
          when that measurement exists the stop below quotes it, so the human
          ratifies a number rather than supplying a fact the tools already know.
          The declaration still stays theirs: declared-and-measured is what makes
          CONTRADICT detectable, and a lone auto-adopted solve would be believed
          silently when it is wrong.

WHY THIS EXISTS: cross-frame reasoning — e.g. the anomaly audit chaining one
satellite across consecutive frames — assumes a FIXED, untracked camera, where
each crossing traces a straight sensor-plane line. That must be GROUND TRUTH,
not a buried default; on a tracked mount it is wrong. So `resolve()` seeds this
record with everything EXIF knows and STOPS if `mount` is undeclared, instead of
silently assuming a camera model. The record is the tracked per-dataset home
(datasets/<session>/<set>/acquisition.json), beside geometry.json / recipe.json;
`exif.*` is tool-written (refreshed when it changes), `mount` is the human field.

Reads only metadata — exiftool photo-EXIF for camera raws, astropy FITS
headers for astrocam frames (never the deliverable's pixels) — and writes only
this record: orchestration + records, not image analysis.
"""
import json
import os
import re
import subprocess
from datetime import datetime

import astrometrics as am   # dataset_dir(): the tracked per-dataset home

MOUNTS = ("fixed", "tracked")
_NOTE = ("`mount` is the one acquisition fact EXIF cannot record and a consumer "
         "must be told; `exif` is auto-derived by scripts/lib/acquisition.py — "
         "do not hand-edit it.")


class AcquisitionUndeclared(Exception):
    """Raised when a set's `mount` is not declared. Carries the seeded record
    path and a ready-to-print ask (derive-what-you-can, ask-what-you-can't)."""

    def __init__(self, path, exif, measured=None, detail=None):
        self.path = path
        self.measured = measured
        e = exif or {}
        opt = (f"{e.get('focal_length_mm', '?')}mm {e.get('exposure_s', '?')}s "
               f"ISO{e.get('iso', '?')}, cadence {e.get('cadence_s', '?')}s, "
               f"{e.get('frames', '?')} frames")
        # Reaching this exception now means the instruments did NOT decide — a
        # decisive signature self-adopts in resolve() (mount_source "derived").
        # So `measured` is populated here only in the disagreement case, where
        # mount_verdict nulls the signature but the raw reading is still worth
        # quoting so the human ratifies a number rather than an open question.
        says = (f"  MEASURED: the data reads as {measured}"
                + (f" ({detail})" if detail else "") + ".\n"
                  f'  If that is right, set  "mount": "{measured}"  to ratify it.\n'
                if measured else
                "  No drift measurement yet — scripts/qa/mount_probe.sh <session> "
                "<set>\n  solves two windows and measures it.\n")
        super().__init__(
            "acquisition: `mount` is not declared for this set.\n"
            "  The cross-frame linking assumes a FIXED (untracked) camera; on a\n"
            "  tracked mount it would mislink, so it will not be assumed.\n"
            f"  EXIF facts were filled into: {path}\n"
            + says +
            '  Valid values: "fixed" (tripod) or "tracked" (driven mount).\n'
            f"  (EXIF: {e.get('camera', '?')}, {opt})")


class MountContradicted(AcquisitionUndeclared):
    """Raised when the set's derived fingerprint measures the sky moving
    OPPOSITE to the declared mount (mount_check CONTRADICT) — a labelling
    error no consumer may build on. Subclasses AcquisitionUndeclared so every
    declare-or-stop consumer stops just as loudly here, with this message."""

    def __init__(self, path, reason):
        self.path = path
        Exception.__init__(
            self,
            "acquisition: the declared `mount` CONTRADICTS the measured sky "
            "motion.\n"
            f"  {reason}\n"
            f"  Record: {path}\n"
            "  Fix the declaration (or re-measure the frames) and re-run — a\n"
            "  consumer must not build on a mislabelled mount.")


def _num(v):
    """Leading number from an exiftool value: '6'->6.0, '70.0 mm'->70.0,
    '28.6 deg (5.11 m)'->28.6, '1/200'->0.005. None if unparseable."""
    if v is None:
        return None
    s = str(v).strip()
    m = re.match(r"([0-9]+(?:\.[0-9]+)?)\s*/\s*([0-9]+(?:\.[0-9]+)?)$", s)
    if m:
        a, b = float(m.group(1)), float(m.group(2))
        return a / b if b else None
    m = re.match(r"[-+]?[0-9]*\.?[0-9]+", s)
    return float(m.group(0)) if m else None


def _epoch(v):
    """exiftool timestamp ('2026:07:14 22:48:48.99-04:00', or without
    subsecond / zone) -> epoch seconds; None if unparseable."""
    if not v:
        return None
    s = str(v).strip()
    for fmt in ("%Y:%m:%d %H:%M:%S.%f%z", "%Y:%m:%d %H:%M:%S%z",
                "%Y:%m:%d %H:%M:%S.%f", "%Y:%m:%d %H:%M:%S"):
        try:
            return datetime.strptime(s, fmt).timestamp()
        except ValueError:
            continue
    return None


def _median(xs):
    xs = sorted(xs)
    n = len(xs)
    if not n:
        return None
    return xs[n // 2] if n % 2 else (xs[n // 2 - 1] + xs[n // 2]) / 2.0


def _pointing_deg(header, num_key, sexa_key, hours):
    """Pointing coordinate (deg) from an astrocam header. Two forms exist:
    the numeric RA/DEC keywords (conventionally decimal DEGREES, but some
    writers use hours for RA) and the OBJCTRA/OBJCTDEC sexagesimal strings
    (unit-unambiguous: RA in hours, Dec in degrees, by FITS convention).
    The numeric form needs a FULL-string float parse — '18 02 36' must not
    truncate to 18 — and when both forms parse but disagree beyond 0.5 deg
    the sexagesimal one wins (its units cannot be misread). None when
    neither parses."""
    numeric = None
    v = header.get(num_key)
    if v is not None:
        try:
            numeric = float(v)
        except (TypeError, ValueError):
            pass
    sexa = None
    s = header.get(sexa_key)
    if s is not None:
        m = re.match(r"^\s*([+-]?)(\d+)[ :h]+(\d+)[ :m]+([0-9.]+)", str(s))
        if m:
            sign = -1.0 if m.group(1) == "-" else 1.0
            d = (int(m.group(2)) + int(m.group(3)) / 60.0
                 + float(m.group(4)) / 3600.0)
            sexa = sign * d * (15.0 if hours else 1.0)
    if numeric is not None and sexa is not None:
        return numeric if abs(numeric - sexa) <= 0.5 else sexa
    return numeric if numeric is not None else sexa


def fits_facts(frames):
    """FITS sibling of the exiftool derivation — the same facts from the FITS
    headers (astropy, HEADERS only). Optics from the first frame; cadence /
    time-span from every frame's DATE-OBS. pixel_scale = 206.265 * XPIXSZ /
    FOCALLEN; the common writers record XPIXSZ as the effective (binned) pixel
    size, and `binning` is recorded so a corpus where that convention differs
    is visible. `iso` stays null (no such concept on an astrocam); GAIN is
    recorded as `gain`. Pointing RA/Dec (the mount's own record, written by
    the capture software) is a header fact here — camera-raw EXIF has no
    equivalent, so on that path it stays None and a solve supplies dec. On
    failure returns {'_error': ...} so a consumer can still require `mount`."""
    try:
        from astropy.io import fits as _fits
    except ImportError as e:
        return {"_error": f"astropy unavailable ({e}); mount still required"}
    try:
        h0 = _fits.getheader(frames[0])
    except OSError as e:
        return {"_error": f"FITS header unreadable ({e}); mount still required"}

    def num(k):
        try:
            v = h0.get(k)
            return float(v) if v is not None else None
        except (TypeError, ValueError):
            return None

    exposure = num("EXPOSURE")
    if exposure is None:
        exposure = num("EXPTIME")
    focal, pixsz = num("FOCALLEN"), num("XPIXSZ")
    width, height = h0.get("NAXIS1"), h0.get("NAXIS2")
    scale = (round(206.2648 * pixsz / focal, 3)
             if pixsz and focal else None)
    ts = []
    for f in frames:
        try:
            d = _fits.getheader(f).get("DATE-OBS")
        except OSError:
            d = None
        if d:
            try:
                ts.append(datetime.fromisoformat(str(d)).timestamp())
            except ValueError:
                pass
    ts.sort()
    dts = [b - a for a, b in zip(ts, ts[1:]) if b > a]
    ra = _pointing_deg(h0, "RA", "OBJCTRA", hours=True)
    dec = _pointing_deg(h0, "DEC", "OBJCTDEC", hours=False)
    return {
        "camera": h0.get("INSTRUME"),
        "lens": h0.get("TELESCOP"),      # the optic identity slot
        "focal_length_mm": focal,
        "exposure_s": exposure,
        "iso": None,
        "gain": num("GAIN"),
        "binning": int(num("XBINNING") or 1),
        "pointing_ra_deg": round(ra, 5) if ra is not None else None,
        "pointing_dec_deg": round(dec, 5) if dec is not None else None,
        "image_wh": [width, height],
        "fov_deg": (round(scale * width / 3600.0, 2)
                    if scale and width else None),
        "pixel_scale_arcsec": scale,
        "cadence_s": round(_median(dts), 2) if dts else None,
        "frames": len(frames),
        "time_span_s": round(ts[-1] - ts[0], 1) if len(ts) > 1 else 0.0,
    }


def exif_facts(frames):
    """Derive the acquisition facts EXIF knows, over all frames (one exiftool
    call). Optics from the first frame; cadence / time-span from the per-frame
    timestamps. pixel_scale (full-res arcsec/px) comes from exiftool's FOV,
    which it computes from its own sensor database (no body hardcode); the green
    plane the audit works on is 2x this. On any exiftool failure returns
    {'_error': ...} so a consumer can still require `mount`. FITS frames route
    to the header sibling `fits_facts` (photo-EXIF tags do not exist there)."""
    if frames and os.path.splitext(frames[0])[1].lower() in (
            ".fit", ".fits", ".fts"):
        return fits_facts(frames)
    tags = ["-json", "-SubSecDateTimeOriginal", "-DateTimeOriginal",
            "-ExposureTime", "-FocalLength", "-ISO", "-Model", "-LensID",
            "-ImageWidth", "-ImageHeight", "-FOV"]
    try:
        r = subprocess.run(["exiftool", *tags, *frames],
                           capture_output=True, text=True)
        data = json.loads(r.stdout)
    except (OSError, ValueError) as e:
        return {"_error": f"exiftool unavailable ({e}); mount still required"}
    if not data:
        return {"_error": "exiftool returned no metadata"}
    d0 = data[0]
    ts = sorted(t for t in (_epoch(d.get("SubSecDateTimeOriginal")
                                   or d.get("DateTimeOriginal")) for d in data)
                if t is not None)
    dts = [b - a for a, b in zip(ts, ts[1:]) if b > a]
    width = d0.get("ImageWidth")
    fov = _num(d0.get("FOV"))
    iso = _num(d0.get("ISO"))
    return {
        "camera": d0.get("Model"),
        "lens": d0.get("LensID"),
        "focal_length_mm": _num(d0.get("FocalLength")),
        "exposure_s": _num(d0.get("ExposureTime")),
        "iso": int(iso) if iso is not None else None,
        "image_wh": [width, d0.get("ImageHeight")],
        "fov_deg": fov,
        "pixel_scale_arcsec": round(fov * 3600.0 / width, 3)
                              if fov and width else None,   # full-res
        "cadence_s": round(_median(dts), 2) if dts else None,
        "frames": len(data),
        "time_span_s": round(ts[-1] - ts[0], 1) if len(ts) > 1 else 0.0,
    }


def timeline(frames):
    """Per-frame [{file, framenum, epoch, exposure_s}] for detecting capture
    discontinuities in an AD-HOC dir (a grab-bag some of whose frames form a
    continuous burst and some of which do not). framenum is the filename's
    trailing number (DSC_6896 -> 6896); epoch is the EXIF capture time;
    exposure_s lets a consumer derive the expected interval-timer cycle
    (exposure + a fixed cooldown), so a gap longer than one cycle is a boundary.
    A big frame-number jump (files from a different capture) or such a long time
    gap marks a boundary a moving object must not be linked across. One exiftool
    pass; on failure fields are None. Sorted by (framenum, epoch, file)."""
    meta = {}
    try:
        r = subprocess.run(["exiftool", "-json", "-SubSecDateTimeOriginal",
                            "-DateTimeOriginal", "-ExposureTime", *frames],
                           capture_output=True, text=True)
        for d in json.loads(r.stdout):
            src = d.get("SourceFile")
            if src:
                meta[os.path.basename(src)] = (
                    _epoch(d.get("SubSecDateTimeOriginal")
                           or d.get("DateTimeOriginal")),
                    _num(d.get("ExposureTime")))
    except (OSError, ValueError):
        pass
    rows = []
    for f in frames:
        base = os.path.basename(f)
        nums = re.findall(r"\d+", os.path.splitext(base)[0])
        epoch, exp = meta.get(base, (None, None))
        rows.append({"file": base,
                     "framenum": int(nums[-1]) if nums else None,
                     "epoch": epoch, "exposure_s": exp})
    rows.sort(key=lambda r: (r["framenum"] if r["framenum"] is not None else 0,
                             r["epoch"] or 0.0, r["file"]))
    return rows


def record_path(session_dir, set_name):
    return os.path.join(am.dataset_dir(session_dir, set_name),
                        "acquisition.json")


def resolve(session_dir, set_name, frames):
    """Return the acquisition record for a set, or STOP if `mount` is not
    declared. Seeds / refreshes datasets/<session>/<set>/acquisition.json with
    the EXIF-derived facts, preserving any human-declared `mount` (normalized
    case-insensitively). Raises AcquisitionUndeclared (a ready-to-print ask)
    when `mount` is missing or not one of MOUNTS — the consumer stops rather
    than assume a camera model. Writes only when the on-disk content would
    change, so a report-only run does not churn a tracked file."""
    path = record_path(session_dir, set_name)
    existing = {}
    if os.path.exists(path):
        try:
            existing = json.load(open(path))
        except ValueError:
            existing = {}
    raw = existing.get("mount")
    mount = raw.strip().lower() if isinstance(raw, str) else None
    valid = mount in MOUNTS
    source = (existing.get("mount_source") or "declared") if valid else None
    exif = exif_facts(frames)
    # The declared mount has to survive its measured cross-check: a set whose
    # FINGERPRINT (derived by scripts/lib/fingerprint.py from the tools' own
    # measures) says the sky moves the OTHER way is mislabelled, and every
    # consumer of this record would build on that error. Read-only here — the
    # fingerprint module derives; this just refuses to hand out a contradicted
    # declaration (consumers STOP on CONTRADICT).
    fp_path = os.path.join(os.path.dirname(path), "fingerprint.json")
    try:
        mount_check = (json.load(open(fp_path)) or {}).get("mount_check") or {}
    except (OSError, ValueError):
        mount_check = {}
    # DERIVE-THEN-ASK: an undeclared set whose instruments have DECIDED adopts
    # the measurement instead of stopping for a human to retype it. `measured`
    # is only ever set when a signature was decisive — mount_verdict nulls it
    # when the two instruments disagree — so the INDETERMINATE case still falls
    # through to the stop below, which is the one case a human is needed for.
    #
    # WHY THIS IS SAFE, against the argument it replaces. This function used to
    # say "the measurement never self-adopts, because the declared-vs-measured
    # pair is what makes CONTRADICT detectable at all." That is half true and it
    # cost every new set a human round-trip to answer a question the tools had
    # already answered four times over. CONTRADICT exists to catch a HUMAN
    # MISLABEL — declared tracked, measures fixed. A set nobody labelled has no
    # mislabel to catch, so nothing is lost by deriving it. What must not be lost
    # is the ability to TELL THE TWO APART afterwards, which is why the source is
    # recorded: `declared` keeps the full human-vs-data cross-check with its
    # CONTRADICT stop, and `derived` still stops if a later, better measurement
    # disagrees with the one adopted — that is no longer a mislabel but an
    # unstable instrument, and it is worth stopping on too.
    derived = None
    if not valid:
        m = mount_check.get("measured")
        m = m.strip().lower() if isinstance(m, str) else None
        if m in MOUNTS:
            derived, mount, valid, source = m, m, True, "derived"
    record = {"mount": mount if valid else None,
              "mount_source": source, "exif": exif, "_note": _NOTE}
    if (existing.get("exif") != exif or existing.get("mount") != record["mount"]
            or existing.get("mount_source") != source
            or not os.path.exists(path)):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        json.dump(record, open(path, "w"), indent=1)
    if not valid:
        raise AcquisitionUndeclared(path, exif, mount_check.get("measured"),
                                    mount_check.get("reason"))
    if mount_check.get("verdict") == "CONTRADICT":
        raise MountContradicted(fp_path, mount_check.get("reason", ""))
    if derived:
        record["derived_now"] = derived    # the caller announces it; not persisted
    return record
