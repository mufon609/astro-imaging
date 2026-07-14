---
id: meta/BACKLOG
type: meta
---

# BACKLOG

**Superseded by the x86 redesign — see [REDESIGN.md](REDESIGN.md).**

The prior BACKLOG was a long queue of refinements and adaptations for the
aarch64 base rig and its hand-rolled render chain. The rig migration to
x86-64 (and the Siril-1.4 tool-rich discovery) makes almost all of it moot:
the render chain is being rebuilt tool-first on x86, and the arm64
workarounds' removal conditions have fired. That queue lives in git history;
it is not carried forward. The x86 rebuild will re-found this file from what
the rebuild actually surfaces.

## Carried forward — durable data-capability items (not arch-specific)

These are real imaging capabilities the pipeline does not yet have; they
survive the rig change and should be reconsidered during the x86 rebuild
(REDESIGN step 4+), each as a measured declared delta:

- **LRGB join** — compose L after both L and RGB are stretched (the standard
  luminance-detail join). The compose stage currently REFUSES a `luminance`
  member because compose-then-render cannot express a post-stretch L-join;
  the x86 chain should. Siril `rgbcomp -lum=` is the native primitive.
- **Full-size dual-band** — native Ha + 2× drizzle of OIII instead of
  downsampling OIII to Ha's half-size, gated on measured dither coverage
  (the per-frame `dither_phase_frac` record already exists in the
  registration QA).
- **run_pipeline auto-routing to a partitioned/large-sequence path** — on
  32 GB this is largely unnecessary, but a very large sequence may still want
  common-reference partitioning; decide against the real x86 memory headroom.
- **Deconvolution** — a measured dead-end on the arm64 data (unstable
  symmetric PSF on in-exposure trailing); revisit with BlurXTerminator on
  x86, where a real deconvolution tool exists.
- **A native star-colour-neutral colour tool** — the O3-sphere mechanism
  Siril has no equivalent for (currently Nightlight's job). Still a genuine
  gap; the x86 chain decides Nightlight-x86 vs a native `ccm`+recombine path.
