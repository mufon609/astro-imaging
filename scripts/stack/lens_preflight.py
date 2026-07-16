#!/usr/bin/env python3
"""Optics preflight for a light set: STOP before a silently-wrong stack.

Usage: lens_preflight.py <session-dir> <set> [--require-profile] [--json=<out>]

Why this exists — two silent-wrong failures this guards, both MEASURED:

1. **A MIXED-OPTICS set.** `acquisition.json` reads optics from the FIRST FRAME
   ONLY, so it structurally cannot see a zoom bump mid-set. A mixed-focal set is
   a mixed-optics stack: every frame carries a different distortion, and the
   lens correction silently applies a DIFFERENT model per frame (each frame's
   own EXIF drives it), so the set does not blend — it fragments. This is the
   acquisition checklist's "lock the zoom ring" surfacing as a processing
   consequence. Checked over EVERY frame, and it is why this cannot be delegated
   to the acquisition record.

2. **A lens the lensfun DB cannot match — which darktable NEVER reports.**
   darktable's lens module bakes nothing: camera, lens, focal and scale all come
   from each image's EXIF (the style carries only `modify_flags`). The upside is
   that ONE style is camera-, lens- and focal-general. The trap is the same
   mechanism: an unmatched lens gets NO correction, silently — measured at max
   |dr| = 0.000 px over 413 stars, exit 0, and not one word in darktable's log.
   Such a set stacks UNCORRECTED and the only symptom is a worse Siril `seqtilt`
   off-axis aberration in the final: exactly the defect the route removes,
   reintroduced with no warning.

**Why this asks darktable rather than lensfun.** The question is not "does the
lensfun DB contain this lens" — it is "will darktable correct THIS set". Those
are adjacent, not identical: darktable normalizes the EXIF strings itself before
querying, so a lensfun-side answer can differ from darktable's. Nor is there a
tool to ask: Debian ships no lensfun query CLI (`lenstool` is not packaged),
`python3-lensfun` exposes only DB-path helpers (`get_database_directories`,
`system_db_path`, `get_database_version`) and no matcher at all, and
`liblensfun-bin` carries only the update/adapter utilities. Querying lensfun
would therefore mean parsing its XML and reimplementing its fuzzy matcher — an
analysis the tool owns (`CLAUDE.md`, the FORBIDDEN test). So `--require-profile`
asks the tool that will do the work to PROVE it did it: render frame 1 through
the pinned `lensdist` and `nodist` styles (the same one-knob pair the route
ships, differing only in the module's enabled bit) and let Siril measure the
difference. Zero difference = no profile matched = STOP.

That proof catches the silent no-op. It does NOT catch lensfun fuzzy-matching a
correct EXIF string to a wrong DB entry — that warp is non-zero, so it passes.
Checks 1 and 2 above bound that risk (the EXIF must be uniform and must match
the record); a residual lensfun-internal mismatch is a documented limit, not a
claim this guard makes.

Siril and darktable and exiftool do every pixel operation and every measurement.
This script reads EXIF via exiftool, compares strings, and asks Siril for the
difference statistic — it reads no pixel and computes no measurement.
"""
import argparse
import glob
import json
import os
import shutil
import re
import subprocess
import sys
import tempfile

_libdir = os.path.dirname(os.path.abspath(__file__))
while _libdir != os.path.dirname(_libdir):
    if os.path.isdir(os.path.join(_libdir, "lib")):
        sys.path.insert(0, os.path.join(_libdir, "lib"))
        break
    _libdir = os.path.dirname(_libdir)
import astrometrics as am  # noqa: E402  (dataset_dir: the tracked per-dataset home)

SIRIL = ["flatpak", "run", "--command=siril-cli", "org.siril.Siril"]
RAW_EXT = (".nef", ".dng", ".cr2", ".cr3", ".arw", ".raf", ".orf", ".rw2")
STYLE_DIR = os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), "darktable")


class Stop(Exception):
    """A ready-to-print refusal: the set must not stack as-is."""


def frames_of(session_dir, set_name):
    d = os.path.join(session_dir, set_name)
    return sorted(p for p in glob.glob(os.path.join(d, "*"))
                  if p.lower().endswith(RAW_EXT))


def per_frame_optics(frames):
    """Every frame's optics from exiftool — NOT just the first. One call."""
    r = subprocess.run(["exiftool", "-json", "-Model", "-LensID",
                        "-FocalLength", "-SourceFile", *frames],
                       capture_output=True, text=True)
    try:
        data = json.loads(r.stdout)
    except ValueError:
        raise Stop("lens_preflight: exiftool returned no parseable metadata "
                   f"for {len(frames)} frame(s). Optics cannot be verified, so "
                   "the set cannot be cleared to stack.")
    return [{"file": os.path.basename(d.get("SourceFile", "?")),
             "camera": d.get("Model"),
             "lens": d.get("LensID"),
             "focal_mm": d.get("FocalLength")} for d in data]


