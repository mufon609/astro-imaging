# Dead-end registry + acquisition checklist

The registry lives in [`docs/dead-ends/`](dead-ends/) — one file per pipeline
stage plus the cross-cutting disciplines. **Never re-attempt a registered dead
end: if a thing does not work, the mechanism why is here. Read
[`00-registry-contract.md`](dead-ends/00-registry-contract.md) first (it
governs how entries are read, cited, written and deleted), then the files your
work touches, before proposing any experiment.** Full detail + the original
numbers live in git history (the NOTES at the commit whose message begins
`checkpoint:` — `git log --oneline --grep='^checkpoint:'`; the pre-split
single-file registry is this path's own history —
`git log -- docs/dead-ends.md`).

Cite an entry by FILE + ENTRY HEADLINE — headlines are stable identifiers,
line numbers are not. Every entry carries its evidence class
(MEASURED / MECHANISM / DOCTRINE), its n, instrument, scope and subject, per
the contract.

| file | scope |
|---|---|
| [`00-registry-contract.md`](dead-ends/00-registry-contract.md) | how entries are read, cited, written, deleted — evidence classes, the SUBJECT axis, the owner-ratified write/delete rules |
| [`terminology-dust.md`](dead-ends/terminology-dust.md) | the "dust" ban and the four measured senses |
| [`acquisition-checklist.md`](dead-ends/acquisition-checklist.md) | the acquisition checklist + the LUNAR class block — the real quality lever |
| [`intake-frame-qa.md`](dead-ends/intake-frame-qa.md) | frame QA, culling, drift/mount instruments |
| [`calibration-flats.md`](dead-ends/calibration-flats.md) | synthetic sky flats, darks, masters; the open `sky × V` tilt's dead ends |
| [`background-extraction.md`](dead-ends/background-extraction.md) | BGE: subsky degrees, GraXpert, the coverage-crop order |
| [`stretch-colour-judgment.md`](dead-ends/stretch-colour-judgment.md) | stretch amplification, colour/chroma, SPCC-NB, judgment surfaces |
| [`separation-deconv-psf.md`](dead-ends/separation-deconv-psf.md) | star separation, deconvolution, the PSF-homogenisation refusal |
| [`plate-solving-wcs.md`](dead-ends/plate-solving-wcs.md) | solver routes, xylists, union solves, SIP/CTYPE and matrix-form traps |
| [`registration-distortion.md`](dead-ends/registration-distortion.md) | wide-field untracked registration, lens models, darktable/lensfun, the ICC legs |
| [`stacking-compose.md`](dead-ends/stacking-compose.md) | weights, rejection, walking noise, the groups route, the sub-stack compose |
| [`lunar-planetary.md`](dead-ends/lunar-planetary.md) | planetary registrations: selection, quality, DFT aliasing |
| [`star-shape-optics.md`](dead-ends/star-shape-optics.md) | the star-shape/PSF/optics measurement family; the open one-sided band |
| [`siril-behaviors.md`](dead-ends/siril-behaviors.md) | tool silent behaviours: clipping, persisted preferences, coordinate conventions |
| [`measurement-discipline.md`](dead-ends/measurement-discipline.md) | comparison crops, floors, reproducibility, controls |
| [`verification-traps.md`](dead-ends/verification-traps.md) | checks and search instruments that lie |
| [`evidence-provenance.md`](dead-ends/evidence-provenance.md) | records, claims, provenance, multi-session epistemics |

Provenance of the split: `dead-ends/manifest.tsv` maps every block of the
pre-split file to its destination; `dead-ends/README.md` carries the
directory's own provenance note.
