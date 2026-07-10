#!/usr/bin/env python3
"""FITS acquisition-metadata probe for the dedicated-astrocam preflight.

Usage: fitsmeta.py <dir>
       fitsmeta.py --pick-masters <calibdir> <filter-token>

Reads every FITS frame's header in <dir> and prints ONE tab-separated line:

    <exptime>\t<gain>\t<offset>\t<filter>\t<mono>

exptime seconds (canonical %g), gain/offset the sensor settings, filter the
NORMALIZED filter token, mono 1 (single-channel, no CFA) or 0 (OSC CFA). It is
the dedicated-camera analog of run_pipeline.sh's exiftool uniformity check and
exits nonzero with a message when <dir> is empty or its frames are not
internally uniform in exptime/gain/offset/filter — a mixed dir must fail loud,
never be averaged into a wrong master.

--pick-masters resolves PREBUILT master calibration for a set: <calibdir>
holds single-FITS masters named {dark,flat}_<token>.<ext>, and the token in
the FILENAME is the only identity these files carry (measured on the SHO
corpus: the masters' headers hold no exposure/gain/filter at all), so both
the filename token and the argument go through the same synonym table the
frame FILTER keyword uses. Prints one line, '-' for a missing kind:

    <dark-path-or-->\t<flat-path-or-->

Two files normalizing to the same kind+token is ambiguity and fails loud.

Filter identity is the FITS FILTER keyword (a free-text SBIG convention, not a
validated core-FITS keyword), so its value is normalized to a canonical token
(L/R/G/B/Ha/OIII/SII) via a synonym table; an unknown, non-empty filter is
passed through verbatim with a warning (degrade loudly — a real filter the
table doesn't know must not be silently dropped). Frame type comes from the
pipeline's directory convention (darks/ flats/ darkflats/ <set>/), not the
header, so a DARK's FILTER ('DARK', a wheel-position label) is never matched.
"""
import os
import re
import sys

EXTS = (".fit", ".fits", ".fts")

# Canonical filter tokens from the free-text variants the acquisition packages
# (NINA/SharpCap/Ekos) write. Key = the frame's FILTER upper-cased with spaces,
# dashes, underscores and brackets stripped; value = the canonical token.
_FILTER_SYNONYMS = {
    "L": "L", "LUM": "L", "LUMINANCE": "L", "CLEAR": "L", "CLS": "L",
    "UVIR": "L", "UVIRCUT": "L", "LPRO": "L", "LENHANCE": "L",
    "R": "R", "RED": "R",
    "G": "G", "GREEN": "G",
    "B": "B", "BLUE": "B",
    "HA": "Ha", "HALPHA": "Ha", "HYDROGENALPHA": "Ha",
    "OIII": "OIII", "O3": "OIII", "OXYGEN": "OIII", "OXYGENIII": "OIII",
    "SII": "SII", "S2": "SII", "SULFUR": "SII", "SULFURII": "SII",
    # dark/bias frames carry a wheel-position label, not a light filter:
    # normalize to "no filter" so they neither warn nor match a light set
    "DARK": "", "DARKFLAT": "", "NONE": "", "NA": "", "N/A": "",
}


def normalize_filter(raw):
    """Free-text FILTER value -> canonical token; unknown non-empty -> verbatim
    (caller warns). Empty/None -> '' (no filter, e.g. a dark)."""
    if not raw:
        return ""
    key = re.sub(r"[\s\-_/\[\]]", "", raw.strip().upper())
    return _FILTER_SYNONYMS.get(key, raw.strip())


def read_header(path):
    """Parse a FITS primary header into {KEY: value_str} (first 12 blocks max
    covers any realistic header; stops at END)."""
    hdr = {}
    with open(path, "rb") as f:
        for _ in range(12):
            block = f.read(2880)
            if not block:
                break
            done = False
            for i in range(0, 2880, 80):
                c = block[i:i + 80].decode("ascii", "replace")
                key = c[:8].strip()
                if key == "END":
                    done = True
                    break
                if "=" in c:
                    hdr[key] = c[10:].split("/")[0].strip().strip("'").strip()
            if done:
                break
    return hdr