def check_uniform(optics):
    """STOP on a mixed-optics set. Every frame, not the first."""
    report = {}
    for key, label in (("camera", "camera body"), ("lens", "lens"),
                       ("focal_mm", "focal length")):
        vals = {}
        for o in optics:
            vals.setdefault(o[key], []).append(o["file"])
        report[key] = {str(k): len(v) for k, v in vals.items()}
        if len(vals) > 1:
            detail = "\n".join(
                f"      {k!r}: {len(v)} frame(s), e.g. {', '.join(v[:3])}"
                for k, v in sorted(vals.items(), key=lambda kv: -len(kv[1])))
            raise Stop(
                f"lens_preflight: MIXED {label} across the set — {len(vals)} "
                f"distinct values:\n{detail}\n"
                "    A mixed-optics set is not one stack: each frame carries "
                "its own distortion, and the lens correction applies a "
                "DIFFERENT model per frame (it reads each frame's own EXIF), "
                "so the set fragments rather than blends.\n"
                "    This is a hard stop, not an interpolation. Split the set "
                "per optics (one dir per pointing AND per focal), or exclude "
                "the odd frames. See the acquisition checklist "
                "('lock the zoom ring') in docs/dead-ends.md.")
        if None in vals and len(vals) == 1:
            raise Stop(
                f"lens_preflight: no {label} in EXIF for any frame. Optics "
                "cannot be verified, so the set cannot be cleared to stack. If "
                "this is a telescope/astrocam set it has no lens EXIF by "
                "construction — such sets do not take the lens-correction "
                "route and should not be run through this preflight.")
    return report


def check_record(session_dir, set_name, optics):
    """Cross-check the tracked acquisition record against the frames."""
    path = os.path.join(am.dataset_dir(session_dir, set_name),
                        "acquisition.json")
    if not os.path.exists(path):
        return {"record": None, "note": "no acquisition.json yet — nothing to "
                                        "contradict (it is seeded at stack time)"}
    rec = json.load(open(path)).get("exif") or {}
    o = optics[0]
    drift = [f"{k}: record {rec.get(rk)!r} vs frames {o[k]!r}"
             for k, rk in (("camera", "camera"), ("lens", "lens"),
                           ("focal_mm", "focal_length_mm"))
             if rec.get(rk) is not None and _norm(rec.get(rk)) != _norm(o[k])]
    if drift:
        raise Stop(
            "lens_preflight: the tracked acquisition record CONTRADICTS the "
            "frames:\n      " + "\n      ".join(drift) + f"\n    ({path})\n"
            "    The record is what downstream consumers trust. Re-derive it "
            "(it is auto-written from EXIF — do not hand-edit the `exif` "
            "block) or confirm the right frames are in this set.")
    return {"record": path, "agrees": True}


def _norm(v):
    if v is None:
        return None
    s = str(v).strip().lower()
    m = re.match(r"^([0-9.]+)", s)          # "70.0 mm" == 70.0
    return m.group(1).rstrip("0").rstrip(".") if m else s


