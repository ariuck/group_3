"""5일차 이미지 Detection — Weight 로 사진을 예측하고 정답(GT)과 나란히 그려 비교한다 (가이드 18장, 6일차 실패분석 준비).

    python scripts/08_predict_images.py                               # 공식 Baseline × 그 Version 의 Validation
    python scripts/08_predict_images.py --model exp002_v5_imgsz1920   # 다른 모델 (실행 이름 · final · .pt 경로)
    python scripts/08_predict_images.py --conf 0.5 --limit 10         # 기준을 바꿔 10장만
    python scripts/08_predict_images.py --source 사진.jpg               # 사진 1장 (라벨이 있으면 비교도)

모델 이름만 주면 imgsz · Validation 폴더 · 타일링 여부를 src/registry.py 로 알아서 정한다.

결과 (runs/predict/<name>/ — Git 제외, 기본 name = <실행>_val):
    compare/*.jpg      왼쪽 정답 · 오른쪽 예측 (TP 실선, CLASS_ERROR 노랑 테두리, FP 빨강 테두리, 놓친 정답 빨강 X)
    predictions.csv    예측 박스 전체 (사진, Class, confidence, 좌표, 판정)
    per_image.csv      사진별 정답 수 · 예측 수 · TP · CLASS_ERROR · FP · FN

Frozen Test(data/yolo/images/test)와 Bridge Holdout 사진은 --allow-test 없이는 예측하지 않는다.
"""
import argparse
import csv
import os
import sys
from collections import Counter
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
os.chdir(PROJECT_ROOT)

import cv2  # noqa: E402
from ultralytics import YOLO  # noqa: E402

from src import registry  # noqa: E402
from src.inference import draw_comparison, load_gt, match  # noqa: E402
from src.split_builder import SplitBuilder  # noqa: E402
from src.tiling import predict_full  # noqa: E402
from src.train_detector import rel  # noqa: E402

IMAGE_SUFFIXES = (".jpg", ".jpeg", ".png")
# 모든 Version 의 Frozen Test · Bridge Holdout (data/yolo*/images/test, data/bridge_holdout*)
PROTECTED = [*(PROJECT_ROOT / "data").glob("yolo*/images/test"), *(PROJECT_ROOT / "data").glob("bridge_holdout*")]


def label_for(img: Path) -> Path:
    """.../images/<split>/a.jpg → .../labels/<split>/a.txt (YOLO 규칙)"""
    parts = list(img.parts)
    if "images" in parts:
        i = len(parts) - 1 - parts[::-1].index("images")
        parts[i] = "labels"
    return Path(*parts).with_suffix(".txt")


