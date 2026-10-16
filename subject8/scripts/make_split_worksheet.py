"""수동 분할(kimchi_v5) 1단계 준비 — 6명이 나눠 볼 작업 시트(CSV)와 확인용 사진판(JPG)을 만든다.

    python scripts/make_split_worksheet.py              # 작업 시트 6개 + 사진판
    python scripts/make_split_worksheet.py --no-sheets  # 작업 시트만 (사진이 없는 PC)

결과:
    manifests/manual_split/worksheet_<A~F>.csv   담당자별 작업 시트 (Git 에 올림 — 사진 없음)
    demo/manual_split/<담당>_<묶음>.jpg           촬영 순서대로 놓은 썸네일 + 정답 박스 (회사 사진 → Git 제외)

작업 방법은 docs/project/manual_split_guide.md 를 따른다.
시트에는 기존 Split(train/val/...) 과 모델 성능을 일부러 넣지 않는다 — 묶음은 사진만 보고 정한다.
"""
import argparse
import csv
import os
import sys
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
os.chdir(PROJECT_ROOT)

from src.constants import CLASS_NAMES, LABEL_FIX_DIRS  # noqa: E402
from src.inference import COLORS, load_gt  # noqa: E402
from src.split_builder import SplitBuilder  # noqa: E402

LABEL_VERSION = "kimchi_v4"     # 라벨은 v4 그대로 쓴다 (이번 작업은 분할만 다시 정함)
OUT_DIR = PROJECT_ROOT / "manifests" / "manual_split"
SHEET_DIR = PROJECT_ROOT / "demo" / "manual_split"
GAP_HINT_SEC = 120              # 이 이상 끊기면 사진판에 빨간색으로 표시 (새 묶음 후보)

# 담당자 배정: 촬영 묶음 경계를 따라 6명에게 약 150장씩. G17(이물 단독)은 배경이 같아 빨리 끝나므로 F 가 200장
ASSIGNEES = {
    "A": ["G00", "G01", "G02", "G03", "G04"],   # 04-10            150장
    "B": ["G05", "G06"],                        # 04-11 오전       124장
    "C": ["G07", "G08", "G09"],                 # 04-11 오후       126장
    "D": ["G10", "G11", "G12"],                 # 04-24 오전~13시  150장
    "E": ["G13", "G14", "G15"],                 # 04-24 오후       150장
    "F": ["G16", "G17"],                        # 04-24 마지막 + 05-13 이물 단독 200장
}
REVIEWER = {"A": "B", "B": "A", "C": "D", "D": "C", "E": "F", "F": "E"}  # 교차 확인 짝
FILL_COLUMNS = ["batch_id", "same_object_as", "note", "review_ok", "review_note"]


def clock(name: str):
    """250410_144403911987.jpg → datetime"""
    return datetime.strptime(name[:13], "%y%m%d_%H%M%S")


def collect(builder: SplitBuilder) -> pd.DataFrame:
    df = builder.assign_capture_groups(pd.read_csv(builder.meta_csv, encoding="utf-8-sig"))
    fix_dir = builder.label_fix_dir(LABEL_VERSION)
    labels = {p.name: p for p in builder.labels_dir.rglob("*.txt")}
    rows = []
    for _, r in df.iterrows():
        img, lbl = r["이미지 파일명"], r["라벨(TXT) 파일명"]
        src = fix_dir / lbl if fix_dir is not None and (fix_dir / lbl).is_file() else labels.get(lbl)
        boxes = load_gt(src) if src else []
        counts = {}
        for c, *_ in boxes:
            counts[c] = counts.get(c, 0) + 1
        rows.append({"image": img, "capture_group": r["capture_group"], "time": clock(img),
                     "scene": r["이미지 유형"], "n_boxes": len(boxes),
                     "classes": " ".join(f"{c}:{n}" for c, n in sorted(counts.items())), "boxes": boxes})
    out = pd.DataFrame(rows).sort_values("time").reset_index(drop=True)
    out["no"] = out.index + 1
    out["gap_sec"] = out["time"].diff().dt.total_seconds().fillna(0).astype(int)
    out.loc[out["capture_group"] != out["capture_group"].shift(), "gap_sec"] = 0  # 묶음 첫 장은 0
    return out