def frame_meta(path):
    h = read_header(path)
    exp = h.get("EXPTIME", h.get("EXPOSURE", ""))
    try:
        exp = f"{float(exp):g}"
    except ValueError:
        pass
    gain = h.get("GAIN", "")
    offset = h.get("OFFSET", h.get("BLKLEVEL", ""))
    filt = normalize_filter(h.get("FILTER", ""))
    naxis = h.get("NAXIS", "2")
    bayer = h.get("BAYERPAT", h.get("BAYERPATTERN", ""))
    mono = "1" if (naxis == "2" and not bayer) else "0"
    return exp, gain, offset, filt, mono


def pick_masters(calibdir, token):
    """{dark,flat}_<token> master paths from <calibdir>, matched on the
    NORMALIZED filename token; '-' when that kind has no match."""
    want = normalize_filter(token)
    if not want or want == "-":
        sys.exit(f"fitsmeta: --pick-masters needs a real filter token, "
                 f"got {token!r} (a filterless set has no per-filter "
                 "master to match)")
    found = {}
    for f in sorted(os.listdir(calibdir)):
        base, ext = os.path.splitext(f)
        if ext.lower() not in EXTS:
            continue
        m = re.match(r"(dark|flat)_(.+)$", base, re.IGNORECASE)
        if not m:
            continue
        kind = m.group(1).lower()
        if normalize_filter(m.group(2)) != want:
            continue
        if kind in found:
            sys.exit(f"fitsmeta: ambiguous prebuilt masters in {calibdir}: "
                     f"both {os.path.basename(found[kind])} and {f} "
                     f"normalize to {kind}_{want} — remove one")
        found[kind] = os.path.join(calibdir, f)
    print(f"{found.get('dark', '-')}\t{found.get('flat', '-')}")


def main():
    if len(sys.argv) == 4 and sys.argv[1] == "--pick-masters":
        pick_masters(sys.argv[2], sys.argv[3])
        return
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    d = sys.argv[1]
    frames = sorted(f for f in os.listdir(d) if f.lower().endswith(EXTS)) \
        if os.path.isdir(d) else []
    if not frames:
        sys.exit(f"fitsmeta: no FITS frames in {d}")
    metas = [frame_meta(os.path.join(d, f)) for f in frames]
    # uniformity on the calibration-relevant fields (exptime/gain/offset/filter)
    keys = set((m[0], m[1], m[2], m[3]) for m in metas)
    if len(keys) != 1:
        sys.stderr.write(f"fitsmeta: mixed exptime/gain/offset/filter in {d} "
                         "— remove stale frames:\n")
        for k in sorted(keys):
            sys.stderr.write(f"  exptime={k[0]} gain={k[1]} offset={k[2]} "
                             f"filter={k[3]!r}\n")
        sys.exit(1)
    exp, gain, offset, filt, mono = metas[0]
    # EVERY field is '-' when absent, NEVER empty: the consumer parses this
    # line with IFS=tab `read`, and bash collapses consecutive tabs, so one
    # empty field shifts every later field left — an absent OFFSET (this
    # keyword is optional; measured on a filter-wheel CCD corpus) put the
    # filter into the offset column and the mono flag into the filter
    # column, and the mono set silently took the debayer path
    exp, gain, offset, filt = (v or "-" for v in (exp, gain, offset, filt))
    # warn (do not fail) on a filter string the synonym table did not know:
    # a real but unlisted filter must degrade loudly, not be dropped
    raw_filts = {read_header(os.path.join(d, f)).get("FILTER", "") for f in frames}
    for rf in raw_filts:
        if rf and normalize_filter(rf) == rf.strip() and \
                re.sub(r"[\s\-_/\[\]]", "", rf.strip().upper()) not in _FILTER_SYNONYMS:
            sys.stderr.write(f"fitsmeta: WARNING: unrecognized filter {rf!r} in "
                             f"{d} — passed through un-normalized (add it to the "
                             "synonym table)\n")
    print(f"{exp}\t{gain}\t{offset}\t{filt}\t{mono}")


if __name__ == "__main__":
    main()
