"""교과 14 용 — Final Model 을 Bridge Holdout 156장에서 **처음** 평가한다 (교과 8 에서는 실행하지 않는다).

    python scripts/17_evaluate_bridge.py --dry-run                  # 파일 개수·Manifest 만 확인 (모델·사진 내용을 쓰지 않음)
    python scripts/17_evaluate_bridge.py --subject14                # 교과 14 에서 처음 한 번 평가

Bridge Holdout 은 교과 8 학습·튜닝·모델 선택·Frozen Test 에 쓰지 않고 교과 14 를 위해 보존한 데이터다.
그래서 `--subject14` 없이는 평가하지 않고, 결과 파일이 이미 있으면 다시 평가하지 않는다 (Frozen Test 와 같은 규칙).
이 점수를 보고 모델·조건을 다시 고르면 Bridge 가 Validation 이 된다 — 다시 고를 일이 있으면 교과 14 안의 새 Validation 으로 한다.

결과 (reports/06_subject14/):
    bridge_metrics.csv · bridge_class_metrics.csv        Bridge 성능 (전체 · Class 별)
    reports/figures/subject14/bridge_{confusion_matrix, confusion_matrix_normalized, pr_curve}.png
"""
import argparse
import csv
import os
import shutil
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
os.chdir(PROJECT_ROOT)

from src import registry  # noqa: E402
from src.constants import DEFAULT_DATASET_VERSION  # noqa: E402
from src.split_builder import SplitBuilder  # noqa: E402
from src.train_detector import rel, sha256_short  # noqa: E402

OUT_DIR = PROJECT_ROOT / "reports" / "06_subject14"
FIG_DIR = PROJECT_ROOT / "reports" / "figures" / "subject14"
BRIDGE_DIR = PROJECT_ROOT / "data" / "bridge_holdout"
EVAL_YAML = PROJECT_ROOT / "configs" / "dataset_bridge.yaml"      # 평가 때만 만든다 (Git 에 없음 · 학습에 쓰지 않음)
CLASS_NAMES = {0: "leaf_paper", 1: "plastic_stone_metal", 2: "branch", 3: "insect",
               4: "rubber_glove_unused", 5: "disease_browning", 6: "green_onion_pepper"}


def manifest_names(version: str):
    """Manifest 의 Bridge Holdout 사진 이름 (SplitBuilder 가 정한 규칙 그대로)"""
    path = SplitBuilder(PROJECT_ROOT, version).manifest_dir / "bridge_holdout.csv"
    with path.open(encoding="utf-8-sig", newline="") as f:
        return {r["이미지 파일명"] for r in csv.DictReader(f)}


def check_folder(version: str):
    """data/bridge_holdout 이 Manifest 와 같은지 (사진 · 라벨 개수와 이름). 사진 내용은 열지 않는다."""
    want = manifest_names(version)
    imgs = {p.name for p in (BRIDGE_DIR / "images").glob("*.jpg")} if (BRIDGE_DIR / "images").is_dir() else set()
    lbls = {p.stem for p in (BRIDGE_DIR / "labels").glob("*.txt")} if (BRIDGE_DIR / "labels").is_dir() else set()
    problems = []
    if imgs != want:
        problems.append(f"사진 {len(imgs)}장 ≠ Manifest {len(want)}장 (없음 {len(want - imgs)} · 남음 {len(imgs - want)})")
    if {Path(n).stem for n in want} != lbls:
        problems.append(f"라벨 {len(lbls)}개 ≠ Manifest {len(want)}개")
    return len(want), len(imgs), len(lbls), problems


def write_eval_yaml():
    EVAL_YAML.write_text(
        "# 교과 14 Bridge Holdout 평가 전용 (scripts/17_evaluate_bridge.py 가 만든다 · 학습에 쓰지 않는다)\n"
        f"path: {BRIDGE_DIR.relative_to(PROJECT_ROOT).as_posix()}\n"
        "train: images\nval: images\ntest: images\n\nnames:\n"
        + "".join(f"  {k}: {v}\n" for k, v in CLASS_NAMES.items()), encoding="utf-8")


