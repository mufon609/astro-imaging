#!/usr/bin/env python3
"""Assemble a user-judgment package from render FINALS — scripted, verified.

Usage: judgment_package.py <outdir> <label>=<final.png> [...]
           --question="what the judge is deciding"
           [--reference=<label>=<path.jpg>] [--note="..." ...]

The review contract (README): a judgment set is a folder of WHOLE-FRAME
LOSSLESS finals (PNG16 + PNG8) with clean names and a QUESTION.md — nothing
else. Hand-assembly has a measured failure mode (a package shipped the
STARLESS-layer PNG16 mislinked as the final for 3 of 4 candidates), so this
tool takes each candidate's 8-bit lossless PNG (the path starcomb prints),
derives its _16bit.png sibling, and VERIFIES the pair before linking:

- the path must be a .png and must not name a _starless layer (the gate
  input is never a judgment surface),
- both files of the pair must exist,
- the pair must agree pixel-wise (PNG16/257 vs PNG8 within 8-bit rounding
  on a sample grid) — a mixed pair (e.g. a starless PNG16 beside a final
  PNG8) cannot pass this.

Candidates are hardlinked (copy fallback) as NN_<label>.png +
NN_<label>_16bit.png in argument order. --reference adds ONE third-party
comparison image, named with LOSSY in the filename (an author's finish is
whatever encoding they published; it is comparison-only, never a judgment
surface). QUESTION.md gets the question, the file list, and the --note
lines verbatim; the caller states gate numbers and caveats there.
"""
import os
import shutil
import struct
import sys
import zlib

import numpy as np


