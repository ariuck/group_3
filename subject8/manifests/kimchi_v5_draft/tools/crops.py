"""모든 박스 crop -> SIFT 디스크립터 저장 (crops.pkl)"""
import sys, pickle
from pathlib import Path
import numpy as np, pandas as pd, cv2

d = sys.argv[1]
ROOT = Path.home() / "group_3/subject8"
df = pd.read_pickle(d + "/features.pkl")
imgs = {p.name: p for p in list((ROOT / "data/yolo/images").rglob("*.jpg")) + list((ROOT / "data/bridge_holdout/images").glob("*.jpg"))}
sift = cv2.SIFT_create(nfeatures=400)
out = []
for i, r in df.iterrows():
    im = cv2.imread(str(imgs[r.image]), cv2.IMREAD_REDUCED_COLOR_2)  # ~1920 wide
    H, W = im.shape[:2]
    for k, (c, x, y, w, h) in enumerate(r.boxes):
        m = 0.15
        x0, x1 = int((x - w / 2 * (1 + m)) * W), int((x + w / 2 * (1 + m)) * W)
        y0, y1 = int((y - h / 2 * (1 + m)) * H), int((y + h / 2 * (1 + m)) * H)
        crop = im[max(0, y0):min(H, y1), max(0, x0):min(W, x1)]
        if crop.size == 0:
            continue
        s = 256 / max(crop.shape[:2])
        crop = cv2.resize(crop, None, fx=s, fy=s, interpolation=cv2.INTER_AREA if s < 1 else cv2.INTER_CUBIC)
        g = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
        kp, des = sift.detectAndCompute(g, None)
        hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
        hist = cv2.calcHist([hsv], [0, 1], None, [18, 8], [0, 180, 0, 256]).flatten(); hist /= hist.sum() + 1e-9
        out.append(dict(img_idx=i, image=r.image, group=r.group, box=k, cls=c, wpx=w * W * 2, hpx=h * H * 2,
                        pts=np.array([p.pt for p in kp], np.float32) if kp else np.zeros((0, 2), np.float32),
                        des=des if des is not None else np.zeros((0, 128), np.float32), hist=hist,
                        thumb=cv2.resize(crop, (64, 64))))
pickle.dump(out, open(d + "/crops.pkl", "wb"))
print(len(out), "crops")
