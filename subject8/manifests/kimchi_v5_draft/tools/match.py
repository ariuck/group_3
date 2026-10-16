"""같은 Class crop 끼리 실물 재사용 탐지.
1) GPU: crop a 의 각 디스크립터가 crop b 안에서 가진 최대 유사도 -> 임계 이상 개수 = 후보 점수
2) 상위 후보만 BF knn + ratio test + RANSAC(부분 아핀) 으로 inlier 수 검증 -> pairs.csv
같은 사진 안의 다른 박스 쌍(= 확실히 다른 실물)도 같이 계산해 기준 분포로 쓴다."""
import sys, pickle
import numpy as np, pandas as pd, cv2, torch

d = sys.argv[1]
crops = pickle.load(open(d + "/crops.pkl", "rb"))
dev = "cuda"
bf = cv2.BFMatcher(cv2.NORM_L2)
rows = []
TOPK = 12
for cls in sorted(set(c["cls"] for c in crops)):
    idx = [i for i, c in enumerate(crops) if c["cls"] == cls and len(c["des"]) >= 8]
    des = np.concatenate([crops[i]["des"] for i in idx]).astype(np.float32)
    owner = torch.tensor(np.concatenate([[j] * len(crops[i]["des"]) for j, i in enumerate(idx)]), device=dev)
    D = torch.tensor(des, device=dev); D = (D / (D.norm(dim=1, keepdim=True) + 1e-6)).half()
    starts = np.cumsum([0] + [len(crops[i]["des"]) for i in idx])
    seen = set()
    for j, i in enumerate(idx):
        q = D[starts[j]:starts[j + 1]]
        sim = (q @ D.T).float()
        mx = torch.full((len(q), len(idx)), -1.0, device=dev)
        mx.scatter_reduce_(1, owner[None, :].expand(len(q), -1), sim, reduce="amax")
        mx[:, j] = -1
        score = (mx >= 0.90).sum(0)
        cand = torch.topk(score, min(TOPK, len(idx))).indices.tolist()
        # 같은 사진 안 다른 박스는 기준 분포용으로 항상 포함
        same_img = [k for k, ii in enumerate(idx) if crops[ii]["img_idx"] == crops[i]["img_idx"] and k != j]
        for k in set(cand) | set(same_img):
            key = (min(j, k), max(j, k))
            if key in seen:
                continue
            seen.add(key)
            ca, cb = crops[idx[key[0]]], crops[idx[key[1]]]
            ms = bf.knnMatch(ca["des"], cb["des"], k=2)
            good = [m for m, n in (x for x in ms if len(x) == 2) if m.distance < 0.8 * n.distance]
            ni = 0
            if len(good) >= 5:
                pa = ca["pts"][[m.queryIdx for m in good]]; pb = cb["pts"][[m.trainIdx for m in good]]
                M, inl = cv2.estimateAffinePartial2D(pa, pb, method=cv2.RANSAC, ransacReprojThreshold=5)
                ni = int(inl.sum()) if inl is not None else 0
            rows.append(dict(cls=cls, a=idx[key[0]], b=idx[key[1]], good=len(good), inliers=ni,
                             score=int(score[k]) if k in cand else -1,
                             hist=float(np.abs(ca["hist"] - cb["hist"]).sum()),
                             img_a=ca["img_idx"], img_b=cb["img_idx"], ga=ca["group"], gb=cb["group"]))
    print("class", cls, "crops", len(idx), "pairs checked", len(seen), flush=True)
pd.DataFrame(rows).to_csv(d + "/pairs.csv", index=False)
