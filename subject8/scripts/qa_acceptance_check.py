"""Acceptance Test 자동 점검 — 가이드 22.7 체크리스트 중 사진·GPU 없이 확인할 수 있는 항목.

    python scripts/qa_acceptance_check.py

결과 상태
    PASS    확인 완료
    FAIL    기준에 어긋남 (고쳐야 함)
    TODO    아직 만들어지지 않은 산출물 (8~9일차 작업 후 PASS 가 되어야 함)
    MANUAL  사진·GPU 가 있는 PC 에서 사람이 직접 확인해야 함

출력: 화면 표 + reports/05_acceptance/acceptance_check.csv (reports/05_acceptance/acceptance_test.md 의 근거)
FAIL 이 하나라도 있으면 종료 코드 1.
"""
import csv
import hashlib
import importlib
import py_compile
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUT_CSV = PROJECT_ROOT / "reports" / "05_acceptance" / "acceptance_check.csv"
R = PROJECT_ROOT / "reports"
M = PROJECT_ROOT / "manifests"

rows = []      # (영역, 항목, 상태, 근거)


def add(area, item, status, detail=""):
    rows.append((area, item, status, detail))


def read_csv(path):
    with Path(path).open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def sha12(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()[:12]


def has_file(rel, area, item, todo_msg="아직 없음"):
    p = PROJECT_ROOT / rel
    if p.is_file():
        add(area, item, "PASS", rel)
        return True
    add(area, item, "TODO", f"{rel} — {todo_msg}")
    return False


# ── Dataset ───────────────────────────────────────────────────
def check_dataset():
    A = "Dataset"
    try:
        sm = read_csv(M / "split_manifest.csv")
    except OSError as e:
        add(A, "split_manifest.csv 읽기", "FAIL", str(e))
        return
    roles = {r: read_csv(M / f"{f}.csv") for r, f in
             (("train", "train"), ("val", "val"), ("test", "test"), ("bridge_holdout", "bridge_holdout"))}

    # 출처·Version 추적
    need = ["출처 데이터셋", "원래 split", "이미지 유형", "capture_group", "dataset_version"]
    empty = {c: sum(1 for r in sm if not (r.get(c) or "").strip()) for c in need}
    if all(c in sm[0] for c in need) and not any(empty.values()):
        add(A, "교과 7 출처(source_dataset·original_split·scene_type)를 추적할 수 있다", "PASS",
            f"{len(sm)}장 모두 {', '.join(need[:3])} 기록")
    else:
        add(A, "교과 7 출처(source_dataset·original_split·scene_type)를 추적할 수 있다", "FAIL", f"빈 칸: {empty}")
    versions = Counter(r["dataset_version"] for r in sm)
    summ = read_csv(R / "01_data" / "dataset_summary.csv")
    sv = {r["dataset_version"] for r in summ}
    add(A, "Dataset Version 을 확인할 수 있다", "PASS" if len(versions) == 1 and set(versions) == sv else "FAIL",
        f"manifest {dict(versions)} · dataset_summary {sorted(sv)}")

    # Manifest 네 역할 합계
    counts = {k: len(v) for k, v in roles.items()}
    total = sum(counts.values())
    add(A, "Train/Validation/Frozen Test/Bridge Holdout Manifest 가 있고 합이 900장", "PASS" if total == 900 == len(sm) else "FAIL",
        f"{counts} 합 {total} · split_manifest {len(sm)}")
    sc = {r["role"]: int(r["image_count"]) for r in summ}
    add(A, "dataset_summary.csv 가 Manifest 와 같다", "PASS" if sc == counts else "FAIL", f"summary {sc}")

    # 역할 간 겹침
    seen, dup = {}, []
    for role, lst in roles.items():
        for r in lst:
            n = r["이미지 파일명"]
            if n in seen and seen[n] != role:
                dup.append((n, seen[n], role))
            seen[n] = role
    add(A, "역할(Train/Val/Test/Bridge) 사이에 같은 이미지가 없다", "PASS" if not dup else "FAIL",
        "겹침 0장" if not dup else f"{len(dup)}장 겹침 (예: {dup[:2]})")

    # 촬영 묶음이 여러 역할에 걸친 경우 (정책 예외 여부)
    grp = {}
    for r in sm:
        grp.setdefault(r["capture_group"], set()).add(r["split"])
    mixed = sorted(g for g, s in grp.items() if len(s) > 1)
    add(A, "같은 촬영 묶음이 여러 역할에 섞이지 않았다 (또는 예외가 문서화됨)", "PASS" if not mixed else "MANUAL",
        "섞인 묶음 없음" if not mixed else f"섞인 묶음 {mixed} — docs/split_policy.md 의 분할 예외로 문서화되어 있는지 사람이 확인")

    # split_policy
    sp = PROJECT_ROOT / "docs" / "split_policy.md"
    txt = sp.read_text(encoding="utf-8") if sp.is_file() else ""
    add(A, "Split 정책이 문서로 확정(FROZEN)되어 있다", "PASS" if "FROZEN" in txt else "FAIL", "docs/split_policy.md")

    # dataset.yaml 에 Bridge 없음, Class 0~6
    ytxt = (PROJECT_ROOT / "configs" / "dataset.yaml").read_text(encoding="utf-8")
    ids = sorted(int(x) for x in re.findall(r"^\s{2}(\d+):", ytxt, re.M))
    add(A, "Class ID 0~6 을 그대로 쓴다", "PASS" if ids == list(range(7)) else "FAIL", f"dataset.yaml names {ids}")
    add(A, "Bridge Holdout 이 dataset.yaml 에 포함되지 않는다", "PASS" if "bridge" not in ytxt.lower() else "FAIL", "configs/dataset.yaml")

    # Frozen Test 사용 흔적 (휴리스틱)
    suspicious = []
    for d in sorted((PROJECT_ROOT / "runs").glob("*")):
        if re.search(r"test|final", d.name, re.I):
            suspicious.append(d.name)
        a = d / "args.yaml"
        if a.is_file() and re.search(r"^split:\s*test", a.read_text(encoding="utf-8"), re.M):
            suspicious.append(f"{d.name}(split=test)")
    guard = "allow_test" in (PROJECT_ROOT / "src" / "evaluate_detector.py").read_text(encoding="utf-8")
    add(A, "Frozen Test 가 Final Model 선택 전에 사용되지 않았다", "PASS" if not suspicious and guard else "FAIL",
        ("runs/ 에 test·final 실행 없음, evaluate_detector 에 allow_test 보호 있음" if not suspicious and guard
         else f"의심: {suspicious} · 보호 코드 {guard}") + " (휴리스틱 — 사람이 학습 로그로 한 번 더 확인)")

    # 학습에 쓴 Manifest 가 기록과 같은지
    doc = (R / "04_improvement" / "exp001_training_condition.md").read_text(encoding="utf-8")
    ok = True
    parts = []
    for fn in ("train", "val"):
        m = re.search(rf"manifests/{fn}\.csv` .*?sha256 ([0-9a-f]{{12}})", doc)
        cur = sha12(M / f"{fn}.csv")
        parts.append(f"{fn} {cur}{'=' if m and m.group(1) == cur else '≠'}{m.group(1) if m else '?'}")
        ok &= bool(m and m.group(1) == cur)
    add(A, "학습에 쓴 Train/Val Manifest 가 지금 Manifest 와 같다 (해시)", "PASS" if ok else "FAIL", " · ".join(parts))


# ── Model ─────────────────────────────────────────────────────
def check_model():
    A = "Model"
    weights = [("baseline", "models/baseline/baseline_best.pt", "02_baseline/baseline_training_condition.md"),
               ("exp001", "models/improved/exp001_best.pt", "04_improvement/exp001_training_condition.md"),
               ("exp002", "models/improved/exp002_best.pt", "04_improvement/exp002_training_condition.md"),
               ("exp003", "models/improved/exp003_best.pt", "04_improvement/exp003_training_condition.md")]
    for name, rel, doc in weights:
        p = PROJECT_ROOT / rel
        if not p.is_file():
            add(A, f"{name} Weight 가 있다", "FAIL", f"{rel} 없음")
            continue
        m = re.search(r"_best\.pt` \(sha256 ([0-9a-f]{12})\)", (R / doc).read_text(encoding="utf-8"))   # Manifest 해시가 아니라 Weight 해시
        cur = sha12(p)
        add(A, f"{name} Weight 가 있고 기록(해시)과 같다", "PASS" if m and m.group(1) == cur else "FAIL",
            f"{rel} · {cur}{'' if m and m.group(1) == cur else ' ≠ 기록 ' + (m.group(1) if m else '없음')}")
    base = (R / "02_baseline" / "baseline_training_condition.md").read_text(encoding="utf-8")
    need = ["Dataset Version", "Epoch", "Image Size", "Batch", "Seed", "Optimizer"]
    miss = [n for n in need if n not in base]
    add(A, "Baseline 학습조건이 기록되어 있다", "PASS" if not miss else "FAIL", "reports/02_baseline/baseline_training_condition.md" + (f" — 빠짐 {miss}" if miss else ""))
    has_file("models/final/final_best.pt", A, "final_best.pt 가 있다", "8일차 Final Model 확정 후")
    has_file("reports/final_model_selection.md", A, "Final Model 을 선택한 이유가 기록되어 있다", "8일차")


# ── Evaluation ────────────────────────────────────────────────
def check_evaluation():
    A = "Evaluation"
    bm = read_csv(R / "02_baseline" / "baseline_metrics.csv")[0]
    keys = ["precision", "recall", "map50", "map50_95"]
    try:
        vals = {k: float(bm[k]) for k in keys}
        add(A, "Baseline Validation 의 Precision·Recall·mAP50·mAP50-95 가 있다", "PASS",
            " · ".join(f"{k} {v:.3f}" for k, v in vals.items()))
    except (KeyError, ValueError) as e:
        add(A, "Baseline Validation 의 Precision·Recall·mAP50·mAP50-95 가 있다", "FAIL", str(e))
    cm = read_csv(R / "02_baseline" / "baseline_class_metrics.csv")
    add(A, "Class 별 성능이 있다", "PASS" if len(cm) >= 6 else "FAIL", f"{len(cm)}개 Class 행")
    has_file("reports/03_failure_analysis/failure_analysis.csv", A, "Failure Analysis 표가 있다")
    has_file("reports/03_failure_analysis/failure_hypothesis.md", A, "실패 원인 가설 문서가 있다")
    has_file("reports/04_improvement/baseline_vs_improved.md", A, "Baseline vs Improved 비교 결과가 있다")
    need = ["experiment_id", "date", "dataset_version", "model", "imgsz", "epochs", "batch", "seed", "changed_variable",
            "reason", "validation_precision", "validation_recall", "validation_map50", "validation_map50_95", "decision"]
    el = read_csv(R / "04_improvement" / "experiment_log.csv")
    miss = [c for c in need if c not in el[0]]
    add(A, "experiment_log.csv 에 권장 필드 15개가 있다", "PASS" if not miss else "FAIL", f"{len(el)}개 실행" + (f" — 빠짐 {miss}" if miss else ""))
    has_file("reports/final_metrics.csv", A, "Frozen Test 결과가 있다", "8일차 Final Model 확정 후 한 번만 평가")


# ── Inference / Auto Label ────────────────────────────────────
def check_use():
    A = "Inference · Auto Label"
    code = [("scripts/08_predict_images.py", "예측 스크립트"), ("src/inference.py", "추론 모듈")]
    for rel, label in code:
        if not (PROJECT_ROOT / rel).is_file():
            add(A, f"{label} 가 있다", "FAIL", rel)
    add(A, "이미지 Detection 이 실행되고 BBox·Class·Confidence 가 표시된다", "MANUAL",
        "사진·GPU 가 있는 PC 에서 `python scripts/08_predict_images.py` 실행 후 비교 이미지 확인")
    if (PROJECT_ROOT / "scripts" / "12_auto_label.py").is_file() or (PROJECT_ROOT / "src" / "auto_labeler.py").is_file():
        add(A, "새 이미지에서 YOLO TXT 후보가 저장된다", "MANUAL", "새 이미지 5장으로 실행 후 TXT 확인")
    else:
        add(A, "새 이미지에서 YOLO TXT 후보가 저장된다", "TODO", "src/auto_labeler.py · scripts/12_auto_label.py 아직 없음 (8일차)")
    add(A, "후보 TXT 를 교과 7 라벨링 도구에서 열고 수정·삭제·추가·승인·저장할 수 있다", "MANUAL",
        "`cd subject7 && python main.py` 로 후보 TXT 를 열어 확인 (Auto Label 구현 후)")
    for rel, label in (("demo/prediction_images", "예측 이미지"), ("demo/auto_label/candidate_labels", "Auto Label 후보"),
                       ("demo/auto_label/reviewed_labels", "검수 완료 라벨")):
        files = [p for p in (PROJECT_ROOT / rel).glob("*") if p.name != ".gitkeep"] if (PROJECT_ROOT / rel).is_dir() else []
        add(A, f"시연 백업자료: {label}", "PASS" if files else "TODO", f"{rel} — {len(files)}개")


# ── 환경 · 코드 · 보안 ────────────────────────────────────────
def check_env():
    A = "환경 · 코드 · 보안"
    bad = []
    for p in sorted(list((PROJECT_ROOT / "src").glob("*.py")) + list((PROJECT_ROOT / "scripts").glob("*.py"))):
        try:
            py_compile.compile(str(p), doraise=True, cfile=str(Path("/tmp") / (p.stem + ".pyc")) if Path("/tmp").is_dir() else None)
        except py_compile.PyCompileError as e:
            bad.append(f"{p.name}: {str(e).splitlines()[-1]}")
    add(A, "src/·scripts/ 의 모든 Python 파일이 문법 오류 없이 컴파일된다", "PASS" if not bad else "FAIL", "전부 정상" if not bad else "; ".join(bad))

    missing = []
    for mod in ("yaml", "pandas", "matplotlib", "ultralytics", "torch", "cv2"):
        try:
            importlib.import_module(mod)
        except Exception:
            missing.append(mod)
    add(A, "학습·추론에 필요한 패키지가 이 PC 에 설치되어 있다", "PASS" if not missing else "FAIL",
        "전부 import 가능" if not missing else f"없음: {', '.join(missing)} — `pip install -r requirements.txt`")

    try:
        out = subprocess.run(["git", "ls-files", "--", ".", ":(exclude)runs"], cwd=PROJECT_ROOT, capture_output=True, text=True, check=True).stdout.splitlines()
        photos = [f for f in out if re.search(r"\.(jpe?g|png|bmp|webp|heic)$", f, re.I) and "/figures/" not in f and not f.startswith("reports/figures/")]
        weights = [f for f in out if f.endswith(".pt") and not f.startswith("models/")]
        add(A, "회사 사진이 Git 에 추적되지 않는다", "PASS" if not photos else "FAIL", "사진 0장" if not photos else f"{len(photos)}장: {photos[:3]}")
        add(A, "Weight(.pt) 는 models/ 안의 것만 추적된다", "PASS" if not weights else "FAIL", "models/ 밖 .pt 0개" if not weights else str(weights[:3]))
    except (OSError, subprocess.CalledProcessError) as e:
        add(A, "Git 추적 파일 점검", "MANUAL", f"git 실행 실패: {e}")

    add(A, "다른 팀원이 README 만 보고 처음부터 재실행할 수 있다", "MANUAL",
        "README 6장 순서대로 다른 PC 에서 실행하고 막힌 곳을 기록 (가이드 22.6)")


def main():
    for fn in (check_dataset, check_model, check_evaluation, check_use, check_env):
        try:
            fn()
        except Exception as e:      # 점검 코드 자체의 오류도 결과로 남긴다
            add(fn.__name__, "점검 실행", "FAIL", f"{type(e).__name__}: {e}")

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["area", "item", "status", "detail"])
        w.writerows(rows)

    last = None
    for area, item, status, detail in rows:
        if area != last:
            print(f"\n[{area}]")
            last = area
        print(f"  {status:<6} {item}")
        if status != "PASS" and detail:
            print(f"         └ {detail}")
    c = Counter(r[2] for r in rows)
    print(f"\n합계: PASS {c['PASS']} · FAIL {c['FAIL']} · TODO {c['TODO']} · MANUAL {c['MANUAL']}  →  {OUT_CSV.relative_to(PROJECT_ROOT)}")
    return 1 if c["FAIL"] else 0


if __name__ == "__main__":
    sys.exit(main())