def write_sheets(df: pd.DataFrame):
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for who, groups in ASSIGNEES.items():
        part = df[df["capture_group"].isin(groups)]
        path = OUT_DIR / f"worksheet_{who}.csv"
        if path.exists():
            print(f" 건너뜀 (이미 있음, 작성 중일 수 있어 덮어쓰지 않음): {path.relative_to(PROJECT_ROOT)}")
            continue
        with path.open("w", encoding="utf-8-sig", newline="") as f:
            w = csv.writer(f)
            w.writerow(["no", "image", "capture_group", "date", "time", "gap_sec", "n_boxes", "classes", "scene",
                        "assignee", "reviewer", *FILL_COLUMNS])
            for r in part.itertuples(index=False):
                w.writerow([r.no, r.image, r.capture_group, r.time.strftime("%y%m%d"), r.time.strftime("%H:%M:%S"),
                            r.gap_sec, r.n_boxes, r.classes, r.scene, who, REVIEWER[who], *[""] * len(FILL_COLUMNS)])
        print(f" 작업 시트 {who}: {len(part):>3}장 ({', '.join(groups)}) -> {path.relative_to(PROJECT_ROOT)}")


def tile(path: Path, boxes, label: str, gap: int, w=320):
    img = cv2.imread(str(path), cv2.IMREAD_REDUCED_COLOR_8)
    if img is None:
        img = np.zeros((180, w, 3), np.uint8)
    img = cv2.resize(img, (w, int(img.shape[0] * w / img.shape[1])))
    h = img.shape[0]
    for c, x1, y1, x2, y2 in boxes:
        cv2.rectangle(img, (int(x1 * w), int(y1 * h)), (int(x2 * w), int(y2 * h)), COLORS.get(c, (255, 255, 255)), 1)
    bar_color = (0, 0, 200) if gap >= GAP_HINT_SEC else (40, 40, 40)
    cv2.rectangle(img, (0, 0), (w, 18), bar_color, -1)
    cv2.putText(img, label, (4, 13), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (255, 255, 255), 1, cv2.LINE_AA)
    return img


def write_contact_sheets(df: pd.DataFrame, cols=6):
    images_dir = SplitBuilder(PROJECT_ROOT).images_dir
    images = {p.name: p for p in images_dir.rglob("*.jpg")}
    if not images:
        print(f" 사진이 없어 사진판을 건너뜀 ({images_dir})")
        return
    SHEET_DIR.mkdir(parents=True, exist_ok=True)
    legend = " ".join(f"{c}={n}" for c, n in CLASS_NAMES.items() if c != 4)
    for who, groups in ASSIGNEES.items():
        for g in groups:
            part = df[df["capture_group"] == g]
            tiles = [tile(images[r.image], r.boxes, f"#{r.no} {r.time:%H:%M:%S} +{r.gap_sec}s  {r.classes}", r.gap_sec)
                     for r in part.itertuples(index=False)]
            th, tw = tiles[0].shape[:2]
            while len(tiles) % cols:
                tiles.append(np.zeros((th, tw, 3), np.uint8))
            tiles = [cv2.resize(t, (tw, th)) for t in tiles]
            body = np.vstack([np.hstack(tiles[i:i + cols]) for i in range(0, len(tiles), cols)])
            head = np.full((26, body.shape[1], 3), 255, np.uint8)
            cv2.putText(head, f"{who} {g}  {len(part)} photos  (red bar = gap >= {GAP_HINT_SEC}s)  class: {legend}",
                        (6, 18), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1, cv2.LINE_AA)
            out = SHEET_DIR / f"{who}_{g}.jpg"
            cv2.imwrite(str(out), np.vstack([head, body]), [cv2.IMWRITE_JPEG_QUALITY, 85])
        print(f" 사진판 {who}: {len(groups)}장 -> {SHEET_DIR.relative_to(PROJECT_ROOT)}/{who}_*.jpg")


def main():
    ap = argparse.ArgumentParser(description="수동 분할 작업 시트·사진판 만들기")
    ap.add_argument("--no-sheets", action="store_true", help="사진판(JPG)은 만들지 않음")
    args = ap.parse_args()

    df = collect(SplitBuilder(project_root=PROJECT_ROOT))
    assigned = sum(ASSIGNEES.values(), [])
    missing = sorted(set(df["capture_group"]) - set(assigned))
    if missing:
        sys.exit(f"담당자가 없는 촬영 묶음: {missing}")
    print(f" 사진 {len(df)}장 · 촬영 묶음 {df['capture_group'].nunique()}개 · 라벨 {LABEL_VERSION}")
    write_sheets(df)
    if not args.no_sheets:
        write_contact_sheets(df)


if __name__ == "__main__":
    main()
