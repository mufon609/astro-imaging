# Terminology — the 'dust' ban and the four senses

Phase-2 file of the dead-ends registry split (`README.md` here holds the index
and dispositions; pre-compression forms live in git and in the live
`docs/dead-ends.md` until the merge).

<!-- phase-2: maintained in place; not regenerated from the manifest -->
**TERMINOLOGY — the word "dust" is BANNED in this repo, and this entry says
why.** "Cosmic dust", "MW", "IFN" and "dust-safe" were used interchangeably
for FOUR physically unrelated things; the term was never defined and never
independently identified, and everything downstream of it — the background
class limit, the GraXpert-Division rejection, the sky-flat enabling
condition, the denoise strength limit — rested on a term nobody had
measured. Use these four instead, and say which one you mean:

**WHERE THE WORD CAME FROM — an ACQUISITION artefact, not a sky object.** The
term entered from early frames shot at 24 mm, 20+ s, ISO 200: at that focal
length the plate scale is ~3× coarser than the 70 mm work, so the star field
below the detection limit never resolves and reads as a smooth diffuse
"dust". The same sky at 70 mm, ISO 1600 resolves those features into
individual stars — which is what sense 2 then MEASURED against Gaia. "Milky
Way dust" was never a thing that exists; it was undersampled starlight, and
the word survived a change of optics that had already falsified it. A term
that is an artefact of one focal length must not set doctrine for another.

1. **OPTICAL DUST MOTES** — physical dust on the sensor or optics. A
   flat-field feature, fixed in SENSOR coordinates, routinely measured
   (`findstar` speck counts on the flats). The only sense in which "dust"
   was ever correct, and it has nothing to do with the sky.
2. **UNRESOLVED STARLIGHT** — the frame-filling faint diffuse field: at this
   data's 17.0″/px in the galactic plane, the integrated light of Milky Way
   stars fainter than the detection limit. **MEASURED (july23 set-01+02,
   Gaia DR3 vs Siril, `qa_work/dust_identification.json`): the star layer's
   per-cell diffuse floor tracks Gaia's unresolved-starlight prediction at
   R² 0.9631 over a 140-cell external lattice; detection limit G ≈ 11.0 at
   50% completeness; ~0.2 catalogued sources per PIXEL brighter than G=17.**
   It is STARS — not dust, and not nebulosity. SCOPE: flux and source-count
   predictors are 97.7% collinear in this field, so the fit constrains
   rather than proves "flux specifically" (the clean separation is
   UNRESOLVED flux at R² 0.963 beating TOTAL flux at 0.503); the absolute
   photometric scale carries a 20–30% systematic (Gaussian-fit photometry on
   trailed stars) — correlations are scale-free and unaffected, ADU
   predictions are not. ONE dataset, one field, one pixel scale.
3. **HII EMISSION** — NGC 7000, IC 1318 and the like: real diffuse emission,
   LOCALIZED, Hα-red. Measured on ONE region only: NGC 7000 sits +2.5σ above
   the starlight relation, R/G 1.1918 against a 0.9303 field. **SCOPE — 1 of
   3 regions tested, and the other two did NOT stand out** (−0.07σ, −0.72σ;
   the 1.4° cells are coarse for objects that size and two test coordinates
   landed in the same cell). The honest claim: emission IS separable from
   starlight by this instrument on a large bright region; the instrument was
   not shown sensitive enough for smaller ones. A nebula is not dust and is
   not "IFN" regardless — definitional, not measured.
4. **DUST SILHOUETTE** — real interstellar dust, which at this scale appears
   as ABSENCE, not emission: the Cygnus Rift dark lanes. **NOT PROPERLY
   MEASURED — a working model, not a result.** Gaia integrated flux in 0.3°
   cones runs lowest near the plane, CONSISTENT with foreground extinction —
   but those cones are dominated by their few brightest stars, and no test
   separated extinction from ordinary structure in the stellar distribution.
   The test that would: per-cell Gaia flux against a reddening map, or
   Gaia's own extinction estimates, over the sense-2 lattice.

**The rendering consequence, and it is not optional.** Sense 2 is stars, so
it is rendered AS STARS — preserving the brightness hierarchy of the
population, never amplified as a diffuse glow (that produced a uniform
speckle-field with no hierarchy and was rejected on sight — the `star_asinh`
entry, `stretch-colour-judgment.md`).
