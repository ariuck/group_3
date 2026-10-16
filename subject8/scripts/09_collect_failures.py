"""6일차 Failure Analysis — 모델이 Validation 에서 틀린 것을 모아 유형·Class·크기·묶음별로 정리한다 (가이드 예시 6).

    python scripts/09_collect_failures.py                               # 공식 Baseline
    python scripts/09_collect_failures.py --model exp002_v5_imgsz1920   # 다른 모델 (결과 이름 앞에 실행 이름)

모델 이름만 주면 imgsz · Validation 폴더 · manifest 를 src/registry.py 로 정한다 (타일링 모델은 지원하지 않음).

결과 (공식 Version → reports/03_failure_analysis/, 지난 Version → reports/history/<Version>/03_failure_analysis/):
    <prefix>_analysis.csv          실패 1건 = 1줄 (산출물 3, 공식 Baseline 은 failure_analysis.csv)
    <prefix>_summary.csv           실패 유형 × Class 개수
    <prefix>_recall_by_size.csv    Class × 박스 크기별 Recall
    <prefix>_box_size_shift.csv    Class 별 정답 박스 크기 Train vs Val
    demo/failure_analysis/[<prefix>/]*.jpg   대표 실패 사진 모음 (회사 사진 → Git 제외)

원인 판단과 다음 실험은 reports/03_failure_analysis/failure_hypothesis.md 에 사람이 정리한다.
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

from src import registry  # noqa: E402
from src.constants import DEFAULT_DATASET_VERSION  # noqa: E402
from src.failure_analyzer import (  # noqa: E402
    box_size_shift, class_montage, collect_failures, failure_montage, recall_by_size, summarize,
)
from src.split_builder import SplitBuilder  # noqa: E402
from src.train_detector import rel  # noqa: E402

REPORTS = PROJECT_ROOT / "reports"
DEMO = PROJECT_ROOT / "demo" / "failure_analysis"
SCENE = {"김치+대상 객체": "kimchi_with_target", "대상 객체 단독": "object_only", "판단 어려움": "other_review", "정상 김치": "normal_kimchi"}


def write_csv(path: Path, rows, bom=True):
    if not rows:
        return
    with path.open("w", encoding="utf-8-sig" if bom else "utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def main():
    ap = argparse.ArgumentParser(description="Validation 실패 사례 수집")
    ap.add_argument("--model", default="baseline", help="baseline · final · 실행 이름 (models/README.md) · .pt 경로")
    ap.add_argument("--conf", type=float, default=0.25)
    ap.add_argument("--imgsz", type=int, help="기본: 그 모델을 학습할 때의 imgsz")
    ap.add_argument("--prefix", help="결과 파일 이름 앞부분 (기본: 공식 Baseline 은 failure, 그 밖은 <실행>_failure)")
    args = ap.parse_args()

    weights, run = registry.resolve(args.model)
    if registry.run_tiles(run):
        sys.exit("타일링 모델은 지원하지 않습니다 (src/tiling.evaluate_full 로 채점).")
    version = registry.run_version(run)
    builder = SplitBuilder(PROJECT_ROOT, version)
    yolo_dir = builder.yolo_dir
    imgsz = args.imgsz or registry.run_args(run)["imgsz"]
    failure_dir = REPORTS / "03_failure_analysis"
    if version != DEFAULT_DATASET_VERSION:
        failure_dir = REPORTS / "history" / version / "03_failure_analysis"

    meta = {}
    with (builder.manifest_dir / "split_manifest.csv").open(encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            meta[r["이미지 파일명"]] = {"capture_group": r["capture_group"], "scene_type": SCENE.get(r["이미지 유형"], r["이미지 유형"])}

    print("=" * 65)
    print(f" [Subject 08] Day 6: Failure Analysis  {run} ({rel(Path(weights))}, imgsz {imgsz})  (Validation, conf≥{args.conf})")
    print("=" * 65)
    failures, gt_rows = collect_failures(str(weights), yolo_dir / "images" / "val", yolo_dir / "labels" / "val",
                                         meta, conf=args.conf, imgsz=imgsz)
    from ultralytics import YOLO
    names = YOLO(str(weights)).names

    p = args.prefix or ("failure" if args.model == "baseline" else f"{run}_failure")
    outputs = {
        failure_dir / f"{p}_analysis.csv": failures,
        failure_dir / f"{p}_summary.csv": summarize(failures),
        failure_dir / f"{p}_recall_by_size.csv": recall_by_size(gt_rows, names),
        failure_dir / f"{p}_box_size_shift.csv": box_size_shift(yolo_dir / "labels" / "train", yolo_dir / "labels" / "val", names),
    }
    failure_dir.mkdir(parents=True, exist_ok=True)
    for path, rows in outputs.items():
        write_csv(path, rows)

    # 대표 실패 사진 모음
    demo = DEMO if p == "failure" else DEMO / p
    pics = [failure_montage(failures, k, yolo_dir / "images" / "val", demo / f"{k.lower()}.jpg")
            for k in ("FN", "CLASS_ERROR", "FP_DUPLICATE", "FP_PARTIAL", "FP_BACKGROUND")]
    for cid, name in names.items():
        if any(r["class_id"] == cid for r in gt_rows):
            pics.append(class_montage(cid, name, {"train": yolo_dir, "val": yolo_dir}, meta,
                                      demo / f"class{cid}_{name}_train_vs_val.jpg"))

    kinds = Counter(f["failure_type"] for f in failures)
    tp = sum(r["result"] == "TP" for r in gt_rows)
    print(f"\n 정답 {len(gt_rows)}개 중 TP {tp} · 실패 {len(failures)}건")
    for k in ("FN", "CLASS_ERROR", "FP_DUPLICATE", "FP_PARTIAL", "FP_BACKGROUND"):
        print(f"  {k:<14} {kinds[k]:>4}")

    print("\n 실패 유형 × Class (5건 이상)")
    for r in outputs[failure_dir / f"{p}_summary.csv"]:
        if r["count"] >= 5:
            print(f"  {r['failure_type']:<14} {r['class_name']:<22} {r['count']:>4}")

    print("\n 종류를 틀린 조합 (정답 → 예측)")
    for (g, pr), n in Counter((f["gt_class"], f["pred_class"]) for f in failures if f["failure_type"] == "CLASS_ERROR").most_common(6):
        print(f"  {g} → {pr}: {n}")

    print("\n 박스 크기별 Recall")
    for r in outputs[failure_dir / f"{p}_recall_by_size.csv"]:
        print(f"  {r['class_name']:<22} {r['size_bucket']:<14} {r['tp']:>3}/{r['gt']:<3} = {r['recall']:.2f}")

    print("\n 정답 박스 크기 중앙값 Train vs Val (원본 px)")
    for r in outputs[failure_dir / f"{p}_box_size_shift.csv"]:
        print(f"  {r['class_name']:<22} train {r['train_median_px']:>4} · val {r['val_median_px']:>4}  (×{r['val_to_train']})")

    print("\n 저장:")
    for path in outputs:
        print(f"  -> {rel(path)}")
    print(f"  -> {rel(demo)}/ ({len(pics)}장)")
    print("=" * 65)


if __name__ == "__main__":
    main()
