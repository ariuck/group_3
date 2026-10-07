"""팀원들의 검수표(CSV)를 하나로 합친다.

    python tools/merge_manifests.py 나.csv 동훈.csv 혜성.csv ...          # 미리보기 (아무것도 쓰지 않음)
    python tools/merge_manifests.py 받은폴더                              # 폴더 안의 *.csv 를 모두 합친다
    python tools/merge_manifests.py 받은폴더 --apply                      # manifests/dataset_manifest.csv 에 저장
    python tools/merge_manifests.py ... --apply -o 합친결과.csv            # 저장할 이름을 정한다

규칙
  - 사진 1장 = 1줄. 키 = 이미지 파일명 + 출처 데이터셋 + 원래 split.
  - 출처 데이터셋·split 이 비었거나 data/raw 에 없는 값(예: 팀원 컴퓨터의 폴더 이름)이면 사진 이름으로 data/raw 에서 찾아 바로잡는다.
    그래도 알 수 없는 줄이 있으면 **조용히 빼지 않고** 알려 주며, 그 줄이 있으면 저장하지 않는다.
  - 같은 사진이 여러 파일에 있고 내용이 같으면 하나로 합친다.
  - 내용이 다르면(충돌) 아래 순서로 하나를 고르고, 어떤 사진이 어떻게 갈렸는지 알려 준다. 알려 준 사진은 직접 확인한다.
        ① '검수 전' 이 아닌 줄  ② 검수일이 더 늦은 줄  ③ 뒤에 넣은 파일의 줄
  - 합친 뒤 출처 데이터셋 · split · 파일명 순으로 정렬하고 No 를 1 부터 다시 매긴다.
  - 저장할 파일(기본: manifests/dataset_manifest.csv)이 이미 있으면 **먼저 같은 폴더에 백업**을 남기고 덮어쓴다.
    그 파일이 입력에 없어도 내 기존 줄이 사라지지 않도록 자동으로 함께 합친다. (입력으로 받은 다른 파일은 고치지 않는다)
  - 머리글(19칸)이 다르거나 엑셀 cp949 로 저장된 파일은 어느 파일이 문제인지 알리고 중단한다.
검수표에는 사진 파일명이 들어 있어 회사 데이터이므로 Git 에 올리지 않는다. (manifests/*.csv 는 .gitignore 에 있다)
"""
import argparse
import shutil
import sys
import time
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src import settings                                                       # noqa: E402
from src.manifest.manifest_writer import (HEADERS, STATUS_BEFORE, STATUS_REVIEW, ManifestError,   # noqa: E402
                                          _load, _save)

KEY = ("출처 데이터셋", "원래 split", "이미지 파일명")
DEFAULT_OUTPUT = settings.MANIFEST_PATH        # 프로그램이 읽고 쓰는 검수표 = manifests/dataset_manifest.csv


def key_of(row):
    return tuple(row[k] for k in KEY)


def _same(a, b):
    return all(a[h] == b[h] for h in HEADERS if h != "No")


def _rank(row):
    """충돌할 때 이긴 줄을 고르는 값: '검수 전' 이 아닌 것 > 검수일이 늦은 것. (같으면 뒤에 넣은 파일이 이긴다)"""
    return (row["상태"] not in ("", STATUS_BEFORE), row["검수일"])


def load_inputs(paths):
    """입력(파일 또는 폴더)에서 [(이름, 줄 목록)] 을 읽는다. 읽을 수 없으면 ManifestError."""
    files = []
    for p in paths:
        p = Path(p)
        if p.is_dir():
            files += sorted(q for q in p.glob("*.csv") if q.is_file())
        elif p.is_file():
            files.append(p)
        else:
            raise ManifestError(f"파일이나 폴더를 찾을 수 없습니다: {p}")
    if not files:
        raise ManifestError("합칠 CSV 파일이 없습니다.")
    loaded = []
    for f in files:
        try:
            loaded.append((f, _load(f)))
        except ManifestError as e:
            raise ManifestError(f"[{f.name}] {e}")
    return loaded


def raw_name_index(raw_dir):
    """{사진 파일명(확장자 포함): [(데이터셋, split), ...]}  — data/raw 의 실제 사진 위치"""
    index = {}
    for ds in sorted(p for p in Path(raw_dir).iterdir() if p.is_dir()):
        images = ds / "images"
        if not images.is_dir():
            continue
        for img in images.rglob("*"):
            if img.is_file() and img.suffix.lower() in settings.IMAGE_EXTS:
                index.setdefault(img.name, []).append((ds.name, img.parent.relative_to(images).as_posix()))
    return index


