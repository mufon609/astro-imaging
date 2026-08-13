# Fresh-session brief — why the corners are worse, on TWO axes, before any crop line

**SELF-RETIRING.** Delete this file in the commit that lands the result.

The owner sees degradation in the far corners of the combined products and wants
a **measured** line for a possible per-member crop rather than an eyeball
judgement. This brief is the measurement that has to come first. **It does not
propose a crop and must not conclude with one unless the numbers force it.**

## READ THIS BEFORE ANYTHING ELSE — this exact question has been misattributed here

A left-side softness in stacked images was chased for a long time as a LENS
problem. **It was not.** It was the compose: `compose-homography-smear` — the
sub-stack compose is a mosaic being aligned with a single homography, and a set's
five members solve to centres **4.28° apart**. The members were clean
(**2.42–2.54 px, roundness 0.924–0.942**); their compose read **3.48 / 0.582**,
and the accepted cross-night union read **roundness 0.448–0.613 over x = 15–30%
of the canvas** against 0.916–0.968 in the clean band. Fixed by astrometric
composition, verified from raws at **0.980**, owner-passed, item closed.

**The manager repeated the same error while scoping this brief**, citing the
registry's radial-aberration entry as though it explained the visible corner
defect. It does not: that entry measures major-axis **2.46 vs 2.63 px**, roughly
**7%** edge-to-centre. The defect the owner saw was 0.92 → 0.58 roundness. A
small real optical term was offered as the explanation for a large visible defect
that had already been correctly attributed elsewhere and fixed.

So: **do not start from a mechanism.** Measure first, attribute second, and only
if a discriminating test separates the candidates.

## The three candidates, with their ACTUAL status

1. **Coverage depth** — the outer union has fewer contributing members by
   construction. **Established, and cleanly measurable.**
2. **Registration residual** — `member_separation.py` reports a monotone
   **0.22 / 0.48 / 1.30 / 2.43 px** profile by member-own field radius. **But
   that was measured on a union predating the astrometric-compose fix**, and the
   same register row records two healthy sets reading 1.12/0.95 px composed among
   themselves and 3.02/3.38 px inside a 41°, 28-member sequence. So an unknown
   share of that profile is the compose's contribution, not a per-member
   property. **Effectively unquantified on today's chain.**
3. **Optics** — a radial field aberration IS measured on single RAWs (136k stars,
   4 alternatives eliminated), and lensfun does **not** correct coma — it
   corrects distortion, vignetting and TCA. But the amplitude is ~7%. **Real,
   small, and not a candidate for a large visible defect.**

## The discriminator, and it is the whole design

**Coverage depth lives in UNION canvas coordinates. Registration residual and
optical aberration live in MEMBER-OWN field radius.** Those are different
coordinate systems, and a pixel's value on one says nothing about the other.

So measure corner quality against **both axes on the same product**:

- If degradation tracks **union coverage** → candidate 1, and the answer is
  exposure planning, not a crop.
- If it tracks **member-own field radius** → candidates 2/3, and a crop is on the
  table because no amount of extra integration improves a zone the lens and the
  registration both handle badly.
- If both → report both with their sizes. Do not collapse them.

## What to measure

On the **post-fix** corpus — the products built since the astrometric compose,
never the archived pre-fix union, whose numbers describe a defect that no longer
exists.

- **Coverage** — `coverage_frame.py` already computes the verified coverage frame
  from Siril `stat` boxes; its per-box coverage data is the depth axis.
- **Star shape at sky positions** — `shape_at_sky.py` places boxes by each
  product's own solved WCS, rank-matches on the brightest fits, and reports n and
  the faintest admitted amplitude. Use it; it is the instrument the compose fix
  was accepted on.
- **Member-own radius** — `member_separation.py` bins in exactly that axis.
  **Its selftest cannot run without a complete sequence**; one exists now at
  `sessions/aug06/work/l1_msep/in/s_.seq`. Run the selftest FIRST and update its
  register row with the result — an instrument whose falsification has not run in
  this tree does not get to anchor a crop line.
- **SNR** — `snr_regions.py`, on like surfaces only, against LOCAL references.
  A distant reference imports the Milky Way's own brightness gradient and returns
  negative SNR; that happened while scoping this brief.

## Traps, all of them registered and all of them cheap to hit

- **A star-shape median across images of different depth is a DETECTION-DEPTH
  comparison, not a quality one.** Measured at a factor of 9 across one pair.
  Rank-match or use one common amplitude threshold, and report n and the faintest
  admitted amplitude with every number. This trap is *especially* live here,
  because the corners have less depth BY CONSTRUCTION — so an unmatched
  comparison will manufacture exactly the corner defect being investigated.
- `findstar`'s default roundness floor **0.50** truncates the elongated tail under
  study; drop it to 0.05.
- `seqfindstar` writes no star lists headless; use per-image `findstar -out=`.
- Do not bin by a radius inferred from the detections — the origin moves with the
  defect and the profile flattens as the defect worsens (trap 3). Geometry comes
  from the header or the solve, never from the stars being measured.
- Judge nothing on the stretched surface; the autostretch amplifies a background
  variation ~17×.

## The output

**A number, or the finding that no crop line is justified.** Both are results.

If a line exists, express it as **member-own field radius**, so it applies
uniformly per member across sets and nights and a cross-night combine inherits it
automatically — that is the registry's own named lever, *"a per-member edge shrink
at compose input: the mainstream GMM-shrink mechanism"*, which has never been
implemented or measured here.

**Do not implement the shrink in this session.** Measure, report, hand the number
to the owner. Adoption is theirs.

## A ratification this touches — flag it, do not assume it

`BACKLOG` records the user-ratified requirement that **the framing=max union is
the deliverable (manual crop later), no yield excuses.** A per-member shrink
trades area for quality BEFORE the combine, which is a different act from
cropping the final picture. The owner has since said they are *"more worried
about stacking bad sections than about not stacking enough"*. Treat that as a
deliberate revision to be recorded WITH the original, not as licence to assume
the old requirement is gone.

## Acceptance

1. `member_separation --selftest` run on the live sequence and its register row
   updated before any of its numbers are used.
2. Both axes measured on the same products, reported separately, never collapsed.
3. Depth-matched star statistics, with n and the faintest admitted amplitude on
   every number.
4. Attribution only where a discriminating test supports it; anything else
   reported as unattributed with the test that would settle it.
5. Every number carries its instrument and the box's `uptime`; guards and
   selftests green; `prompts/REPORT.md` updated and this file deleted in the same
   commit.

## Honest failure

**"The corners are worse and nothing here separates why" is a real result** and
better than a confident wrong mechanism — which is precisely what this question
produced last time and what cost the most. If the post-fix corpus shows no
corner degradation worth cropping for, say that: the compose fix may already have
taken most of it, and the owner is looking at a residue rather than the defect
they remember.
