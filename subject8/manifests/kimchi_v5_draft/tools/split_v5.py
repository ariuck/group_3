"""kimchi_v5 초안: 촬영 묶음(session) 통째 배정 + G00 만 시간순 블록 예외. 검증 지표 출력."""
import sys, json, collections, pickle
import numpy as np, pandas as pd

d = sys.argv[1]
df = pd.read_pickle(d + "/features.pkl")
bt = pd.read_csv(d + "/batches.csv")
df["batch"] = df.image.map(dict(zip(bt.image, bt.batch)))

SESSION = {
    "train": ["G02", "G03", "G04", "G06", "G08", "G09", "G16", "G17", "G01"],
    "val": ["G07", "G11", "G12"],
    "test": ["G05", "G14"],
    "bridge_holdout": ["G10", "G13", "G15"],
}
G00 = {"val": [(0, 2), (41, 43)], "test": [(19, 21), (44, 46)], "bridge_holdout": [(22, 24), (47, 49)]}

split = {}
for s, gs in SESSION.items():
    for g in gs:
        for n in df[df.group == g].image: split[n] = s
g0 = df[df.group == "G00"].sort_values("ts").image.tolist()
for i, n in enumerate(g0):
    split[n] = "train"
    for s, rngs in G00.items():
        if any(a <= i <= b for a, b in rngs): split[n] = s
df["split"] = df.image.map(split)
assert df.split.notna().all()

def table(col):
    rows = []
    for s in ["train", "val", "test", "bridge_holdout"]:
        x = df[df[col] == s]
        box = collections.Counter(b[0] for bs in x.boxes for b in bs)
        img = collections.Counter(c for bs in x.boxes for c in {b[0] for b in bs})
        rows.append(dict(split=s, images=len(x), sessions=x.group.nunique(), batches=x.batch.nunique(),
                         **{f"box_c{k}": box.get(k, 0) for k in [0, 1, 2, 3, 5, 6]},
                         **{f"img_c{k}": img.get(k, 0) for k in [0, 1, 2, 3, 5, 6]}))
    return pd.DataFrame(rows)

out = {}
for col in ["old_split", "split"]:
    t = table(col)
    print(f"\n=== {col} ===\n" + t.to_string(index=False))
    # 누수 지표
    sh = df.groupby("group")[col].nunique()
    split_sessions = sh[sh > 1].index.tolist()
    shb = df.groupby("batch")[col].nunique()
    print("세션이 여러 역할로 나뉜 것:", split_sessions, "| 배치가 나뉜 것:", shb[shb > 1].index.tolist())
    for s in ["val", "test", "bridge_holdout"]:
        x = df[df[col] == s]
        tr_groups = set(df[df[col] == "train"].group)
        print(f"  {s}: Train 과 같은 촬영 묶음 출신 {x.group.isin(tr_groups).sum()}/{len(x)}장")
    # 이미지 근접 중복(dHash<=40) 교차 split
    H = np.stack(df.dhash.values); D = (H[:, None] != H[None]).sum(-1); np.fill_diagonal(D, 999)
    ii, jj = np.where(np.triu(D <= 40))
    print("  dHash<=40 쌍 중 split 이 다른 것:", sum(df[col][i] != df[col][j] for i, j in zip(ii, jj)), "/", len(ii))
    # 실물 재사용: 평가 crop 중 train crop 과 강한 SIFT 매칭(inlier>=20)이 있는 비율
    p = pd.read_csv(d + "/pairs.csv"); p = p[(p.img_a != p.img_b) & (p.inliers >= 20)]
    crops = pickle.load(open(d + "/crops.pkl", "rb"))
    cs = np.array([df[col][c["img_idx"]] for c in crops])
    linked = collections.defaultdict(set)
    for a, b in zip(p.a, p.b):
        if cs[a] == "train" and cs[b] != "train": linked[cs[b]].add(b)
        if cs[b] == "train" and cs[a] != "train": linked[cs[a]].add(a)
    for s in ["val", "test", "bridge_holdout"]:
        print(f"  {s}: 박스 {int((cs == s).sum())}개 중 Train 실물과 강하게 매칭 {len(linked[s])}개 ({len(linked[s]) / max(1, (cs == s).sum()) * 100:.1f}%)")
df[["image", "group", "batch", "old_split", "split"]].to_csv(d + "/kimchi_v5_split.csv", index=False)
