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
   from each image's EXIF (the style carries only its enabled bit — every
   op_params field is ignored, so the correction SET is enforced in the lensfun
   DB by install_lens_model.sh, not here). The upside is
   that ONE style is camera-, lens- and focal-general. The trap is the same
   mechanism: an unmatched lens gets NO correction, silently — measured at max
   |dr| = 0.000 px over 413 stars, exit 0, and not one word in darktable's log.
   Such a set stacks UNCORRECTED and the only symptom is a worse Siril `seqtilt`
   off-axis aberration in the final: exactly the defect the route removes,
   reintroduced with no warning.

3. **The correction SET widening back to darktable's default, which includes
   VIGNETTING** — a double-correction over lights the flat already corrected,
   measured at 1.27-1.37x corner/centre while it was live. `--require-profile`
   delegates this to `verify_lens_card.py` (grid positive control + uniform
   card; the card ALONE is vacuous). It is a separate failure from 2 because a
   vignetting-corrected frame IS warped, so the no-op proof passes on it.

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

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lib"))
from siril_run import SIRIL, run as siril_run   # serialized invoker (BACKLOG item 18)
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
        # setcompress is a PERSISTED siril preference — pin it off so the
        # saved reference is the plain .fit the isub line names
        f.write("requires 1.4.4\n"
                "setcompress 0\nsetext fit\n"
                f"load {outs['nodist']}\n"
                f"save {ref}\n"
                f"load {outs['lensdist']}\n"
                f"isub {ref}\n"
                "stat\n")
    r = siril_run(["-d", work, "-s", ssf],
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



def prove_vignetting_off(frame, work):
    """Prove darktable's correction SET is distortion-only for these optics —
    delegated whole to scripts/darktable/verify_lens_card.py.

    `prove_correction` above answers "did darktable warp at all" and
    `check_pinned_model` answers "is the DB carrying our coefficients". Neither
    can see the third failure: the correction SET widening back to darktable's
    default, which includes VIGNETTING. That double-corrects lights already
    flat-corrected upstream — MEASURED at 1.27-1.37x corner/centre on a
    full-depth stack while it was live. The set is not chosen by the style
    (darktable ignores a style's lens op_params); it is enforced in the lensfun
    user DB, which `lensfun-update-data` OVERWRITES on every run. So the strip is
    machine-local state a routine tool update silently reverts, and until this
    call the only thing that would notice was a human remembering to run the
    check by hand.

    UNCONDITIONAL under --require-profile: MEASURED at 11.1 s on this rig's
    6064x4040 frames against a run that already renders one raw twice, so there
    is no cost argument for making it optional.

    --from-frame, not --session/--set: the fixture then takes its optics AND its
    card geometry from the frame this preflight has already proven uniform
    across the set, so it works before acquisition.json is seeded (a new set has
    no record yet) and cannot disagree with the frames.
    """
    tool = os.path.join(STYLE_DIR, "verify_lens_card.py")
    rec = os.path.join(work, "lens_card.json")
    r = subprocess.run([sys.executable, tool, "--from-frame", frame,
                        "--work", work, "--json", rec],
                       capture_output=True, text=True)
    if r.returncode != 0 or not os.path.exists(rec):
        raise Stop(
            "lens_preflight: the distortion-only proof FAILED — darktable's lens "
            "correction is not the set this chain is built on:\n"
            + (r.stdout + r.stderr).strip()[-1200:] +
            "\n    Both fixtures matter: the GRID is the positive control (the "
            "module must fire at all) and the UNIFORM CARD is the measurement "
            "(a photometric corner-vs-centre step means VIGNETTING is back in "
            "the path, double-correcting lights the flat already corrected).\n"
            "    Fix: scripts/darktable/install_lens_model.sh <session> <set> "
            "re-strips <vignetting>/<tca> from the lensfun user DB.")
    return json.load(open(rec))


def live(s):
    """Blank XML-comment CONTENT, preserving length so match offsets still index
    `s`. Mandatory before scanning a <lens> block for a distortion line: the
    marker install_lens_model.sh used to write embedded a VERBATIM
    `<distortion .../>` element naming the coefficients it REPLACED, so a raw
    scan finds the superseded model first and this check then compares the
    pinned file against its own footprint. MEASURED on this rig 2026-08-05 — it
    returned state=ok while lensfun was applying a different model, i.e. the one
    assertion that exists to catch a wrong-but-present profile could not fail
    once the block had ever been patched. install_lens_model.sh no longer writes
    the decoy, but blocks patched by older versions are still in service on real
    rigs, so this stays. lensfun ignores comments; so must we.

    MODULE-LEVEL DELIBERATELY: _selftest() neutralises it to prove the fixture's
    decoy is real and that the masking is load-bearing. A closure could not be
    neutralised, and then the only evidence that the guard CAN fail would be an
    argument about the fixture's construction rather than an executed result —
    which is exactly how the two previous versions of this test came to pass
    while proving nothing.
    """
    return re.sub(r"<!--.*?-->", lambda m: " " * len(m.group(0)), s, flags=re.S)


PINNED_MODELS = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "scripts", "darktable", "lens_models.json")