def prove_correction(frame, work):
    """Ask darktable to PROVE it corrects this frame: render it through the
    pinned lensdist/nodist pair (one knob — the lens module's enabled bit) and
    let Siril measure the difference. Identical output = no profile matched.

    Returns Siril's difference statistic. darktable does the pixel work; Siril
    measures; this only compares the numbers it printed.
    """
    if not shutil.which("darktable-cli"):
        raise Stop("lens_preflight: --require-profile needs darktable-cli, "
                   "which is not installed. The lens-correction route cannot "
                   "run on this rig (see CLAUDE.md Environment).")
    cfg = os.path.join(work, "dtcfg")
    inst = os.path.join(STYLE_DIR, "install_styles.sh")
    subprocess.run(["bash", inst, cfg], capture_output=True, text=True)
    outs = {}
    for style in ("lensdist", "nodist"):
        out = os.path.join(work, f"{style}.tif")
        subprocess.run(
            ["darktable-cli", frame, out, "--style", style, "--style-overwrite",
             "--icc-type", "SRGB", "--core", "--configdir", cfg,
             "--library", ":memory:",
             "--conf", "plugins/imageio/format/tiff/bpp=16"],
            capture_output=True, text=True)
        if not os.path.exists(out):
            raise Stop(f"lens_preflight: darktable produced no output for "
                       f"style {style!r} on {os.path.basename(frame)}.")
        outs[style] = out
    ssf = os.path.join(work, "_diff.ssf")
    ref = os.path.join(work, "nodist_fits")   # isub takes FITS, not TIFF
    with open(ssf, "w") as f:
        f.write("requires 1.4.4\n"
                f"load {outs['nodist']}\n"
                f"save {ref}\n"
                f"load {outs['lensdist']}\n"
                f"isub {ref}\n"
                "stat\n")
    r = subprocess.run(SIRIL + ["-d", work, "-s", ssf],
                       capture_output=True, text=True)
    # Siril `stat` prints per layer: "... Sigma: S, ... Max: M, ...".
    sig = [float(x) for x in re.findall(r"Sigma:\s*([0-9.eE+-]+)", r.stdout)]
    mx = [float(x) for x in re.findall(r"Max:\s*([0-9.eE+-]+)", r.stdout)]
    if sig and mx:
        return {"siril_stat_sigma": sig, "siril_stat_max": mx,
                "corrected": max(mx) > 0 or max(sig) > 0}
    # An all-zero difference is the NO-OP we are hunting, and Siril names it
    # exactly: it refuses to compute statistics over an empty image ("all
    # nil?") rather than printing zeros. That refusal IS the proof, so read it
    # as the answer — not as a parse failure.
    if re.search(r"Statistics computation failed.*all nil", r.stdout):
        return {"siril_stat_sigma": [], "siril_stat_max": [],
                "siril_verdict": "stat refused: difference image is all nil",
                "corrected": False}
    raise Stop("lens_preflight: Siril `stat` reported neither statistics nor "
               "its all-nil refusal for the lensdist-vs-nodist difference — "
               "its output format may have drifted, so the proof is "
               "inconclusive and the set is not cleared:\n" + r.stdout[-600:])


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("session")
    ap.add_argument("set")
    ap.add_argument("--require-profile", action="store_true",
                    help="also PROVE darktable corrects this set (renders one "
                         "frame twice); STOP if the correction is a no-op. Pass "
                         "this whenever the lens-correction route will run.")
    ap.add_argument("--json")
    a = ap.parse_args()

    frames = frames_of(a.session, a.set)
    if not frames:
        print(f"lens_preflight: no camera raws in {a.session}/{a.set} — "
              "not a camera-lens set, nothing to verify.")
        return 0
    try:
        optics = per_frame_optics(frames)
        spread = check_uniform(optics)
        rec = check_record(a.session, a.set, optics)
        o = optics[0]
        print(f"lens_preflight: {len(frames)} frames, optics UNIFORM")
        print(f"  camera {o['camera']!r}  lens {o['lens']!r}  "
              f"focal {o['focal_mm']!r}")
        result = {"frames": len(frames), "optics": o, "spread": spread,
                  "record": rec}
        if a.require_profile:
            # The proof's scratch lives under the tracked per-set dir (the raw
            # frame dir holds raw frames only), which a new set may not have yet.
            # It must be under $HOME either way — the flatpak sandbox has a
            # private /tmp, so Siril cannot see a scratchpad there.
            ddir = am.dataset_dir(a.session, a.set)
            os.makedirs(ddir, exist_ok=True)
            work = tempfile.mkdtemp(prefix=".lenspre_", dir=ddir)
            try:
                proof = prove_correction(os.path.abspath(frames[0]), work)
            finally:
                shutil.rmtree(work, ignore_errors=True)
            result["profile_proof"] = proof
            if not proof["corrected"]:
                evidence = proof.get("siril_verdict") or (
                    f"max {proof['siril_stat_max']}, sigma "
                    f"{proof['siril_stat_sigma']}")
                raise Stop(
                    "lens_preflight: darktable applied NO correction to "
                    f"{os.path.basename(frames[0])} — the lensdist and nodist "
                    f"renders are IDENTICAL (Siril on their difference: "
                    f"{evidence}).\n"
                    f"    lensfun has no profile for {o['camera']!r} + "
                    f"{o['lens']!r}. darktable does not report this — it exits "
                    "0 and silently passes the frame through, so the set would "
                    "stack UNCORRECTED and only a worse `seqtilt` off-axis "
                    "aberration in the final would show it.\n"
                    "    Fix the DB (the upstream lensfun DB is newer than the "
                    "distro's — see docs/wide-field-untracked-registration.md), "
                    "or route this set WITHOUT the lens correction and record "
                    "that choice with its trade-off.")
            print(f"  darktable PROVES it corrects this set "
                  f"(lensdist vs nodist: Siril stat max "
                  f"{max(proof['siril_stat_max']):.0f}, not a no-op)")
    except Stop as e:
        print(str(e), file=sys.stderr)
        return 1
    if a.json:
        with open(a.json, "w") as f:
            json.dump(result, f, indent=1)
        print(f"  wrote {a.json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
