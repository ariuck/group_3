"""5일차 이미지 Detection — Weight 로 사진을 예측하고 정답(GT)과 나란히 그려 비교한다 (가이드 18장, 6일차 실패분석 준비).

    python scripts/08_predict_images.py                          # Baseline × Validation 84장
    python scripts/08_predict_images.py --conf 0.5 --limit 10    # 기준을 바꿔 10장만
    python scripts/08_predict_images.py --source 사진.jpg          # 사진 1장 (라벨이 있으면 비교도)

결과 (runs/predict/<name>/ — Git 제외):
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

from ultralytics import YOLO  # noqa: E402

from src.inference import draw_comparison, load_gt, match  # noqa: E402
from src.train_detector import rel  # noqa: E402

IMAGE_SUFFIXES = (".jpg", ".jpeg", ".png")
PROTECTED = [PROJECT_ROOT / "data" / "yolo" / "images" / "test", PROJECT_ROOT / "data" / "bridge_holdout"]


def label_for(img: Path) -> Path:
    """.../images/<split>/a.jpg → .../labels/<split>/a.txt (YOLO 규칙)"""
    parts = list(img.parts)
    if "images" in parts:
        i = len(parts) - 1 - parts[::-1].index("images")
        parts[i] = "labels"
    return Path(*parts).with_suffix(".txt")


def main():
    ap = argparse.ArgumentParser(description="Weight 로 사진 예측 + 정답 비교")
    ap.add_argument("--weights", default="models/baseline/baseline_best.pt")
    ap.add_argument("--source", default="data/yolo/images/val", help="사진 폴더 또는 사진 1장")
    ap.add_argument("--conf", type=float, default=0.25, help="이 확신도 이상인 예측만 사용")
    ap.add_argument("--imgsz", type=int, default=640, help="학습 때와 같은 값")
    ap.add_argument("--name", default="baseline_val_images")
    ap.add_argument("--limit", type=int, default=0, help="앞에서부터 N장만 (0 = 전부)")
    ap.add_argument("--allow-test", action="store_true", help="Frozen Test·Bridge 사진 예측 허용 (8일차 이후)")
    args = ap.parse_args()

    source = Path(args.source).resolve()
    if not args.allow_test and any(source == p.resolve() or p.resolve() in source.parents for p in PROTECTED):
        sys.exit("Frozen Test / Bridge Holdout 사진입니다. Final Model 확정 전에는 보지 않습니다 (--allow-test).")
    images = [source] if source.is_file() else sorted(p for p in source.iterdir() if p.suffix.lower() in IMAGE_SUFFIXES)
    if args.limit:
        images = images[:args.limit]
    if not images:
        sys.exit(f"사진이 없습니다: {source}")

    out = PROJECT_ROOT / "runs" / "predict" / args.name
    (out / "compare").mkdir(parents=True, exist_ok=True)
    model = YOLO(args.weights)
    names = model.names

    print("=" * 65)
    print(f" [Subject 08] Day 5: Prediction  {rel(Path(args.weights))}  conf≥{args.conf}")
    print(f" 사진 {len(images)}장  ({rel(source)})")
    print("=" * 65)

    pred_rows, image_rows = [], []
    totals = Counter()
    fn_by_class, fp_by_class, cls_err_pairs = Counter(), Counter(), Counter()
    for r in model.predict(source=[str(p) for p in images], conf=args.conf, imgsz=args.imgsz, stream=True, verbose=False):
        img = Path(r.path)
        preds = [(int(c), float(p), *map(float, b)) for c, p, b in zip(r.boxes.cls, r.boxes.conf, r.boxes.xyxyn)]
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
