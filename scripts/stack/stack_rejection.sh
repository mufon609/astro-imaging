#!/usr/bin/env bash
# Single source of truth for the integration REJECTION clause, shared by every
# stack builder — the stack-step counterpart to calibrate_light.sh. Siril's
# rejection doctrine selects the algorithm by sub count: too few frames for a
# robust sigma estimate use percentile clipping; a middle count uses winsorized
# sigma clipping; a deep stack uses GESD, which rejects the outlier tail a
# winsorized sigma-clip leaves behind once the population is large. Routing every
# builder through this one function keeps the algorithm matched to the sub count,
# so no builder can hard-code one rejection that under-rejects a deep stack.
# scripts/stack/check_stack_rejection.sh enforces that no path bypasses it.
#
#   stack_rejection_for <n_frames>   ->  the `rej ...` clause for `stack`
# e.g.
#   stack r_lt $(stack_rejection_for "$N") -norm=addscale -output_norm -out=...
#
# n is the input sub count the builder has at stack-command generation (the
# registered count is <= this and lands in the same band in every real case;
# register runs in the same script, so the exact stacked count is not yet known).
stack_rejection_for() {
  local n=$1
  if   [ "$n" -le 6 ];  then echo "rej p 0.2 0.1"     # percentile clipping
  elif [ "$n" -le 50 ]; then echo "rej w 3 3"         # winsorized sigma clipping
  else                       echo "rej g 0.3 0.05"    # GESD (outlier fraction + significance)
  fi
}
