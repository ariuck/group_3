"""촬영 묶음 안에서 '같은 이물 세트' 배치 경계 자동 추정 -> batches.csv
규칙: 이물 구성(Class 집합, 우연히 섞인 갈변·파 1개는 무시)이 2장 이상 이어서 바뀌면 끊는다.
구성이 매 장 바뀌는 구간(공통 풀에서 뽑아 섞은 장면)은 한 배치로 묶는다.
G12 는 사람(시트 D)이 정한 경계를 그대로 쓴다."""
import sys, csv, collections
from pathlib import Path
import numpy as np, pandas as pd

d = sys.argv[1]
df = pd.read_pickle(d + "/features.pkl")
ws = Path.home() / "group_3/subject8/manifests/manual_split/worksheet_D.csv"
human = {r["image"]: r["batch_id"] for r in csv.DictReader(open(ws, encoding="utf-8-sig")) if r["batch_id"].strip()}

def sig(boxes):
    c = collections.Counter(b[0] for b in boxes)
    s = {k for k, v in c.items() if k in (0, 1, 2, 3)}
    if c.get(5, 0) >= 3: s.add(5)
    if c.get(6, 0) >= 3: s.add(6)
    if len(s) > 1:  # 1개짜리 덤 이물은 구성에서 뺀다 (예: 파 5 + 가지 1)
        main = {k for k in s if c[k] >= 2}
        if main: s = main if sum(c[k] for k in s - main) <= 1 else s
    return frozenset(s)

out = []
for g, s in df.groupby("group", sort=False):
    s = s.sort_values("ts")
    names = s.image.tolist()
    if g == "G12" and all(n in human for n in names):
        out += [(n, g, human[n], "human(worksheet_D)") for n in names]
        continue
    sigs = [sig(b) for b in s.boxes]
    gaps = [0] + [(b - a).total_seconds() for a, b in zip(s.ts[:-1], s.ts[1:])]
    # run-length
    runs = []
    for i, x in enumerate(sigs):
        if runs and runs[-1][0] == x:
            runs[-1][2] = i
        else:
            runs.append([x, i, i])
    # 길이 1 run 이 앞뒤가 같은 구성 사이에 끼어 있으면 흡수
    changed = True
    while changed:
        changed = False
        for k in range(1, len(runs) - 1):
            if runs[k][2] == runs[k][1] and runs[k - 1][0] == runs[k + 1][0]:
                runs[k - 1][2] = runs[k + 1][2]; del runs[k:k + 2]; changed = True; break
    # 짧은 run(<=2)이 연속된 구간 = 섞인 장면 -> 하나로
    segs = []
    for r in runs:
        short = (r[2] - r[1] + 1) <= 2
        if segs and short and segs[-1]["mixed"]:
            segs[-1]["end"] = r[2]
        elif segs and short and (segs[-1]["end"] - segs[-1]["start"] + 1) <= 2:
            segs[-1]["end"] = r[2]; segs[-1]["mixed"] = True
        else:
            segs.append(dict(start=r[1], end=r[2], mixed=short, sig=r[0]))
    # 남은 1~2장짜리 조각은 이웃 중 구성이 더 가까운 쪽에 붙임
    merged = []
    for sg in segs:
        n = sg["end"] - sg["start"] + 1
        if merged and n <= 2 and not sg["mixed"]:
            merged[-1]["end"] = sg["end"]
        else:
            merged.append(sg)
    for k, sg in enumerate(merged):
        bid = f"{g}-{chr(97 + k) if k < 26 else 'z' + str(k)}"
        why = "mixed-pool" if sg["mixed"] else "set:" + "+".join(map(str, sorted(sg["sig"])))
        for i in range(sg["start"], sg["end"] + 1):
            out.append((names[i], g, bid, why))
b = pd.DataFrame(out, columns=["image", "group", "batch", "rule"])
b.to_csv(d + "/batches.csv", index=False)
t = b.groupby(["group", "batch", "rule"], sort=False).size()
print(t.to_string()); print("batches", b.batch.nunique())