def normalize_sources(loaded, raw_index):
    """출처 데이터셋·split 이 비었거나 raw 에 없는 조합이면 사진 이름으로 raw 에서 찾아 줄을 바로잡는다. (줄을 직접 고친다)

    돌려주는 값: ({파일 이름: 바로잡은 줄 수}, [(파일 이름, 사진 이름 또는 '', 이유), ...] = 알 수 없는 줄)
    - raw 에서 같은 이름의 사진이 한 곳뿐이면 그 위치로 바로잡는다. 여러 곳이면 줄에 적힌 데이터셋으로 좁혀 보고, 그래도 못 정하면 알 수 없는 줄.
    - raw 에 없는 사진이라도 데이터셋과 split 이 둘 다 적혀 있으면 확인할 수 없으므로 그대로 둔다.
    - 줄이 완전히 비어 있으면(엑셀의 빈 줄) 무시한다.
    """
    valid = {pair for pairs in raw_index.values() for pair in pairs}
    fixed, unresolved = {}, []
    for f, rows in loaded:
        for row in rows:
            name = row["이미지 파일명"]
            if not name:
                if any(row[h] for h in HEADERS if h != "No"):
                    unresolved.append((f.name, "", "이미지 파일명이 비어 있음"))
                continue
            if (row["출처 데이터셋"], row["원래 split"]) in valid:
                continue
            cands = raw_index.get(name, [])
            if len(cands) > 1:
                cands = [c for c in cands if c[0] == row["출처 데이터셋"]] or cands
            if len(cands) == 1:
                row["출처 데이터셋"], row["원래 split"] = cands[0]
                fixed[f.name] = fixed.get(f.name, 0) + 1
            elif len(cands) > 1:
                unresolved.append((f.name, name, "같은 이름의 사진이 raw 의 여러 곳에 있음"))
            elif not (row["출처 데이터셋"] and row["원래 split"]):
                unresolved.append((f.name, name, "raw 에 없는 사진이고 출처가 비어 있음"))
    return fixed, unresolved


def merge(loaded):
    """[(파일, 줄 목록)] → (합친 줄 목록, 충돌 목록, 같은 줄 수). 충돌 = [(키, [(파일 이름, 줄)...], 고른 파일 이름)]"""
    by_key, order = {}, []
    for f, rows in loaded:
        for row in rows:
            if not (row["이미지 파일명"] and row["출처 데이터셋"] and row["원래 split"]):
                continue                                              # 사진을 알 수 없는 줄(빈 줄 등)은 건너뛴다
            k = key_of(row)
            if k not in by_key:
                by_key[k] = []
                order.append(k)
            by_key[k].append((f.name, row))
    merged, conflicts, duplicates = [], [], 0
    for k in order:
        entries = by_key[k]
        winner = entries[0]
        distinct = [entries[0]]
        for e in entries[1:]:
            if _same(e[1], winner[1]):
                duplicates += 1
                continue
            distinct.append(e)
            if _rank(e[1]) >= _rank(winner[1]):
                winner = e
        if len(distinct) > 1:
            conflicts.append((k, [(n, r) for n, r in distinct], winner[0]))
        merged.append(dict(winner[1]))
    merged.sort(key=key_of)
    for i, row in enumerate(merged, 1):
        row["No"] = str(i)
    return merged, conflicts, duplicates


def summarize(rows, raw_dir=None):
    """합친 결과를 한눈에 볼 수 있는 숫자로 정리한다. (사진 이름은 넣지 않는다)"""
    status = Counter(r["상태"] or "(비어 있음)" for r in rows)
    no_author = sum(1 for r in rows if not r["작성자"])
    same_person = sum(1 for r in rows if r["검수자"] and r["검수자"] == r["작성자"])
    open_review = sum(1 for r in rows if r["상태"] == STATUS_REVIEW and r["발견된 문제"].startswith("REVIEW"))
    result = {"total": len(rows), "status": dict(status), "no_author": no_author,
              "same_person": same_person, "open_review": open_review, "missing": None}
    raw_dir = Path(raw_dir or settings.RAW_DIR)
    if raw_dir.is_dir():
        have = {key_of(r) for r in rows}
        total = missing = 0
        for ds in sorted(p for p in raw_dir.iterdir() if p.is_dir()):
            images = ds / "images"
            if not images.is_dir():
                continue
            for img in images.rglob("*"):
                if img.is_file() and img.suffix.lower() in settings.IMAGE_EXTS:
                    total += 1
                    split = img.parent.relative_to(images).as_posix()
                    if (ds.name, split, img.name) not in have:
                        missing += 1
        result["raw_total"], result["missing"] = total, missing
    return result


