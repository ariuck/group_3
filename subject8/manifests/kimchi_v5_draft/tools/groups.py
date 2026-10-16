import sys, collections
import numpy as np, pandas as pd
d = sys.argv[1]
df = pd.read_pickle(d + "/features.pkl")
rows = []
for g, s in df.groupby("group"):
    box = collections.Counter(); img = collections.Counter()
    for bs in s.boxes:
        c = collections.Counter(b[0] for b in bs)
        box.update(c); img.update(set(c))
    rows.append(dict(group=g, n=len(s), **{f"b{k}": box.get(k, 0) for k in [0,1,2,3,5,6]}, **{f"i{k}": img.get(k, 0) for k in [5,6]}))
t = pd.DataFrame(rows)
t.loc["sum"] = t.sum(numeric_only=True)
print(t.to_string())
# G17 near dups
s = df[df.group == "G17"]
H = np.stack(s.dhash.values)
D = (H[:, None, :] != H[None, :, :]).sum(-1)
print("G17 pairs dh<=10:", ((D <= 10).sum() - len(s)) // 2)
# global near-dup by dhash across all
H = np.stack(df.dhash.values); D = (H[:, None, :] != H[None, :, :]).sum(-1)
np.fill_diagonal(D, 999)
for th in [10, 20, 30, 40, 50]:
    ii, jj = np.where(np.triu(D <= th))
    cross = sum(df.group[i] != df.group[j] for i, j in zip(ii, jj))
    print(f"dh<={th}: pairs {len(ii)}, cross-group {cross}, non-G17 {sum(df.group[i]!='G17' for i in ii)}")
