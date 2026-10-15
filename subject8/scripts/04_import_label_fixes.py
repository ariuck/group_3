"""라벨링 프로그램에서 고친 TXT 를 kimchi_v3 라벨 수정본으로 가져온다 (교과 7 최종본은 그대로 둔다).

    python scripts/04_import_label_fixes.py            # 확인만 (무엇이 바뀌는지 출력)
    python scripts/04_import_label_fixes.py --apply    # data/label_fixes/kimchi_v3/ 로 복사 + 변경 기록

흐름:
    group_3/subject7 라벨링 프로그램에서 data/final 폴더를 열어 고치고 저장
      → group_3/subject7/data/work/_RAW밖/<사진이름>.txt   (RAW 밖 폴더라 검수표에는 기록되지 않음)
      → 이 스크립트가 원본(data/subject7_final/labels)과 비교해 바뀐 TXT 만 data/label_fixes/kimchi_v3/ 로 복사
      → python scripts/03_build_split.py --version kimchi_v3 --copy-files

결과:
    data/label_fixes/kimchi_v3/*.txt          바뀐 사진의 TXT (data/ 는 Git 제외)
    reports/class5/label_changes_kimchi_v3.csv       사진별 변경 기록 (지운 줄·추가된 줄 수, Class 별 BBox 수 변화)
"""
import argparse
import csv
import shutil
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
FINAL_LABELS = PROJECT_ROOT / "data" / "subject7_final" / "labels"
FIX_DIR = PROJECT_ROOT / "data" / "label_fixes" / "kimchi_v3"
DEFAULT_SRC = PROJECT_ROOT.parent / "subject7" / "data" / "work" / "_RAW밖"
WORKLIST = PROJECT_ROOT / "reports" / "class5" / "class5_relabel_worklist.csv"
REPORT = PROJECT_ROOT / "reports" / "class5" / "label_changes_kimchi_v3.csv"


def read_lines(path):
    return [ln.strip() for ln in Path(path).read_text(encoding="utf-8").splitlines() if ln.strip()]


def same_box(a, b, tol=1e-4):
    """같은 Class 이고 좌표 차이가 tol 이하이면 같은 BBox (프로그램이 저장하며 자릿수를 바꿔도 같다고 본다)"""
    pa, pb = a.split(), b.split()
    return pa[0] == pb[0] and all(abs(float(x) - float(y)) <= tol for x, y in zip(pa[1:5], pb[1:5]))


def compare(orig, new):
    """원본 줄 중 사라진 것(1부터 센 줄 번호)과 새로 생긴 줄 수"""
    left = list(new)
    removed = []
    for i, line in enumerate(orig, 1):
        hit = next((j for j, n in enumerate(left) if same_box(line, n)), None)
        if hit is None:
            removed.append(i)
        else:
            left.pop(hit)
    return removed, len(left)