def check_pinned_model(optics):
    """Assert the live lensfun DB still carries the PINNED coefficients for these
    optics.

    `prove_correction` answers "did darktable warp this frame at all", which
    catches a MISSING profile. It cannot catch the case that actually bit this
    repo: a profile that is present but is not the model the products were built
    with. `lensfun-update-data` OVERWRITES the user DB on every run, silently
    reverting the fitted entry to the community one — a wrong-but-present model
    that warps, so the existing proof passes and the set stacks with different
    optics than every product it will be compared against.

    Reads our own pinned record and the DB text; asks lensfun nothing (Debian
    ships no query CLI, which is why the warp proof exists at all).
    """
    o = optics[0]
    lens, focal = o.get("lens"), o.get("focal_mm")
    # exiftool reports FocalLength as text ("70.0 mm"), not a number — take the
    # leading value rather than assuming a float, the same way the fixture
    # builder in verify_lens_card.py does.
    fm = re.match(r"\s*([0-9.]+)", str(focal)) if focal is not None else None
    if not lens or not fm:
        return {"state": "na", "why": f"no usable lens/focal ({lens!r}, {focal!r})"}
    focal = fm.group(1)
    try:
        pinned = json.load(open(PINNED_MODELS))
    except (OSError, ValueError) as e:
        return {"state": "na", "why": f"no pinned model file ({e})"}

    def norm(x):
        return re.sub(r"[^a-z0-9]", "", str(x).lower())

    f = float(focal)
    key = f"{lens}@{str(int(f)) if f == int(f) else f}"
    entry = next((v for k, v in pinned.items()
                  if not k.startswith("_") and norm(k) == norm(key)), None)
    if entry is None:
        return {"state": "unpinned", "key": key,
                "why": "no pinned model for these optics — the warp will use "
                       "whatever the DB happens to carry, which is not tracked"}
    pt = entry["ptlens"]
    dbdir = os.path.expanduser("~/.local/share/lensfun/updates/version_1")
    want = {k: float(pt[k]) for k in ("a", "b", "c")}
    for path in sorted(glob.glob(os.path.join(dbdir, "*.xml"))):
        try:
            xml = open(path, encoding="utf-8", errors="replace").read()
        except OSError:
            continue
        for blk in re.findall(r"<lens>(?:(?!</lens>).)*?</lens>", xml, re.S):
            mm = re.search(r"<model>(.*?)</model>", blk, re.S)
            if not mm or norm(mm.group(1)) != norm(lens):
                continue
            fs = str(int(f)) if f == int(f) else str(f)
            dm = re.search(rf'<distortion[^>]*focal="{re.escape(fs)}"[^>]*/>',
                           live(blk))
            if not dm:
                return {"state": "MISMATCH", "key": key, "pinned": want,
                        "why": f"the DB block for {mm.group(1)!r} has no "
                               f"focal={fs} distortion line at all"}
            got = {k: float(v) for k, v in
                   re.findall(r'\b([abc])="([-0-9.eE+]+)"', dm.group(0))}
            if all(abs(got.get(k, 1e9) - want[k]) <= 1e-9 for k in want):
                return {"state": "ok", "key": key, "coefficients": got}
            return {"state": "MISMATCH", "key": key, "pinned": want,
                    "installed": got, "db": os.path.basename(path)}
    return {"state": "MISMATCH", "key": key, "pinned": want,
            "why": f"no <lens> block matching {lens!r} in {dbdir}"}


