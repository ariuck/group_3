"""올인원 준비 — 어느 PC 든 이것 하나로 교과 7 복원 → 데이터 점검 → kimchi_v4·v5 학습 폴더까지 만든다.

    python3 scripts/00_setup.py             # 처음 PC 든 이미 준비된 PC 든 같은 명령
    python3 scripts/00_setup.py --rebuild   # 학습 폴더가 맞아도 지우고 다시 복사

먼저 할 일 (각 PC 에서 한 번): 회사 원본 폴더를 그대로 subject7/data/raw/ 에 넣는다
    subject7/data/raw/이물검출_학습데이터1/images/train/*.jpg …, 이물검출_학습데이터2/…

단계 (이미 된 것은 건너뛴다 — 여러 번 실행해도 결과가 같다)
  1. subject8/.venv 가 없으면 만들고 requirements.txt 설치, 이후 단계는 .venv 의 Python 으로 다시 실행
  2. subject7/data/raw 에 사진 900장이 있는지 확인 (없으면 넣을 위치를 알려 주고 멈춤)
  3. subject7: tools/restore_from_final.py --apply — work · 검수표 · final 사진 (같은 파일은 건너뜀, 다른 파일은 덮어쓰지 않고 멈춤)
  4. scripts/02_audit_subject7_final.py — 900장 · 이슈 0 확인
  5. kimchi_v4 · kimchi_v5: 03_build_split.py 로 manifest 를 다시 만들고, 학습 폴더가 manifest·라벨과 다를 때만 --copy-files
  6. git status — manifest·점검 보고서가 Git 에 있는 것과 같으면 "같은 데이터·같은 분할"
"""
import argparse
import filecmp
import os
import subprocess
import sys
import venv
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SUBJECT7 = PROJECT_ROOT.parent / "subject7"
VENV_PY = PROJECT_ROOT / ".venv" / "bin" / "python"
VERSIONS = ["kimchi_v4", "kimchi_v5"]
EXPECTED_IMAGES = 900


def step(n, title):
    print(f"\n[{n}/6] {title}", flush=True)


def run(cmd, cwd=PROJECT_ROOT):
    print("   $ " + " ".join(str(c) for c in cmd), flush=True)
    if subprocess.run([str(c) for c in cmd], cwd=cwd).returncode != 0:
        sys.exit(f"\n실패: {' '.join(str(c) for c in cmd)}")


def ensure_venv():
    """1. .venv 준비 후 그 Python 으로 이 스크립트를 다시 실행 (이미 .venv 안이면 통과)"""
    if Path(sys.prefix).resolve() == (PROJECT_ROOT / ".venv").resolve():
        return
    step(1, "가상환경 subject8/.venv")
    if not VENV_PY.exists():
        print("   없음 → 만들고 requirements.txt 설치 (처음 한 번, 몇 분 걸림)")
        venv.create(PROJECT_ROOT / ".venv", with_pip=True)
        run([VENV_PY, "-m", "pip", "install", "-r", PROJECT_ROOT / "requirements.txt"])
    else:
        print("   있음 → 건너뜀")
    os.execv(str(VENV_PY), [str(VENV_PY), __file__, *sys.argv[1:]])


def check_raw():
    step(2, "회사 원본 subject7/data/raw")
    raw = SUBJECT7 / "data" / "raw"
    n = sum(1 for p in raw.rglob("*") if p.suffix.lower() in (".jpg", ".jpeg"))
    if n != EXPECTED_IMAGES:
        sys.exit(f"   사진 {n}장 (필요 {EXPECTED_IMAGES}장). 회사 원본 폴더를 그대로 넣으세요:\n"
                 f"     {raw}/이물검출_학습데이터1/images/train/*.jpg …\n"
                 f"     {raw}/이물검출_학습데이터2/images/train|validation/*.jpg …")
    print(f"   사진 {n}장 ✓")


def dataset_matches(version):
    """학습 폴더가 manifest 와 같은 사진·같은 라벨인가 (사진은 크기, 라벨은 내용 비교)"""
    sys.path.insert(0, str(PROJECT_ROOT))
    import pandas as pd
    from src.split_builder import SplitBuilder
    b = SplitBuilder(PROJECT_ROOT, version)
    manifest = b.manifest_dir / "split_manifest.csv"
    if not manifest.is_file():
        return False
    fix = b.label_fix_dir(version)
    imgs = b._build_file_index(b.images_dir, "*.jpg")
    lbls = b._build_file_index(b.labels_dir, "*.txt")
    expected = set()
    for _, r in pd.read_csv(manifest, encoding="utf-8-sig").iterrows():
        img, lbl, split = r["이미지 파일명"], r["라벨(TXT) 파일명"], r["split"]
        if split == "bridge_holdout":
            dst_img, dst_lbl = b.bridge_dir / "images" / img, b.bridge_dir / "labels" / lbl
        else:
            dst_img, dst_lbl = b.yolo_dir / "images" / split / img, b.yolo_dir / "labels" / split / lbl
        src_lbl = fix / lbl if fix is not None and (fix / lbl).is_file() else lbls[lbl]
        if not (dst_img.is_file() and img in imgs and dst_img.stat().st_size == imgs[img].stat().st_size):
            return False
        if not (dst_lbl.is_file() and filecmp.cmp(src_lbl, dst_lbl, shallow=False)):
            return False
        expected |= {dst_img, dst_lbl}
    actual = {p for d in (b.yolo_dir, b.bridge_dir) for p in d.rglob("*") if p.is_file() and p.suffix != ".cache"}
    return actual == expected     # manifest 에 없는 파일이 남아 있으면 다시 만든다 (누수 방지)


def main():
    ap = argparse.ArgumentParser(description="올인원 준비: 교과 7 복원 → 점검 → kimchi_v4·v5 학습 폴더")
    ap.add_argument("--rebuild", action="store_true", help="학습 폴더가 맞아도 지우고 다시 복사")
    args = ap.parse_args()
    ensure_venv()
    py = sys.executable
    check_raw()

    step(3, "교과 7 복원 (work · 검수표 · final 사진)")
    run([py, "tools/restore_from_final.py", "--apply"], cwd=SUBJECT7)

    step(4, "데이터 점검 (02)")
    run([py, "scripts/02_audit_subject7_final.py"])

    step(5, "학습 폴더 " + " · ".join(VERSIONS))
    for v in VERSIONS:
        run([py, "scripts/03_build_split.py", "--version", v])       # manifest 다시 만들기 (빠름)
        if not args.rebuild and dataset_matches(v):
            print(f"   {v}: 학습 폴더가 manifest·라벨과 같음 → 복사 건너뜀")
        else:
            run([py, "scripts/03_build_split.py", "--version", v, "--copy-files"])
            if not dataset_matches(v):
                sys.exit(f"   {v}: 복사 후에도 manifest 와 다름 — 확인 필요")

    step(6, "Git 과 비교")
    out = subprocess.run(["git", "status", "--porcelain", "--", "manifests", "configs", "reports/01_data",
                          "../subject7/data/final"], cwd=PROJECT_ROOT, capture_output=True, text=True).stdout.strip()
    if out:
        print("   ⚠ Git 에 있는 것과 다른 파일:\n" + "\n".join("     " + x for x in out.splitlines()))
        sys.exit(1)
    print("   manifest · 점검 보고서 · 교과 7 최종본이 Git 과 같음 → 같은 데이터 · 같은 분할 ✓")
    print("\n준비 끝. 학습: python scripts/06_train_baseline.py (v4) · python scripts/11_train_v5.py (v5)")


if __name__ == "__main__":
    main()
