"""팀원이 받은 라벨(TXT)을 내 작업 폴더(data/work)로 가져온다.

    python tools/import_labels.py <받은 폴더>               # 먼저 어떻게 될지만 보여 준다 (아무것도 복사하지 않음)
    python tools/import_labels.py <받은 폴더> --apply        # 새 라벨만 복사한다
    python tools/import_labels.py <받은 폴더> --apply --overwrite   # 이름이 같고 내용이 다른 것도 덮어쓴다

탐색기로 복사하면 Windows 가 'xxx.txtZone.Identifier' 같은 표시 파일을 같이 만든다.
이 프로그램은 .txt 파일만 골라 복사하므로 그런 파일이 생기지 않는다. (받은 폴더 안에 있어도 무시한다)

- 어느 데이터셋·split 에 넣을지는 data/raw 의 사진 이름(같은 이름)으로 찾는다. 폴더 구조가 달라도 된다.
- 같은 이름의 사진이 여러 곳에 있으면 받은 폴더의 경로(데이터셋 이름, train/validation)로 구분하고, 그래도 모르면 복사하지 않고 알려 준다.
- 형식이 잘못된 TXT(Class 범위 밖, 좌표 범위 밖 등)는 복사하지 않고 알려 준다.
- 원본(data/raw)은 읽기만 한다.
"""
import argparse
import filecmp
import shutil
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src import settings                                   # noqa: E402
from src.validation.validator import parse_label_file, validate_rows   # noqa: E402


def build_index(raw_dir):
    """{사진 이름(확장자 없음): [(데이터셋, split), ...]}"""
    index = defaultdict(list)
    for ds in sorted(p for p in Path(raw_dir).iterdir() if p.is_dir()):
        images = ds / "images"
        if not images.is_dir():
            continue
        for img in images.rglob("*"):
            if img.is_file() and img.suffix.lower() in settings.IMAGE_EXTS:
                split = img.parent.relative_to(images).as_posix()
                index[img.stem].append((ds.name, split))
    return index


def _choose(candidates, parts):
    """같은 이름의 사진이 여러 곳에 있을 때 받은 파일의 경로로 구분한다. 못 정하면 None."""
    if len(candidates) == 1:
        return candidates[0]
    narrowed = [c for c in candidates if c[0] in parts] or candidates
    narrowed = [c for c in narrowed if c[1] in parts] or narrowed
    return narrowed[0] if len(narrowed) == 1 else None


def plan_import(source, raw_dir=None, work_dir=None):
    """받은 폴더를 살펴서 {종류: [(받은 파일, 넣을 곳 또는 이유), ...]} 로 돌려준다. (복사하지 않는다)

    종류: new(새 라벨) · same(이미 같은 내용) · conflict(이름은 같고 내용이 다름) ·
          unknown(raw 에 같은 이름의 사진이 없음) · ambiguous(같은 이름 사진이 여러 곳) · invalid(형식 오류)
    """
    raw_dir, work_dir = Path(raw_dir or settings.RAW_DIR), Path(work_dir or settings.WORK_DIR)
    index = build_index(raw_dir)
    result = defaultdict(list)
    ignored = 0
    for p in sorted(Path(source).rglob("*")):
        if not p.is_file():
            continue
        if p.suffix.lower() != ".txt":
            ignored += 1                                    # Zone.Identifier 등 .txt 가 아닌 파일
            continue
        candidates = index.get(p.stem)
        if not candidates:
            result["unknown"].append((p, "raw 에 같은 이름의 사진이 없음"))
            continue
        chosen = _choose(candidates, set(p.relative_to(source).parts[:-1]))
        if chosen is None:
            result["ambiguous"].append((p, "같은 이름의 사진이 여러 곳에 있음: " + ", ".join(f"{d}/{s}" for d, s in candidates)))
            continue
        rows, errors = parse_label_file(p)
        problems = [msg for sev, _code, _line, msg in validate_rows(rows, errors) if sev == "CRITICAL"]
        if problems:
            result["invalid"].append((p, problems[0]))
            continue
        target = work_dir / chosen[0] / "labels" / chosen[1] / (p.stem + ".txt")
        if not target.exists():
            result["new"].append((p, target))
        elif filecmp.cmp(p, target, shallow=False):
            result["same"].append((p, target))
        else:
            result["conflict"].append((p, target))
    result["_ignored"] = ignored
    return result


def apply_import(result, overwrite=False):
    """new 는 복사하고, overwrite 이면 conflict 도 덮어쓴다. 복사한 개수를 돌려준다."""
    todo = list(result.get("new", [])) + (list(result.get("conflict", [])) if overwrite else [])
    for src, target in todo:
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, target)                        # 내용만 복사 (Windows 의 표시 정보는 따라오지 않는다)
    return len(todo)


LABELS = [("new", "새 라벨"), ("same", "이미 같은 내용"), ("conflict", "이름은 같고 내용이 다름"),
          ("unknown", "raw 에 없는 이름"), ("ambiguous", "넣을 곳을 정할 수 없음"), ("invalid", "형식 오류")]


def main(argv=None):
    ap = argparse.ArgumentParser(description="팀원이 받은 라벨(TXT)을 data/work 로 가져온다")
    ap.add_argument("source", help="받은 라벨이 들어 있는 폴더")
    ap.add_argument("--apply", action="store_true", help="실제로 복사한다 (없으면 미리보기만)")
    ap.add_argument("--overwrite", action="store_true", help="이름이 같고 내용이 다른 것도 덮어쓴다")
    args = ap.parse_args(argv)
    source = Path(args.source)
    if not source.is_dir():
        print(f"폴더를 찾을 수 없습니다: {source}")
        return 2
    result = plan_import(source)
    print(f"받은 폴더: {source}")
    for key, title in LABELS:
        items = result.get(key, [])
        print(f"  {title:<16} {len(items):>5}개")
        if key in ("conflict", "unknown", "ambiguous", "invalid"):
            for p, why in items[:5]:
                print(f"      - {p.name}: {why if key != 'conflict' else '작업 폴더에 다른 내용이 이미 있음'}")
            if len(items) > 5:
                print(f"      … 외 {len(items) - 5}개")
    if result["_ignored"]:
        print(f"  (.txt 가 아닌 파일 {result['_ignored']}개는 무시했습니다. Zone.Identifier 같은 표시 파일입니다)")
    if not args.apply:
        print("\n미리보기입니다. 복사하려면 --apply 를 붙이세요.")
        return 0
    n = apply_import(result, overwrite=args.overwrite)
    held = len(result.get("conflict", [])) if not args.overwrite else 0
    print(f"\n{n}개를 복사했습니다." + (f" 내용이 다른 {held}개는 그대로 두었습니다 (덮어쓰려면 --overwrite)." if held else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
