"""DIAGNOSTIC PROBE — what does sirilpy's `get_selection_stats()` actually
return on THIS build (siril 1.4.4 flatpak), and does its `channel` argument
select the channel (upstream #1673, closed 2025-06, claimed channel was
ignored and green always returned)?

    (from an .ssf that has an RGB image loaded)  pyscript probe_type.py

MEASURES ONLY. Wires nothing, gates nothing, reads no deliverable pixel in-house
— every number is Siril's own statistics reply. Exists to verify, by execution
rather than source reading, the two claims an upstream filing is about to make:
the function returns ImageStats (not the PSFStar its annotation declares), and
the object carries statistics fields rather than star-model fields.
"""
import json
import sys

import sirilpy


def main() -> int:
    out = {"_what": "get_selection_stats runtime type/behavior probe. MEASURES ONLY."}
    s = sirilpy.SirilInterface()
    s.connect()
    try:
        out["sirilpy_version"] = sirilpy.__version__
    except Exception as exc:  # noqa: BLE001 - report, never mask
        out["sirilpy_version"] = f"unreadable: {type(exc).__name__}: {exc}"

    shape = [2000, 2000, 128, 128]
    r = s.get_selection_stats(shape=shape, channel=0)
    out["shape_used"] = shape
    out["returned_type"] = type(r).__name__
    out["returned_module"] = type(r).__module__
    try:
        from sirilpy.models import ImageStats, PSFStar
        out["isinstance_ImageStats"] = isinstance(r, ImageStats)
        out["isinstance_PSFStar"] = isinstance(r, PSFStar)
    except Exception as exc:  # noqa: BLE001
        out["isinstance_check"] = f"import failed: {type(exc).__name__}: {exc}"
    try:
        out["returned_fields"] = sorted(vars(r).keys())
    except TypeError:
        out["returned_fields"] = sorted(
            a for a in dir(r) if not a.startswith("_") and not callable(getattr(r, a)))

    # Channel behavior (#1673): on an SPCC-calibrated RGB stack the three
    # channels' medians differ, so three identical replies = channel ignored.
    med = {}
    for ch in (0, 1, 2):
        rc = s.get_selection_stats(shape=shape, channel=ch)
        med[str(ch)] = getattr(rc, "median", None)
    out["median_by_channel"] = med
    vals = [v for v in med.values() if v is not None]
    out["channel_arg_effective"] = len(set(vals)) > 1 if len(vals) == 3 else "inconclusive"

    print("PROBE_JSON " + json.dumps(out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