def main():
    parser = argparse.ArgumentParser(description="라벨링 프로그램 수정본 → kimchi_v3 라벨 수정본")
    parser.add_argument("--src", default=str(DEFAULT_SRC), help="고친 TXT 가 저장된 폴더 (기본: group_3/subject7/data/work/_RAW밖)")
    parser.add_argument("--apply", action="store_true", help="실제로 복사하고 변경 기록을 쓴다")
    args = parser.parse_args()

    src = Path(args.src)
    if not src.is_dir():
        sys.exit(f"고친 TXT 폴더가 없습니다: {src}\n  라벨링 프로그램에서 data/final 폴더를 열고 고친 뒤 저장했는지 확인하세요.")
    originals = {p.stem: p for p in FINAL_LABELS.rglob("*.txt")}

    plan, unknown, unchanged = [], [], 0
    for p in sorted(src.glob("*.txt")):
        if p.stem not in originals:
            unknown.append(p.name)
            continue
        orig, new = read_lines(originals[p.stem]), read_lines(p)
        removed, added = compare(orig, new)
        if not removed and not added:
            unchanged += 1
            continue
        before = Counter(int(ln.split()[0]) for ln in orig)
        after = Counter(int(ln.split()[0]) for ln in new)
        delta = {c: after[c] - before[c] for c in sorted(set(before) | set(after)) if after[c] != before[c]}
        # Class 5 가 아닌 BBox 가 지워지거나 새로 생겼나 (좌표만 바뀌어도 '지움 + 추가' 로 잡힌다)
        added_lines = [n for n in new if not any(same_box(o, n) for o in orig)]
        other = sum(orig[i - 1].split()[0] != "5" for i in removed) + sum(n.split()[0] != "5" for n in added_lines)
        plan.append({"파일": p, "TXT 파일명": p.name, "원본 BBox 수": len(orig), "수정 BBox 수": len(new),
                     "지운 줄(원본 기준)": " ".join(map(str, removed)), "추가된 BBox 수": added,
                     "Class 별 변화": " ".join(f"C{c}:{d:+d}" for c, d in delta.items()),
                     "Class 5 외 변경 BBox": other})

    print(f" 고친 TXT 폴더: {src}")
    print(f" 바뀐 사진 {len(plan)}장 · 그대로 {unchanged}장 · 교과 7 최종본에 없는 이름 {len(unknown)}개")
    if unknown:
        print("   (건너뜀) " + ", ".join(unknown[:10]) + (" …" if len(unknown) > 10 else ""))
    total = Counter()
    for row in plan:
        for part in row["Class 별 변화"].split():
            c, d = part.split(":")
            total[c] += int(d)
    print(" Class 별 BBox 수 변화: " + (", ".join(f"{c} {d:+d}" for c, d in sorted(total.items())) or "없음"))

    # 작업 목록과 대조: '삭제' 로 정한 박스가 남아 있거나, Class 5 가 아닌 BBox 가 바뀐 사진을 알려 준다
    if WORKLIST.is_file():
        with WORKLIST.open(encoding="utf-8-sig") as f:
            work = list(csv.DictReader(f))
        removed_by = {r["TXT 파일명"].rsplit(".", 1)[0]: set(map(int, r["지운 줄(원본 기준)"].split())) for r in plan}
        missed = [f"{w['화면 번호']}-{w['라벨 목록 No']}" for w in work
                  if w["할 일"] == "삭제" and int(w["라벨 목록 No"]) not in removed_by.get(Path(w["이미지 파일명"]).stem, set())]
        print(f" 작업 목록 '삭제' {sum(w['할 일'] == '삭제' for w in work)}개 중 아직 남아 있는 것: {len(missed)}개"
              + (f" → {', '.join(missed[:15])}" + (" …" if len(missed) > 15 else "") if missed else ""))
    other = [r["TXT 파일명"] for r in plan if r["Class 5 외 변경 BBox"]]
    if other:
        print(f" ⚠ Class 5 외 BBox 가 바뀐 사진 {len(other)}장 (좌표만 바뀐 것 포함): {', '.join(other[:10])}")

    if not args.apply:
        print("\n (확인만 했습니다. 실제로 가져오려면 --apply)")
        return
    if FIX_DIR.exists():
        backup = FIX_DIR.with_name(f"{FIX_DIR.name}_이전_{datetime.now():%Y%m%d_%H%M%S}")
        FIX_DIR.rename(backup)
        print(f" 이전 수정본은 {backup.relative_to(PROJECT_ROOT)} 로 옮겼습니다.")
    FIX_DIR.mkdir(parents=True)
    for row in plan:
        shutil.copy2(row["파일"], FIX_DIR / row["TXT 파일명"])
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    with REPORT.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=[k for k in plan[0] if k != "파일"] if plan else ["TXT 파일명"])
        w.writeheader()
        for row in plan:
            w.writerow({k: v for k, v in row.items() if k != "파일"})
    print(f" 복사 완료: {FIX_DIR.relative_to(PROJECT_ROOT)} ({len(plan)}개) · 기록: {REPORT.relative_to(PROJECT_ROOT)}")
    print(" 다음: python scripts/03_build_split.py --version kimchi_v3 --copy-files")


if __name__ == "__main__":
    main()