def _selftest():
    """ASYMMETRIC mutation test for check_pinned_model's block scan.

    Why asymmetric, and why this test exists at all: the scan was blind — it
    read the `<distortion .../>` element embedded in install_lens_model.sh's
    marker comment instead of the live one — and the mutation test written to
    prove it could fail DID NOT CATCH IT. That mutation rewrote the coefficient
    string with `str.replace` and no count, so it flipped the live element AND
    the marker's copy together; whichever copy the scan read, both had moved, so
    the check still reported MISMATCH and the guard looked green while being
    blind. A mutation that changes EVERY copy of a thing cannot distinguish
    "reads the right copy" from "reads any copy". The mutation has to change
    exactly one occurrence and leave the other intact. Same species as the
    `Found [0-9]+ star` regex and the vacuous uniform card: the check could not
    fail, and the thing meant to prove it could fail was itself defective.

    Four blocks, all with a pinned/candidate pair and a legacy-style marker
    carrying a verbatim element, so the test also covers markers written before
    the coefficients-only change.
    """
    ok = True

    def flag(name, cond):
        nonlocal ok
        ok = ok and cond
        print(f"  [{'PASS' if cond else 'FAIL'}] {name}")

    # Identity + reference coefficients come from the PINNED file itself, so the
    # fixture cannot drift out of the authority and cannot silently become
    # "unpinned" (which would make every case pass vacuously).
    pinned = json.load(open(PINNED_MODELS))
    key, entry = next((k, v) for k, v in pinned.items() if not k.startswith("_"))
    lens_name, focal_key = key.rsplit("@", 1)
    pt = entry["ptlens"]
    PIN = " ".join(f'{k}="{pt[k]!r}"'.replace("'", "") for k in "abc")
    CAND = PIN.replace(f'a="{pt["a"]!r}"', f'a="{float(pt["a"]) * 1.05!r}"', 1)
    assert CAND != PIN, "selftest fixture failed to perturb the live element"

    def blk(marker_coeffs, live_coeffs):
        return (f'<lens><maker>M</maker><model>{lens_name}</model>\n'
                f'  <!-- astro-imaging fitted: focal=70 replaced '
                f'<distortion model="ptlens" focal="{focal_key}" {marker_coeffs}/>; '
                f'2026-08-05 -->\n'
                f'  <calibration>\n'
                f'    <distortion model="ptlens" focal="24" a="0.03" b="-0.1" c="0.07"/>\n'
                f'    <distortion model="ptlens" focal="{focal_key}" {live_coeffs}/>\n'
                f'  </calibration></lens>')

    def state(block):
        """check_pinned_model's inner scan, on a supplied block."""
        import tempfile as _tf
        d = _tf.mkdtemp(prefix=".lenspre_selftest_")
        try:
            with open(os.path.join(d, "test.xml"), "w") as f:
                f.write("<lensdatabase>" + block + "</lensdatabase>")
            real = os.path.expanduser
            os.path.expanduser = lambda p: d if "lensfun" in p else real(p)
            try:
                return check_pinned_model([{"lens": lens_name,
                                            "focal_mm": f"{focal_key}.0 mm"}])
            finally:
                os.path.expanduser = real
        finally:
            shutil.rmtree(d, ignore_errors=True)

    # The pinned file must carry the key this fixture names, or every case
    # returns "unpinned" and the test is itself vacuous — assert that first.
    probe = state(blk(CAND, PIN))
    flag("fixture resolves against a PINNED entry (not vacuous)",
         probe.get("state") != "unpinned")

    # CASE 2 IS THE INCIDENT, not one of five permutations. Mutating the LIVE
    # element only, leaving the marker on the pinned value, is EXACTLY the state
    # this rig was in on 2026-08-05: lensfun applying the x86 re-fit while this
    # function reported `pinned model OK`, because the scan matched the marker's
    # embedded copy. It is the regression test. Do not simplify the fixture down
    # to the symmetric cases — they pass on a blind scan (see case 5).
    r = state(blk(PIN, CAND))
    flag(f"live=candidate, marker=pinned -> {r['state']} (want MISMATCH)",
         r["state"] == "MISMATCH")

    # MUTATE THE MARKER ONLY -> must still be ok. A scan that reads the marker
    # fails HERE, which is the other half of the asymmetry.
    r = state(blk(CAND, PIN))
    flag(f"live=pinned, marker=candidate -> {r['state']} (want ok)",
         r["state"] == "ok")

    # Cases 4 and 5 are the SYMMETRIC mutation — both copies moved together.
    # Case 5 is preserved as a SPECIMEN: it is the mutation test that was
    # actually written for this guard, and it PASSED on the blind scan, because
    # when every copy of the coefficients moves it does not matter which one is
    # read. A mutation that changes every copy of a thing cannot distinguish
    # "reads the right copy" from "reads any copy". Neither case proves anything
    # on its own; they are here so nobody mistakes them for coverage.
    flag("both pinned -> ok (symmetric, weak)",
         state(blk(PIN, PIN))["state"] == "ok")
    flag("both candidate -> MISMATCH (symmetric — PASSES ON A BLIND SCAN, weak)",
         state(blk(CAND, CAND))["state"] == "MISMATCH")

    # ---- PROVE THE TEST CAN FAIL, by executing it -------------------------
    # THE RULE THIS ENCODES: verifying that a guard can fail is an ACT, not an
    # argument. Break the mechanism, watch the assertion go red, restore. Two
    # earlier versions of this very test passed while proving nothing — the
    # first because its mutation moved every copy of the coefficients at once,
    # the second because its decoy was written `focal=70` where the scanner
    # requires `focal="70"`, so the fixture had no decoy at all. Both were
    # reasoned about from construction and neither was executed against a
    # disabled mechanism. So the disabled-mechanism run happens HERE, every run.
    global live
    _real, live = live, (lambda t: t)          # neutralise the masking
    try:
        blind = state(blk(PIN, CAND))["state"]
    finally:
        live = _real
    flag(f"with masking DISABLED, case 2 reads {blind} (want ok = the incident "
         f"reproduces, so the fixture's decoy is real and masking is what "
         f"catches it)", blind == "ok")
    # and the mechanism must be back
    flag("masking restored", state(blk(PIN, CAND))["state"] == "MISMATCH")

    print("SELFTEST", "PASS" if ok else "FAIL")
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("session", nargs="?")
    ap.add_argument("set", nargs="?")
    ap.add_argument("--selftest", action="store_true",
                    help="asymmetric mutation test of the pinned-model scan")
    ap.add_argument("--require-profile", action="store_true",
                    help="also PROVE darktable corrects this set (renders one "
                         "frame twice); STOP if the correction is a no-op. Pass "
                         "this whenever the lens-correction route will run.")
    ap.add_argument("--json")
    a = ap.parse_args()

    if a.selftest:
        return _selftest()
    if not (a.session and a.set):
        ap.error("session and set are required (or --selftest)")

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
            pin = check_pinned_model(optics)
            result["pinned_model"] = pin
            if pin["state"] == "MISMATCH" and pin.get("installed"):
                # The ONE sanctioned divergence: installed == this SET'S OWN
                # recorded fit — the --from-fit A/B state
                # (install_lens_model.sh), which this assert predated and
                # blocked. Announced as CANDIDATE, never silent; any OTHER
                # installed model (community revert via lensfun-update-data,
                # another set's state left behind) still STOPS below — exactly
                # the silent-wrong cases the assert exists for. Per-set optical
                # states: BACKLOG:`optical-state-models`; its closing condition
                # is the standing per-state wiring this bridges.
                try:
                    fit = json.load(open(os.path.join(
                        am.dataset_dir(a.session, a.set),
                        "qa_work", "lens_fit.json")))["fitted_ptlens"]
                    if all(abs(float(fit[k]) - pin["installed"].get(k, 1e9))
                           <= 1e-9 for k in ("a", "b", "c")):
                        pin = {**pin, "state": "candidate",
                               "fit_record": "qa_work/lens_fit.json"}
                        result["pinned_model"] = pin
                except (OSError, ValueError, KeyError):
                    pass
            if pin["state"] == "MISMATCH":
                raise Stop(
                    "lens_preflight: the installed lens model is NOT the pinned "
                    f"one for {pin['key']}.\n"
                    f"    pinned    {pin.get('pinned')}\n"
                    f"    installed {pin.get('installed', pin.get('why'))}\n"
                    "    darktable WILL warp — with different optics than every "
                    "product this set would be compared against, and the "
                    "warp-happened proof cannot see that. `lensfun-update-data` "
                    "overwrites the user DB on every run, which is the usual "
                    "cause.\n"
                    "    Fix: scripts/darktable/install_lens_model.sh "
                    f"{a.session} {a.set}")
            if pin["state"] == "ok":
                print(f"  pinned model OK: {pin['key']} matches the live DB")
            elif pin["state"] == "candidate":
                print(f"  CANDIDATE model live: installed == this set's OWN "
                      f"fitted model (qa_work/lens_fit.json), NOT the pinned "
                      f"incumbent for {pin['key']} — the --from-fit A/B state; "
                      f"the build carries the set's optical state")
            elif pin["state"] == "unpinned":
                print(f"  WARN: {pin['why']}")
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
            # LAST of the three, because it is the only one that costs a render
            # pair of its own: the two cheaper checks above catch the same
            # lensfun-update-data event and stop before this one is paid for.
            card_work = tempfile.mkdtemp(prefix=".lenscard_", dir=ddir)
            try:
                card = prove_vignetting_off(os.path.abspath(frames[0]),
                                            card_work)
            finally:
                shutil.rmtree(card_work, ignore_errors=True)
            result["vignetting_off"] = card
            print(f"  distortion-only VERIFIED: grid control fires "
                  f"(Siril sigma {max(card['grid_control']['sigma']):.1f}), "
                  f"uniform card worst corner {card['worst_corner']} "
                  f"{card['worst_delta_adu']:.3f} ADU from centre "
                  f"(tol {card['tol_adu']}) — no vignetting in the path")
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
