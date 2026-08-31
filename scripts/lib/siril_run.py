#!/usr/bin/env python3
"""Single source of truth for INVOKING Siril from python — the peer of
scripts/lib/siril_run.sh, taking the SAME lock file so the shell and python
halves of a chain serialize against each other.

    import siril_run
    r = siril_run.run(["-d", work, "-s", ssf], capture_output=True, text=True)

`run()` forwards every keyword to subprocess.run and returns its
CompletedProcess, so a call site changes only its command construction.
`SIRIL` is exported for anything that still needs the raw argv prefix.

WHY: the flatpak Siril tears down its per-app instance dir when a short-lived
instance exits exactly as another is starting its sandbox — "bwrap: Can't get
type of source /run/user/1000/.flatpak/org.siril.Siril/tmp". Measured once in
~150 paired invocations, it kills the caller mid-chain and prints nothing
useful. Mechanism, the rejected retry alternative, and the removal condition
are documented in siril_run.sh; this module only mirrors the lock.

The lock is released by the kernel when the process dies, so it cannot go
stale, and the wait is deliberately unbounded — a legitimate stack holds it for
an hour and waiting is the correct behaviour.
"""
import fcntl
import os
import subprocess
import sys

SIRIL = ["flatpak", "run", "--command=siril-cli", "org.siril.Siril"]
LOCK = os.environ.get("SIRIL_LOCK",
                      os.path.expanduser("~/.cache/astro-imaging/siril-cli.lock"))


def run(args, **kw):
    """Run siril-cli with `args`, serialized against every other holder."""
    os.makedirs(os.path.dirname(LOCK), exist_ok=True)
    with open(LOCK, "a") as fh:            # append: never truncates
        try:
            fcntl.flock(fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            print("[siril_run] another Siril job holds the lock — waiting",
                  file=sys.stderr)
            fcntl.flock(fh, fcntl.LOCK_EX)
        return subprocess.run(SIRIL + list(args), **kw)
        # the with-block closes fh on exit, which releases the lock
