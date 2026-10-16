import sys
import numpy as np, pandas as pd
d = sys.argv[1]
p = pd.read_csv(d + "/pairs.csv")
b = pd.read_csv(d + "/batches.csv")
df = pd.read_pickle(d + "/features.pkl")
img2batch = dict(zip(b.image, b.batch))
p["ba"] = [img2batch[df.image[i]] for i in p.img_a]
p["bb"] = [img2batch[df.image[i]] for i in p.img_b]
same = p[p.img_a == p.img_b]
cross = p[p.img_a != p.img_b]
print("same-image (different objects) inliers quantiles:", same.inliers.quantile([.5, .9, .99, .999, 1]).round(1).tolist(), len(same))
print("cross-image inliers quantiles:", cross.inliers.quantile([.5, .9, .99, .999, 1]).round(1).tolist(), len(cross))
for th in [10, 15, 20, 30]:
    s = cross[cross.inliers >= th]
    print(f"th {th}: pairs {len(s)}  same-batch {(s.ba==s.bb).sum()}  same-group-diff-batch {((s.ga==s.gb)&(s.ba!=s.bb)).sum()}  cross-group {(s.ga!=s.gb).sum()}  | same-image FP {(same.inliers>=th).sum()}")
TH = int(sys.argv[2]) if len(sys.argv) > 2 else 15
s = cross[cross.inliers >= TH]
print("\n== cross-group strong matches by class/group pair (th", TH, ")")
s2 = s[s.ga != s.gb].copy()
s2["gp"] = [f"{min(a,b)}-{max(a,b)}" for a, b in zip(s2.ga, s2.gb)]
print(s2.groupby(["cls", "gp"]).size().to_string())
print("\n== within-group cross-batch strong matches")
s3 = s[(s.ga == s.gb) & (s.ba != s.bb)].copy()
s3["bp"] = [f"{min(a,b)}~{max(a,b)}" for a, b in zip(s3.ba, s3.bb)]
print(s3.groupby(["cls", "bp"]).size().to_string())
s.to_csv(d + "/strong_pairs.csv", index=False)