def main():
    ap = argparse.ArgumentParser(description="Final Model Bridge Holdout 평가 (교과 14, 처음 한 번)")
    ap.add_argument("--model", default="final", help="기본: final (models/final/final_best.pt)")
    ap.add_argument("--subject14", action="store_true", help="교과 14 에서 Bridge 를 처음 평가한다는 확인 (없으면 평가하지 않음)")
    ap.add_argument("--dry-run", action="store_true", help="Manifest · 폴더 개수만 확인")
    args = ap.parse_args()

    version = DEFAULT_DATASET_VERSION
    n_want, n_img, n_lbl, problems = check_folder(version)
    print(f" Bridge Holdout ({version}): Manifest {n_want}장 · 폴더 사진 {n_img}장 · 라벨 {n_lbl}개")
    for p in problems:
        print(f"  ! {p}")
    if args.dry_run:
        sys.exit(1 if problems else 0)
    if not args.subject14:
        sys.exit("Bridge Holdout 은 교과 14 용으로 보존한 데이터입니다. 교과 14 에서 처음 평가할 때만 --subject14 를 붙여 실행하세요 "
                 "(교과 8 에서는 실행하지 않습니다). 확인만 하려면 --dry-run.")
    if problems:
        sys.exit("data/bridge_holdout 이 Manifest 와 다릅니다. python scripts/00_setup.py 로 다시 만든 뒤 실행하세요.")
    out_metrics = OUT_DIR / "bridge_metrics.csv"
    if out_metrics.is_file():
        sys.exit(f"{rel(out_metrics)} 가 이미 있습니다. Bridge 는 처음 한 번만 평가합니다 (다시 평가하려면 교과 14 새 Validation 사용).")

    from src.evaluate_detector import evaluate_detector  # 무거운 import 는 실제 평가 때만

    weight, run = registry.resolve(args.model)
    a = registry.run_args(run)
    write_eval_yaml()
    print("=" * 65)
    print(f" [Subject 14] Bridge Holdout — {run} ({rel(weight)}, sha256 {sha256_short(weight)}) · imgsz {a['imgsz']}")
    print("=" * 65)
    r = evaluate_detector(weight, EVAL_YAML, "val", a["imgsz"], max(1, a["batch"]), project=PROJECT_ROOT / "runs" / "eval",
                          name=f"bridge_{run}")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with out_metrics.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["model_version", "dataset_version", "split", "imgsz", "batch", "images", "instances",
                    "precision", "recall", "map50", "map50_95"])
        w.writerow([run, version, "bridge_holdout", a["imgsz"], a["batch"], r["images"], r["instances"],
                    r["precision"], r["recall"], r["map50"], r["map50_95"]])
    with (OUT_DIR / "bridge_class_metrics.csv").open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(r["per_class"][0]))
        w.writeheader()
        w.writerows(r["per_class"])
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    for src, dst in (("confusion_matrix.png", "bridge_confusion_matrix.png"),
                     ("confusion_matrix_normalized.png", "bridge_confusion_matrix_normalized.png"),
                     ("BoxPR_curve.png", "bridge_pr_curve.png")):
        if (r["save_dir"] / src).is_file():
            shutil.copy2(r["save_dir"] / src, FIG_DIR / dst)
    print(f"\n Bridge Holdout {r['images']}장 · 정답 {r['instances']}개")
    print(f" P {r['precision']:.3f} | R {r['recall']:.3f} | mAP50 {r['map50']:.3f} | mAP50-95 {r['map50_95']:.3f}")
    for c in r["per_class"]:
        if c["instances"]:
            print(f"  {c['class_id']} {c['class_name']:<22} {c['instances']:>4}  R {c['recall']:.3f}  mAP50-95 {c['map50_95']:.3f}")
    print(f" 저장: {rel(OUT_DIR)}/, {rel(FIG_DIR)}/")


if __name__ == "__main__":
    main()
