"""kimchi_v4 900장 특징 추출 -> features.pkl (scratchpad)"""
import sys, glob, os, pickle
from pathlib import Path
from datetime import datetime
import numpy as np, pandas as pd, cv2

ROOT = Path.home() / "group_3/subject8"
OUT = Path(sys.argv[1])

man = pd.read_csv(ROOT / "manifests/split_manifest.csv", encoding="utf-8-sig")
imgs = {}
for p in list((ROOT / "data/yolo/images").rglob("*.jpg")) + list((ROOT / "data/bridge_holdout/images").glob("*.jpg")):
    imgs[p.name] = p
lbls = {}
for p in list((ROOT / "data/yolo/labels").rglob("*.txt")) + list((ROOT / "data/bridge_holdout/labels").glob("*.txt")):
    lbls[p.name] = p

def dhash(g):
    s = cv2.resize(g, (17, 16), interpolation=cv2.INTER_AREA)
    return (s[:, 1:] > s[:, :-1]).flatten()

rows = []
for _, r in man.iterrows():
    name = r["이미지 파일명"]
    stem = name[:-4]
    ts = datetime.strptime(stem[:13], "%y%m%d_%H%M%S")
    boxes = []
    for line in open(lbls[stem + ".txt"]).read().split("\n"):
        t = line.split()
        if len(t) == 5:
            boxes.append([int(t[0])] + [float(x) for x in t[1:]])
    img = cv2.imread(str(imgs[name]), cv2.IMREAD_REDUCED_COLOR_8)
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    hist = cv2.calcHist([hsv], [0, 1], None, [16, 8], [0, 180, 0, 256]).flatten()
    hist /= hist.sum()
    small = cv2.resize(img, (64, 36), interpolation=cv2.INTER_AREA).astype(np.float32).flatten() / 255
    rows.append(dict(
        image=name, ts=ts, group=r["capture_group"], old_split=r["split"], scene=r["이미지 유형"],
        orig_split=r["원래 split"], boxes=boxes, dhash=dhash(g), hist=hist, small=small,
        bright=float(g.mean()), contrast=float(g.std()), shape=img.shape[:2],
    ))
df = pd.DataFrame(rows).sort_values("ts").reset_index(drop=True)
df.to_pickle(OUT)
print(len(df), "images; missing imgs", len(set(man["이미지 파일명"]) - set(imgs)))