def main():
    ap = argparse.ArgumentParser(description="Weight 로 사진 예측 + 정답 비교")
    ap.add_argument("--model", default="baseline", help="baseline · final · 실행 이름 (models/README.md) · .pt 경로")
    ap.add_argument("--source", help="사진 폴더 또는 사진 1장 (기본: 그 모델 Version 의 Validation)")
    ap.add_argument("--conf", type=float, default=0.25, help="이 확신도 이상인 예측만 사용")
    ap.add_argument("--imgsz", type=int, help="기본: 그 모델을 학습할 때의 imgsz")
    ap.add_argument("--name", help="기본: <실행>_val")
    ap.add_argument("--limit", type=int, default=0, help="앞에서부터 N장만 (0 = 전부)")
    ap.add_argument("--allow-test", action="store_true", help="Frozen Test·Bridge 사진 예측 허용 (8일차 이후)")
    args = ap.parse_args()

    weights, run = registry.resolve(args.model)
    imgsz = args.imgsz or registry.run_args(run)["imgsz"]
    tiles = registry.run_tiles(run)
    yolo_dir = SplitBuilder(PROJECT_ROOT, registry.run_version(run)).yolo_dir
    source = Path(args.source or yolo_dir / "images" / "val").resolve()
    if not args.allow_test and any(source == p.resolve() or p.resolve() in source.parents for p in PROTECTED):
        sys.exit("Frozen Test / Bridge Holdout 사진입니다. Final Model 확정 전에는 보지 않습니다 (--allow-test).")
    images = [source] if source.is_file() else sorted(p for p in source.iterdir() if p.suffix.lower() in IMAGE_SUFFIXES)
    if args.limit:
        images = images[:args.limit]
    if not images:
        sys.exit(f"사진이 없습니다: {source}")

    out = PROJECT_ROOT / "runs" / "predict" / (args.name or f"{run}_val")
    (out / "compare").mkdir(parents=True, exist_ok=True)
    model = YOLO(str(weights))
    names = model.names

    print("=" * 65)
    print(f" [Subject 08] Day 5: Prediction  {run} ({rel(Path(weights))})  imgsz {imgsz}"
          + (f" · 타일 {tiles[0][0]}×{tiles[0][1]}" if tiles else "") + f"  conf≥{args.conf}")
    print(f" 사진 {len(images)}장  ({rel(source)})")
    print("=" * 65)

    def predictions():
        """(사진 경로, [(cls, conf, x1, y1, x2, y2)] 비율 좌표) — 타일링 모델은 조각 예측을 합친다"""
        if not tiles:
            for path in images:     # 한 장씩 — 목록째 넘기면 큰 imgsz(2240)에서 사진이 한꺼번에 묶여 GPU 메모리가 넘친다
                r = model.predict(source=str(path), conf=args.conf, imgsz=imgsz, verbose=False)[0]
                yield Path(r.path), [(int(c), float(p), *map(float, b)) for c, p, b in zip(r.boxes.cls, r.boxes.conf, r.boxes.xyxyn)]
            return
        for p in images:
            im = cv2.imread(str(p))
            h, w = im.shape[:2]
            d = predict_full(model, im, imgsz, tiles, conf=args.conf)
            yield p, [(int(c), float(s), x1 / w, y1 / h, x2 / w, y2 / h) for x1, y1, x2, y2, s, c in d]

    pred_rows, image_rows = [], []
    totals = Counter()
    fn_by_class, fp_by_class, cls_err_pairs = Counter(), Counter(), Counter()
    for img, preds in predictions():
        gt = load_gt(label_for(img))
        res = match(gt, preds)

        for i, (c, p, *b) in enumerate(preds):
            kind, j = res["pred_kind"][i]
            pred_rows.append({"image": img.name, "class_id": c, "class_name": names[c], "conf": round(p, 3),
                              "x1": round(b[0], 4), "y1": round(b[1], 4), "x2": round(b[2], 4), "y2": round(b[3], 4),
                              "result": kind, "gt_class": gt[j][0] if j is not None else ""})
            if kind == "FP":
                fp_by_class[c] += 1
            elif kind == "CLASS_ERROR":
                cls_err_pairs[(gt[j][0], c)] += 1
        for j in res["fn"]:
            fn_by_class[gt[j][0]] += 1

        image_rows.append({"image": img.name, "gt": len(gt), "pred": len(preds), "tp": res["tp"],
                           "class_error": res["class_error"], "fp": res["fp"], "fn": res["fn_count"]})
        for k in ("tp", "class_error", "fp"):
            totals[k] += res[k]
        totals["fn"] += res["fn_count"]
        totals["gt"] += len(gt)
        draw_comparison(img, gt, preds, res, names, out / "compare" / f"{img.stem}.jpg")

    for fname, rows in (("predictions.csv", pred_rows), ("per_image.csv", image_rows)):
        if rows:
            with (out / fname).open("w", encoding="utf-8-sig", newline="") as f:
                w = csv.DictWriter(f, fieldnames=list(rows[0]))
                w.writeheader()
                w.writerows(rows)

    has_gt = totals["gt"] > 0
    print(f"\n 예측 박스 {len(pred_rows)}개" + (f" / 정답 박스 {totals['gt']}개" if has_gt else " (정답 라벨 없음 — 비교 생략)"))
    if has_gt:
        print(f" TP {totals['tp']}  |  CLASS_ERROR {totals['class_error']}  |  FP {totals['fp']}  |  FN {totals['fn']}")
        print(f" (이 conf 기준) 정답 중 맞힌 비율 {totals['tp'] / totals['gt']:.1%}"
              + (f" · 예측 중 맞은 비율 {totals['tp'] / len(pred_rows):.1%}" if pred_rows else ""))

        print("\n Class 별 놓침(FN) · 오검출(FP)")
        for c in sorted(names):
            if fn_by_class[c] or fp_by_class[c]:
                print(f"  {c} {names[c]:<22} FN {fn_by_class[c]:>4}   FP {fp_by_class[c]:>4}")
        if cls_err_pairs:
            print("\n 종류를 틀린 경우 (정답 → 예측)")
            for (g, p), n in cls_err_pairs.most_common(8):
                print(f"  {names[g]} → {names[p]}: {n}")

        print("\n 틀린 것이 많은 사진 Top 10 (6일차 실패분석 후보)")
        worst = sorted(image_rows, key=lambda r: -(r["fn"] + r["fp"] + r["class_error"]))[:10]
        for r in worst:
            print(f"  {r['image']}  정답 {r['gt']} · 예측 {r['pred']} · FN {r['fn']} · FP {r['fp']} · CLS {r['class_error']}")

    print(f"\n 비교 이미지: {rel(out / 'compare')}/  ({len(image_rows)}장)")
    print(f" 표: {rel(out / 'predictions.csv')}, {rel(out / 'per_image.csv')}")
    print("=" * 65)


if __name__ == "__main__":
    main()
