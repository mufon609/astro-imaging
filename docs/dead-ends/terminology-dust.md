# Terminology — the 'dust' ban and the four senses

Phase-1 split of `docs/dead-ends.md` (organize-only; the original file stays
the live registry until the merge is decided). Content below the marker is
VERBATIM from the original, so in-text "above"/"below"/section references may
point at entries now homed in a sibling file — `README.md` in this directory
carries the index, the assignment rule, and the block manifest that resolves
them. Do not edit below the marker while the refactor is in phase 1; the split
is re-derivable from the manifest and verified byte-identical by `split.py`.

<!-- == verbatim content from docs/dead-ends.md below this marker == -->
**TERMINOLOGY — the word "dust" is BANNED in this repo, and this entry says why.**
"Cosmic dust", "MW", "IFN" and "dust-safe" were used interchangeably for FOUR
physically unrelated things; the term was never defined and never independently
identified, and everything downstream of it — the background class limit, the
GraXpert-Division rejection, the sky-flat enabling condition, the denoise
strength limit — rested on a term nobody had measured. Use these four instead,
and say which one you mean:

**WHERE THE WORD CAME FROM — an ACQUISITION artefact, not a sky object.** The
term entered this project from early wide-field frames shot at **24 mm, 20+ s,
ISO 200**. At that focal length the plate scale is ~3x coarser than the 70 mm
work, so the star field below the detection limit never resolves and reads as a
smooth diffuse "dust". The same sky at **70 mm, ISO 1600** resolves those same
features into individual stars — which is exactly what sense 2 below then
MEASURED against Gaia. "Milky Way dust" was never a thing that exists; it was
undersampled starlight, and the word survived a change of optics that had
already falsified it. There is no Milky Way dust. There is nebular EMISSION
(sense 3), there is real interstellar dust seen in SILHOUETTE (sense 4), and
there are faint stars (sense 2). A term that is an artefact of one focal length
must not set doctrine for another.

1. **OPTICAL DUST MOTES** — physical dust on the sensor or optics. A flat-field
   feature, fixed in SENSOR coordinates, routinely measured (`findstar` speck
   counts on the flats). The only sense in which "dust" was ever correct, and
   it has nothing to do with the sky.
2. **UNRESOLVED STARLIGHT** — the frame-filling faint diffuse field: at this
   data's 17.0"/px in the galactic plane, the integrated light of Milky Way
   stars fainter than the detection limit. **MEASURED (july23 set-01+02, Gaia
   DR3 vs Siril, `qa_work/dust_identification.json`): the star layer's per-cell
   diffuse floor tracks Gaia's unresolved-starlight prediction at R² 0.9631
   over a 140-cell external lattice; detection limit G ≈ 11.0 at 50%
   completeness (one-to-one matched); ~0.2 catalogued sources per PIXEL
   brighter than G=17.** It is STARS — not dust, and not nebulosity.
   SCOPE: flux and source-count predictors are 97.7% collinear in this field,
   so that fit constrains rather than proves "flux specifically" — the clean
   separation is UNRESOLVED flux (R² 0.963) beating TOTAL flux (R² 0.503),
   which is not a collinear pair. The integrated starlight figure of
   22.74 mag/arcsec² is ONE 0.25° cone at the field centre; no frame-wide value
   was computed. The absolute photometric scale carries a 20-30% systematic
   (Gaussian-fit photometry on trailed stars) — every CORRELATION above is
   scale-free and unaffected, but any ADU prediction derived from it is not.
   ONE dataset, one field, one pixel scale.
3. **HII EMISSION** — NGC 7000, IC 1318 and the like: real diffuse emission,
   LOCALIZED, Hα-red. Measured on ONE region only: NGC 7000 sits +2.5σ above
   the starlight relation and reads R/G 1.1918 against a 0.9303 field.
   **SCOPE — 1 of 3 regions tested, and the other two did NOT stand out**
   (IC 1318 −0.07σ, NGC 6888 −0.72σ) — partly because the 1.4° cells are coarse
   for objects that size and the IC 1318 and "dark lane" test coordinates
   landed in the SAME cell. The honest claim: emission IS separable from
   starlight by this instrument on a large bright region, and the instrument
   was not shown sensitive enough for smaller ones. A nebula is not dust and is
   not "IFN" regardless — definitional, not measured.
4. **DUST SILHOUETTE** — real interstellar dust, which at this scale appears as
   ABSENCE, not emission: the Cygnus Rift dark lanes. **NOT PROPERLY MEASURED —
   treat as a working model, not a result.** Gaia integrated flux in 0.3° cones
   runs lowest near the plane (1.76e-3 at b=−2 against 1.27e-2 at b=−10), which
   is CONSISTENT with foreground extinction — but those cones are small enough
   to be dominated by their few brightest stars (noted as noisy when taken),
   and no test separated extinction from ordinary structure in the stellar
   distribution. The physical expectation (dust obscures rather than emits at
   17"/px) is textbook and is why this sense belongs in the list at all; the
   NUMBERS above do not establish it. The test that would: per-cell Gaia flux
   against a reddening map, or Gaia's own extinction estimates, over the
   sense-2 lattice.

**The rendering consequence, and it is not optional.** Sense 2 is stars, so it
is rendered AS STARS — preserving the brightness hierarchy of the population,
never amplified as a diffuse glow (that produced a uniform speckle-field with
no hierarchy and was rejected on sight — the `star_asinh` entry under
"Stretch / colour").

