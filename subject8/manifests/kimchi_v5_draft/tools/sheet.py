import sys, pickle
import numpy as np, pandas as pd, cv2
d = sys.argv[1]
crops = pickle.load(open(d + "/crops.pkl", "rb"))
s = pd.read_csv(d + "/strong_pairs.csv")
s = s[s.ga != s.gb]
picks = []
for (cls, ga, gb), g in s.groupby(["cls", "ga", "gb"]):
    if len(g) >= 3:
        picks.append(g.sort_values("inliers").iloc[len(g)//2])  # median-strength example
rows = []
for r in picks[:40]:
    a, b = crops[int(r.a)]["thumb"], crops[int(r.b)]["thumb"]
    a = cv2.resize(a, (128, 128)); b = cv2.resize(b, (128, 128))
    pad = np.full((128, 150, 3), 255, np.uint8)
    cv2.putText(pad, f"c{int(r.cls)} {r.ga}-{r.gb}", (2, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 0), 1)
    cv2.putText(pad, f"inl {int(r.inliers)}", (2, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 0), 1)
    rows.append(np.hstack([pad, a, b]))
cols = 2
while len(rows) % cols: rows.append(np.full_like(rows[0], 255))
grid = np.vstack([np.hstack(rows[i:i + cols]) for i in range(0, len(rows), cols)])
cv2.imwrite(d + "/sheet_cross.jpg", grid)
# 기준: 같은 사진 다른 박스 중 inlier 높은 것
p = pd.read_csv(d + "/pairs.csv"); same = p[p.img_a == p.img_b].sort_values("inliers", ascending=False).head(10)
rows = []
for _, r in same.iterrows():
    a = cv2.resize(crops[int(r.a)]["thumb"], (128, 128)); b = cv2.resize(crops[int(r.b)]["thumb"], (128, 128))
    pad = np.full((128, 150, 3), 255, np.uint8)
    cv2.putText(pad, f"SAME-IMG c{int(r.cls)} {r.ga}", (2, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 0), 1)
    cv2.putText(pad, f"inl {int(r.inliers)}", (2, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 0), 1)
    rows.append(np.hstack([pad, a, b]))
cv2.imwrite(d + "/sheet_sameimg.jpg", np.vstack([np.hstack(rows[i:i+2]) for i in range(0, 10, 2)]))
print(len(picks))
