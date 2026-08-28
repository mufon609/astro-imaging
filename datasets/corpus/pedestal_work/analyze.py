#!/usr/bin/env python3
"""Pedestal zero-point arithmetic — in-house arithmetic over Siril's OWN numbers only.

Inputs (never a pixel):
  seqstat_*.csv           Siril 1.4.4 `seqstat <seq> <csv> full` on `link`ed symlink
                          sequences of members / products (mean median sigma min max
                          bgnoise avgDev mad sqrtbwmv location scale; [0,1] units).
  r_s_.seq M lines        Siril's cached normalization statistics on the REGISTERED
                          r_ copies (what `stack -norm=addscale` actually used), from a
                          kept compose scratch (web/results/<session>/.compose_<tag>/seq/).

Model (Siril 1.4.4 source, tag 1.4.4):
  normalization.c compute_factors_from_estimators + median_and_mean.c:1628:
      member pixel x -> a_m*(x - loc_m) + loc_ref,   a_m = scale_ref/scale_m, per channel
  median_and_mean.c:556-582 norm_to_0_1_range: ONE (min,max) over all channels,
      zeros skipped, every non-zero pixel -> (v - min)/(max - min)
  => product location O_c = (loc_ref,c - mu) / D,   mu = darkest non-zero pixel of the
     pre-output-norm composite (any channel), D = max - min ([0,1] units).
  Three channels, two unknowns: D from each channel pair must agree (the closure test).

Units: x65535 ("ADU16") for locations / mu; D dimensionless ([0,1] units).
Removal condition: Siril reporting its output-normalization min/max (then mu, D are
read, not derived).
"""
import csv, os, re, sys
K = 65535.0
HERE = os.path.dirname(os.path.abspath(__file__))
COLS = "image layer mean median sigma min max bgnoise avgDev mad sqrtbwmv location scale".split()

def read_csv(path):
    if not os.path.isabs(path):
        path = os.path.join(HERE, path)
    out = {}
    with open(path) as f:
        for row in csv.reader(f, delimiter="\t"):
            if not row or not row[0].strip().isdigit():
                continue
            d = dict(zip(COLS, row))
            out[(int(d["image"]), int(d["layer"]))] = {k: float(d[k]) for k in COLS[2:]}
    return out

def read_M(seqpath):
    """M<layer>-<image0> total ngoodpix mean median sigma avgDev mad sqrtbwmv location scale min max normValue bgnoise
    Returns ({(image1, layer): stats}, reference_image1) — 1-based image indices."""
    names = "total ngoodpix mean median sigma avgDev mad sqrtbwmv location scale min max normValue bgnoise".split()
    M, ref = {}, None
    for line in open(seqpath):
        if line.startswith("S "):
            ref = int(line.split()[6]) + 1        # S 'name' beg number selnum fixed reference_image version variable fz drizzle
        m = re.match(r"M(\d)-(\d+) (.*)", line.strip())
        if m:
            M[(int(m.group(2)) + 1, int(m.group(1)))] = dict(zip(names, [float(x) for x in m.group(3).split()]))
    return M, ref

def anchors(stats, n, ref):
    """c_m = a_m*loc_m per member/channel (ADU16) and the reference's location."""
    out = {}
    for img in range(1, n + 1):
        out[img] = [(stats[(img, l)]["location"] * K,
                     stats[(ref, l)]["scale"] / stats[(img, l)]["scale"],
                     stats[(ref, l)]["scale"] / stats[(img, l)]["scale"] * stats[(img, l)]["location"] * K)
                    for l in range(3)]
    return out

def solve(loc_ref, O):
    """O_c*D + mu = loc_ref,c.  Returns D from (G-R, B-R, G-B) and mu per channel for each."""
    D = [(loc_ref[1] - loc_ref[0]) / (O[1] - O[0]),
         (loc_ref[2] - loc_ref[0]) / (O[2] - O[0]),
         (loc_ref[1] - loc_ref[2]) / (O[1] - O[2])]
    mu = [[loc_ref[l] - O[l] * d for l in range(3)] for d in D]
    return D, mu

def closure(label, loc_ref, O):
    D, mu = solve(loc_ref, O)
    print(f"{label}: loc_ref {loc_ref[0]:.2f}/{loc_ref[1]:.2f}/{loc_ref[2]:.2f}  O {O[0]:.2f}/{O[1]:.2f}/{O[2]:.2f}"
          f"  D(G-R,B-R,G-B) {D[0]:.4f}/{D[1]:.4f}/{D[2]:.4f}  mu {mu[0][0]:.2f}/{mu[1][1]:.2f}/{mu[2][2]:.2f}")
    return D, mu

def predict_setref(stats, ref, newref, O):
    """E1: same registered copies, normalization reference ref -> newref.
    Assumes the global min stays in R (ch0) and the max in G (ch1)."""
    lr = [stats[(ref, l)]["location"] * K for l in range(3)]; sr = [stats[(ref, l)]["scale"] for l in range(3)]
    ln = [stats[(newref, l)]["location"] * K for l in range(3)]; sn = [stats[(newref, l)]["scale"] for l in range(3)]
    D, mu = solve(lr, O); D, mu = D[0], mu[0][0]; Mx = D * K + mu
    kap = [sn[l] / sr[l] for l in range(3)]
    mu2 = kap[0] * (mu - lr[0]) + ln[0]; Mx2 = kap[1] * (Mx - lr[1]) + ln[1]; D2 = (Mx2 - mu2) / K
    O2 = [(ln[l] - mu2) / D2 for l in range(3)]
    return O2, [O2[l] / O[l] for l in range(3)], [ln[l] / lr[l] for l in range(3)], mu2, D2

if __name__ == "__main__":
    # usage: analyze.py <members.csv> <n> <ref> <products.csv> <product_index> [<r_s_.seq>]
    mem = read_csv(sys.argv[1]); n = int(sys.argv[2]); ref = int(sys.argv[3])
    pr = read_csv(sys.argv[4]); pidx = int(sys.argv[5])
    st = mem
    if len(sys.argv) > 6:
        M, mref = read_M(sys.argv[6]); st = M
        print(f"M lines: reference image {mref} (given {ref})")
    A = anchors(st, n, ref)
    O = [pr[(pidx, l)]["location"] * K for l in range(3)]
    closure(f"{os.path.basename(sys.argv[4])}#{pidx}", [A[ref][l][0] for l in range(3)], O)