def main(argv=None):
    ap = argparse.ArgumentParser(description="팀원들의 검수표(CSV)를 하나로 합친다")
    ap.add_argument("inputs", nargs="+", help="합칠 CSV 파일들 또는 CSV 가 들어 있는 폴더")
    ap.add_argument("-o", "--output", default=str(DEFAULT_OUTPUT), help="저장할 파일 (기본: manifests/dataset_manifest.csv)")
    ap.add_argument("--apply", action="store_true", help="실제로 저장한다 (없으면 미리보기만)")
    ap.add_argument("--raw", default=None, help="사진 위치를 확인할 원본 폴더 (기본: data/raw)")
    args = ap.parse_args(argv)
    try:
        loaded = load_inputs(args.inputs)
    except ManifestError as e:
        print(e)
        return 2
    out = Path(args.output).resolve()
    if out.is_file() and not any(f.resolve() == out for f, _ in loaded):
        try:
            loaded.insert(0, (out, _load(out)))                 # 내 기존 검수표도 함께 합쳐서 기존 줄이 사라지지 않게 한다
        except ManifestError as e:
            print(f"[{out.name}] {e}")
            return 2
        print(f"저장할 파일({out.name})에 이미 있는 줄도 함께 합칩니다.")
    raw_dir = Path(args.raw or settings.RAW_DIR)
    fixed, unresolved = ({}, [])
    if raw_dir.is_dir():
        fixed, unresolved = normalize_sources(loaded, raw_name_index(raw_dir))
    merged, conflicts, dup = merge(loaded)
    print("합치는 파일:")
    for f, rows in loaded:
        note = f"  (출처 데이터셋·split 을 data/raw 에서 찾아 바로잡은 줄 {fixed[f.name]}개)" if f.name in fixed else ""
        print(f"  {f.name}: {len(rows)}줄{note}")
    print(f"\n합친 결과: {len(merged)}줄  (같은 내용이라 하나로 합친 줄 {dup}개, 내용이 달라 고른 줄 {len(conflicts)}개)")
    for k, entries, winner in conflicts[:10]:
        print(f"  충돌: {k[0]}/{k[1]}/{k[2]}  → {winner} 의 줄을 선택 (" +
              " | ".join(f"{n}: {r['상태'] or '-'} {r['검수일'] or ''}".strip() for n, r in entries) + ")")
    if len(conflicts) > 10:
        print(f"  … 외 {len(conflicts) - 10}개")
    s = summarize(merged)
    print("\n상태별: " + "  ".join(f"{k} {v}" for k, v in sorted(s["status"].items())))
    print(f"작성자가 비어 있는 줄: {s['no_author']}   작성자와 검수자가 같은 줄: {s['same_person']}   미처리 REVIEW: {s['open_review']}")
    if s["missing"] is not None:
        print(f"원본 사진 {s['raw_total']}장 중 검수표에 줄이 없는 사진: {s['missing']}장")
    if unresolved:
        print(f"\n⚠ 사진 위치(출처 데이터셋·split)를 알 수 없는 줄 {len(unresolved)}개가 있어 합친 결과에 들어가지 않았습니다.")
        for fname, photo, why in unresolved[:8]:
            print(f"  - [{fname}] {photo or '(이름 없음)'}: {why}")
        if len(unresolved) > 8:
            print(f"  … 외 {len(unresolved) - 8}개")
    if not args.apply:
        print("\n미리보기입니다. 저장하려면 --apply 를 붙이세요.")
        return 0
    if unresolved:
        print("\n알 수 없는 줄이 있어 저장하지 않았습니다. 해당 파일을 확인한 뒤 다시 실행하세요.")
        return 2
    backup = None
    try:
        if out.is_file():
            backup = out.with_name(f"{out.stem}.백업-{time.strftime('%Y%m%d_%H%M%S')}{out.suffix}")
            shutil.copy2(out, backup)                            # 덮어쓰기 전에 지금 파일을 그대로 남겨 둔다
        _save(out, merged)
    except (ManifestError, OSError) as e:
        print(e)
        return 2
    print(f"\n저장했습니다: {out}")
    if backup:
        print(f"덮어쓰기 전 파일은 {backup.name} 로 남겨 두었습니다. (문제가 없으면 지워도 됩니다)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
