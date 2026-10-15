"""3일차 Smoke Test — 작은 데이터(Train 40 / Val 8)로 학습 → Weight → Prediction 이 끝까지 되는지 확인 (가이드 16.5~16.7).

    python scripts/05_smoke_train.py              # 3 epoch
    python scripts/05_smoke_train.py --overwrite  # runs/smoke_v1 을 지우고 다시

성능을 보는 단계가 아니다. Smoke Weight 는 Baseline 이 아니다.
"""
import argparse
import os
import shutil
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
os.chdir(PROJECT_ROOT)  # dataset.yaml 의 path: data/... 는 이 폴더 기준

from ultralytics import YOLO  # noqa: E402

from src.smoke_dataset import build_smoke_dataset  # noqa: E402
from src.train_detector import check_training, rel, train_detector, write_condition_report  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description="Smoke Test (작은 데이터로 학습 Pipeline 확인)")
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--batch", type=int, default=16, help="Baseline 과 같은 값으로 GPU 메모리 확인")
    parser.add_argument("--name", default="smoke_v1")
    parser.add_argument("--overwrite", action="store_true", help="같은 이름의 runs 폴더를 지우고 다시 실행")
    args = parser.parse_args()

    runs = PROJECT_ROOT / "runs"
    if args.overwrite:
        shutil.rmtree(runs / args.name, ignore_errors=True)
        shutil.rmtree(runs / f"{args.name}_predict", ignore_errors=True)

    print("=" * 65)
    print(" [Subject 08] Day 3: Smoke Test")
    print("=" * 65)

    smoke = build_smoke_dataset(PROJECT_ROOT)
    print(f" Smoke Dataset: train {smoke['train']}장 / val {smoke['val']}장 -> {smoke['yaml']}")

    result = train_detector(
        model_name="yolo11n.pt",
        data_yaml=str(smoke["yaml"]),
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        seed=42,
        project=str(runs),
        name=args.name,
    )
    checks = check_training(result)

    # Smoke Weight 로 Val 이미지 1장 Prediction (가이드 16.7)
    # 3 epoch 모델은 확신이 낮아 conf 0.25 에서 0개일 수 있다 → 그때는 기준을 낮춰 표시 기능만 확인
    sample = sorted((smoke["root"] / "images" / "val").iterdir())[0]
    model = YOLO(str(result["best"]))
    for conf in (0.25, 0.01):
        pred = model.predict(source=str(sample), conf=conf, save=True,
                             project=str(runs), name=f"{args.name}_predict", exist_ok=True)[0]
        if len(pred.boxes):
            break
    boxes = [(pred.names[int(c)], round(float(p), 2)) for c, p in zip(pred.boxes.cls, pred.boxes.conf)]
    pred_dir = Path(pred.save_dir)
    checks["이미지 Prediction 실행"] = (True, f"{sample.name} (conf {conf}) → BBox {len(boxes)}개, 저장 `{rel(pred_dir)}`")
    checks["BBox · Class · Confidence 표시"] = (len(boxes) > 0 and (pred_dir / sample.name).is_file(),
                                               ", ".join(f"{n} {c}" for n, c in boxes[:5]) or "검출 0개")

    report = write_condition_report(
        PROJECT_ROOT / "reports" / "smoke_test.md",
        "Smoke Test 기록 (진행용)",
        {
            "목적": "학습 Pipeline 확인 (성능 판단 X)",
            "Model": "yolo11n.pt (사전학습)",
            "Dataset": f"`configs/smoke_dataset.yaml` — data/yolo 의 train {smoke['train']}장 / val {smoke['val']}장 (seed 42)",
            "Epoch": args.epochs, "Image Size": args.imgsz, "Batch": args.batch, "Seed": 42,
            "Optimizer / lr0": f"{result['optimizer']} / {result['lr0']}",
        },
        result,
        checks,
        notes=["Frozen Test 와 Bridge Holdout 은 사용하지 않았다.",
               "Smoke Weight 는 Baseline 으로 쓰지 않는다 (4일차에 전체 Train 으로 Baseline 학습)."],
    )

    print("\n-----------------------------------------------------------------")
    print(" [Smoke Test Checks]")
    print("-----------------------------------------------------------------")
    for k, (ok, detail) in checks.items():
        print(f" {'PASS' if ok else 'FAIL'}  {k}: {detail}")
    print(f"\n 기록: {rel(report)}")
    print("=" * 65)
    if not all(ok for ok, _ in checks.values()):
        sys.exit(1)


if __name__ == "__main__":
    main()
