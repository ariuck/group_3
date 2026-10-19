"""추론 설정 비교 (재학습 없음) — 학습된 모델을 Validation 에서 추론 옵션만 바꿔 평가한다.

    python scripts/15_eval_inference_options.py                                     # 기본 후보 (exp007 · exp008)
    python scripts/15_eval_inference_options.py --models exp015_v5_s_imgsz2240_aug exp009_v5_m_imgsz1920_aug

옵션 4가지: 기본 · TTA(augment=True, 좌우반전·크기 바꿔 여러 번 예측해 합침) · agnostic_nms(Class 가 달라도 겹친 박스 하나로)
· 둘 다. 모델마다 학습 때 imgsz·batch 로 평가한다 (src/registry). Frozen Test 는 쓰지 않는다.

결과: reports/04_improvement/inference_options.csv (모델 × 옵션 × 전체·Class 별 P·R·mAP50·mAP50-95·속도) — 다시 실행하면 같은 모델 줄만 바꾼다
가설: kimchi_v1 실패 분석 H3 "같은 물체를 두 Class 로 예측" (FP 의 절반) → agnostic_nms 로 줄어드나, TTA 로 작은 이물이 늘어나나.
"""
import argparse
import csv
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
os.chdir(PROJECT_ROOT)

from src import registry  # noqa: E402
from src.evaluate_detector import evaluate_detector  # noqa: E402
from src.split_builder import SplitBuilder  # noqa: E402
from src.train_detector import rel  # noqa: E402

OUT = PROJECT_ROOT / "reports" / "04_improvement" / "inference_options.csv"
OPTIONS = {"기본": {}, "TTA": {"augment": True}, "agnostic_nms": {"agnostic_nms": True},
           "TTA+agnostic_nms": {"augment": True, "agnostic_nms": True}}
DEFAULT_MODELS = ["exp007_v5_s_imgsz1920_aug", "exp008_v5_s_imgsz1920_aug_epoch100"]


def main():
    ap = argparse.ArgumentParser(description="추론 옵션 비교 (Validation)")
    ap.add_argument("--models", nargs="*", default=DEFAULT_MODELS, help="실행 이름 (models/README.md)")
    args = ap.parse_args()
    old = list(csv.DictReader(OUT.open(encoding="utf-8-sig"))) if OUT.is_file() else []
    rows = [r for r in old if r["model"] not in args.models]
    for run in args.models:
        weight, _ = registry.resolve(run)
        a = registry.run_args(run)
        if registry.run_tiles(run):
            print(f" 건너뜀 (타일링 모델): {run}")
            continue
        data = SplitBuilder(PROJECT_ROOT, registry.run_version(run)).dataset_yaml
        for opt, kw in OPTIONS.items():
            r = evaluate_detector(weight, data, "val", a["imgsz"], max(1, a["batch"]), project=PROJECT_ROOT / "runs" / "eval",
                                  name=f"infer_{run}_{opt}", **kw)
            ms = sum(r["speed_ms"].values())
            print(f" {run:<36} {opt:<17} P {r['precision']:.3f} R {r['recall']:.3f} mAP50 {r['map50']:.3f} "
                  f"mAP50-95 {r['map50_95']:.3f}  {ms:.0f}ms/장")
            base = {"model": run, "option": opt, "imgsz": a["imgsz"], "ms_per_image": round(ms, 1)}
            rows.append({**base, "class": "all", "instances": r["instances"],
                         **{k: r[k] for k in ("precision", "recall", "map50", "map50_95")}})
            for c in r["per_class"]:
                if c["instances"]:
                    rows.append({**base, "class": c["class_id"], "instances": c["instances"],
                                 **{k: c[k] for k in ("precision", "recall", "map50", "map50_95")}})
    with OUT.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(f" 저장: {rel(OUT)}")


if __name__ == "__main__":
    main()
