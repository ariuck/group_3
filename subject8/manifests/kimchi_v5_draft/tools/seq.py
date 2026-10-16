import sys, collections
import numpy as np, pandas as pd
d = sys.argv[1]
df = pd.read_pickle(d + "/features.pkl")
out = open(d + "/seq.txt", "w")
prev = None
for i, r in df.iterrows():
    c = collections.Counter(b[0] for b in r.boxes)
    cs = " ".join(f"{k}:{v}" for k, v in sorted(c.items()))
    area = np.median([b[3] * b[4] for b in r.boxes]) * 1000 if r.boxes else 0
    if prev is not None:
        gap = (r.ts - prev.ts).total_seconds()
        dh = int((r.dhash != prev.dhash).sum())
        hd = float(np.abs(r["hist"] - prev["hist"]).sum())
        px = float(np.abs(r.small - prev.small).mean())
    else:
        gap = dh = 0; hd = px = 0
    out.write(f"{i:3d} {r.group} {r.ts:%m%d %H:%M:%S} gap{int(gap):6d} n{len(r.boxes):2d} [{cs:12s}] a{area:5.1f} dh{dh:3d} hd{hd:.2f} px{px:.3f} br{r.bright:5.1f} {r.old_split}\n")
    prev = r