def read_png16_sampled(path, step=16):
    """Decode a 16-bit RGB PNG (color type 2, depth 16) and return a
    row/column-sampled uint16 array — enough to identity-check against the
    8-bit sibling without holding the full 100 MB decode."""
    with open(path, "rb") as f:
        data = f.read()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        sys.exit(f"judgment_package: {path} is not a PNG")
    pos, w, h, depth, ct, idat = 8, None, None, None, None, []
    while pos < len(data):
        ln = struct.unpack(">I", data[pos:pos + 4])[0]
        tag = data[pos + 4:pos + 8]
        if tag == b"IHDR":
            w, h, depth, ct = struct.unpack(">IIBB", data[pos + 8:pos + 18])
        elif tag == b"IDAT":
            idat.append(data[pos + 8:pos + 8 + ln])
        elif tag == b"IEND":
            break
        pos += 12 + ln
    if depth != 16 or ct != 2:
        sys.exit(f"judgment_package: {path} is not a 16-bit RGB PNG "
                 f"(depth {depth}, color type {ct})")
    raw = zlib.decompress(b"".join(idat))
    stride, bpp = w * 6, 6
    out_rows = []
    prev = np.zeros(stride, np.int32)
    p = 0
    for y in range(h):
        flt = raw[p]; p += 1
        row = np.frombuffer(raw[p:p + stride], np.uint8).astype(np.int32)
        p += stride
        if flt == 0:
            cur = row
        elif flt == 1:
            cur = row.copy()
            for i in range(bpp, stride):
                cur[i] = (cur[i] + cur[i - bpp]) & 0xff
        elif flt == 2:
            cur = (row + prev) & 0xff
        elif flt == 3:
            cur = row.copy()
            cur[:bpp] = (cur[:bpp] + prev[:bpp] // 2) & 0xff
            for i in range(bpp, stride):
                cur[i] = (cur[i] + ((cur[i - bpp] + prev[i]) >> 1)) & 0xff
        else:                                   # 4 = Paeth
            cur = row.copy()
            for i in range(stride):
                a = cur[i - bpp] if i >= bpp else 0
                b = prev[i]
                c = prev[i - bpp] if i >= bpp else 0
                pa, pb, pc = abs(b - c), abs(a - c), abs(a + b - 2 * c)
                pr = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                cur[i] = (cur[i] + pr) & 0xff
        if y % step == 0:
            u8 = cur.astype(np.uint8).reshape(w, 3, 2)
            out_rows.append(((u8[..., 0].astype(np.uint16) << 8)
                             | u8[..., 1])[::step])
        prev = cur
    return np.stack(out_rows)


def verify_pair(png8, png16, step=16):
    """The final pair must be the SAME render: PNG16/257 vs PNG8 within
    8-bit rounding on the sample grid. A mixed pair (starless PNG16 beside
    a final PNG8) differs by whole stars and cannot pass."""
    from PIL import Image
    Image.MAX_IMAGE_PIXELS = None
    a8 = np.asarray(Image.open(png8))[::step, ::step].astype(np.float32)
    a16 = read_png16_sampled(png16, step).astype(np.float32)
    if a8.shape != a16.shape:
        sys.exit(f"judgment_package: {os.path.basename(png8)} and its "
                 f"_16bit sibling differ in geometry {a8.shape} vs "
                 f"{a16.shape}")
    err = np.abs(a16 / 257.0 - a8)
    if float(err.max()) > 0.51:
        sys.exit(f"judgment_package: PAIR MISMATCH for "
                 f"{os.path.basename(png8)}: PNG16 disagrees with PNG8 "
                 f"(max {err.max():.1f} counts on the sample grid) — the "
                 "16-bit file is NOT this final (mislinked layer?)")


def place(src, dst):
    try:
        os.link(src, dst)
    except OSError:
        shutil.copy2(src, dst)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    notes = [a[7:] for a in sys.argv[1:] if a.startswith("--note=")]
    question = next((a[11:] for a in sys.argv[1:]
                     if a.startswith("--question=")), None)
    reference = next((a[12:] for a in sys.argv[1:]
                      if a.startswith("--reference=")), None)
    if len(args) < 2 or not question:
        sys.exit(__doc__)
    outdir, cands = args[0], args[1:]
    if os.path.isdir(outdir) and os.listdir(outdir):
        sys.exit(f"judgment_package: {outdir} exists and is not empty — "
                 "a judgment set is assembled once, never edited in place")
    os.makedirs(outdir, exist_ok=True)

    lines = [f"# Judgment: {question}", "",
             "Open each file independently, full frame, your own viewers.",
             "_16bit.png = the float render at 65536 levels; .png = 8-bit",
             "lossless. All pipeline candidates are whole-frame lossless",
             "finals (verified pairs).", ""]
    for i, spec in enumerate(cands, 1):
        if "=" not in spec:
            sys.exit(f"judgment_package: candidate {spec!r} is not "
                     "label=<final.png>")
        label, png8 = spec.split("=", 1)
        if not png8.endswith(".png") or png8.endswith("_16bit.png"):
            sys.exit(f"judgment_package: {png8} — pass the 8-bit lossless "
                     ".png final (the path starcomb prints); the _16bit "
                     "sibling is derived")
        if "_starless" in os.path.basename(png8):
            sys.exit(f"judgment_package: {png8} is a STARLESS layer — the "
                     "gate input is never a judgment surface; pass the "
                     "combined final")
        png16 = png8[:-4] + "_16bit.png"
        for p in (png8, png16):
            if not os.path.exists(p):
                sys.exit(f"judgment_package: missing {p}")
        verify_pair(png8, png16)
        d8 = os.path.join(outdir, f"{i:02d}_{label}.png")
        d16 = os.path.join(outdir, f"{i:02d}_{label}_16bit.png")
        place(png8, d8)
        place(png16, d16)
        print(f"[judgment_package] {i:02d}_{label}: verified pair linked")
        lines.append(f"- {i:02d}_{label}: FILL IN (knobs / what changed)")
    if reference:
        rl, rp = reference.split("=", 1)
        ext = os.path.splitext(rp)[1].lower() or ".jpg"
        dn = f"{len(cands) + 1:02d}_{rl}_LOSSY_ORIGINAL{ext}"
        place(rp, os.path.join(outdir, dn))
        print(f"[judgment_package] {dn}: reference (comparison only)")
        lines.append(f"- {dn}: third-party reference — LOSSY original, "
                     "comparison only, never a judgment surface")
    lines.append("")
    lines += notes
    lines += ["", "Say which candidate pins (or what to ladder next)."]
    with open(os.path.join(outdir, "QUESTION.md"), "w") as f:
        f.write("\n".join(lines) + "\n")
    print(f"[judgment_package] wrote {outdir}/QUESTION.md — fill in the "
          "candidate descriptions + gate numbers before handing it over")


if __name__ == "__main__":
    main()
