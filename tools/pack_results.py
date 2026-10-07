"""내 작업 결과(라벨 txt + 검수표)를 압축 파일 하나로 묶는다. 팀원에게 전달하기 쉽게 하기 위한 도구다.

    python tools/pack_results.py                        # 전부 묶는다: data/share/결과_날짜_시각.zip
    python tools/pack_results.py --name 김동훈 --from 1 --to 300
                                                        # 검수한 내 범위(번호 1~300)만 묶는다: 결과_김동훈_날짜_시각.zip
    python tools/pack_results.py -o 내결과.zip           # 저장할 이름을 직접 정한다

번호는 프로그램 화면의 'N / 900' 과 같다. (데이터셋 → split → 파일명 순)
검수 결과를 모을 때는 --name 과 --from/--to 를 쓰세요. 이유: 세 명의 결과를 한 곳에 풀어도 파일 이름이 겹치지 않고(검수표가
'검수표_이름.csv'), 내 범위 밖의 옛 라벨이 다른 사람이 고친 라벨을 덮어쓰지 못하기 때문이다.

들어가는 것
  - data/work 안의 라벨(.txt)  (폴더 구조를 그대로 유지: 데이터셋/labels/split/파일.txt)  — --from/--to 가 있으면 그 번호 범위만
  - manifests/dataset_manifest.csv  → zip 안에서는 '검수표.csv' (--name 이 있으면 '검수표_이름.csv', 범위가 있으면 그 줄만)
들어가지 않는 것
  - 사진(jpg), Windows 의 Zone.Identifier 표시 파일, _session.json 등 라벨이 아닌 모든 파일

받는 쪽은 압축을 푼 뒤 아래 두 줄이면 된다.
    python tools/import_labels.py <푼 폴더> --apply
    python tools/merge_manifests.py <푼 폴더>/검수표.csv --apply      (여러 명이면: 푼 폴더 --apply)
라벨과 검수표는 사진 파일명이 들어 있는 회사 데이터다. 허용된 방법으로만 전달하고 Git 에는 올리지 않는다. (data/ 는 .gitignore 에 있다)
"""
import argparse
import csv
import io
import sys
import time
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src import settings                                   # noqa: E402

CSV_NAME = "검수표.csv"


def collect(work_dir):
    """data/work 의 라벨(.txt) 목록과, 무시한(라벨이 아닌) 파일 수를 돌려준다."""
    work_dir = Path(work_dir)
    labels, skipped = [], 0
    if work_dir.is_dir():
        for p in sorted(work_dir.rglob("*")):
            if not p.is_file() or p.is_symlink():
                continue
            if p.suffix.lower() == ".txt":
                labels.append(p)
            else:
                skipped += 1
    return labels, skipped


def photo_numbers(raw_dir):
    """{(데이터셋, split, 사진 파일명): 번호}  — 프로그램 화면의 'N / 900' 과 같은 번호 (데이터셋 → split → 파일명 순)"""
    items = []
    for ds in sorted(p for p in Path(raw_dir).iterdir() if p.is_dir()):
        images = ds / "images"
        if images.is_dir():
            for img in images.rglob("*"):
                if img.is_file() and img.suffix.lower() in settings.IMAGE_EXTS:
                    items.append((ds.name, img.parent.relative_to(images).as_posix(), img.name))
    return {k: i for i, k in enumerate(sorted(items), 1)}


def _label_key(work_dir, p):
    """data/work/<데이터셋>/labels/<split>/<이름>.txt → (데이터셋, split, 사진 파일명 후보 stem)"""
    parts = p.relative_to(work_dir).parts
    if len(parts) >= 4 and parts[1] == "labels":
        return parts[0], "/".join(parts[2:-1]), p.stem
    return None


def pack(out_zip, work_dir=None, manifest_path=None, name=None, number_range=None, raw_dir=None):
    """zip 파일을 만들고 {'labels': 라벨 수, 'manifest': 검수표 줄 수 또는 None, 'skipped': 라벨이 아니라 뺀 파일 수,
    'out_of_range': 범위 밖이라 뺀 라벨 수} 를 돌려준다.  number_range=(처음, 끝) 이면 그 번호의 사진만 담는다."""
    work_dir = Path(work_dir or settings.WORK_DIR)
    manifest_path = Path(manifest_path or settings.MANIFEST_PATH)
    labels, skipped = collect(work_dir)
    numbers, lo, hi = None, None, None
    if number_range:
        lo, hi = number_range
        numbers = photo_numbers(raw_dir or settings.RAW_DIR)
        if not (1 <= lo <= hi <= len(numbers)):
            raise ValueError(f"번호 범위는 1 ~ {len(numbers)} 안에서 정해야 합니다: {lo}~{hi}")

    def in_range(ds, split, photo_name):
        return lo <= numbers.get((ds, split, photo_name), 0) <= hi

    by_stem = {}
    if numbers is not None:
        for (_ds, _split, photo_name), num in numbers.items():
            by_stem.setdefault(Path(photo_name).stem, []).append(num)
    kept, out_of_range = [], 0
    for p in labels:
        if numbers is None:
            kept.append(p)
            continue
        key = _label_key(work_dir, p)
        photo = next((n for n in (key[2] + e for e in (".jpg", ".JPG", ".jpeg", ".JPEG")) if (key[0], key[1], n) in numbers), None) if key else None
        if photo:
            ok = in_range(key[0], key[1], photo)
        else:
            # 폴더 구조가 다른 PC(예: work/data/labels/파일.txt)에서 저장된 라벨은 사진 이름으로 번호를 찾는다. (이름이 raw 에서 하나뿐일 때만)
            nums = by_stem.get(p.stem, [])
            ok = len(nums) == 1 and lo <= nums[0] <= hi
        if ok:
            kept.append(p)
        else:
            out_of_range += 1
    out_zip = Path(out_zip)
    out_zip.parent.mkdir(parents=True, exist_ok=True)
    rows = None
    csv_name = f"검수표_{name}.csv" if name else CSV_NAME
    with zipfile.ZipFile(out_zip, "w", zipfile.ZIP_DEFLATED) as z:
        for p in kept:
            z.write(p, p.relative_to(work_dir).as_posix())
        if manifest_path.is_file():
            with open(manifest_path, encoding="utf-8-sig", newline="") as f:
                reader = csv.DictReader(f)
                header = reader.fieldnames
                data = [r for r in reader if numbers is None or in_range(r.get("출처 데이터셋", ""), r.get("원래 split", ""), r.get("이미지 파일명", ""))]
            buf = io.StringIO(newline="")
            w = csv.DictWriter(buf, fieldnames=header, lineterminator="\r\n")
            w.writeheader()
            w.writerows(data)
            z.writestr(csv_name, ("\ufeff" + buf.getvalue()).encode("utf-8"))      # 엑셀에서도 열리는 UTF-8(BOM)
            rows = len(data)
    return {"labels": len(kept), "manifest": rows, "skipped": skipped, "out_of_range": out_of_range}


def main(argv=None):
    ap = argparse.ArgumentParser(description="라벨(txt)과 검수표를 압축 파일 하나로 묶는다")
    ap.add_argument("-o", "--output", default=None, help="만들 zip 파일 (기본: data/share/결과_날짜_시각.zip)")
    ap.add_argument("--name", default=None, help="내 이름. zip 과 검수표 이름에 붙는다 (예: 김동훈)")
    ap.add_argument("--from", dest="first", type=int, default=None, help="묶을 첫 번호 (프로그램의 N / 900)")
    ap.add_argument("--to", dest="last", type=int, default=None, help="묶을 마지막 번호")
    args = ap.parse_args(argv)
    if (args.first is None) != (args.last is None):
        print("--from 과 --to 는 함께 써야 합니다.")
        return 2
    stamp = time.strftime("%Y%m%d_%H%M%S")
    label = f"결과_{args.name}_{stamp}" if args.name else f"결과_{stamp}"
    out = Path(args.output) if args.output else settings.PROJECT_DIR / "data" / "share" / f"{label}.zip"
    try:
        result = pack(out, name=args.name, number_range=(args.first, args.last) if args.first is not None else None)
    except ValueError as e:
        print(e)
        return 2
    if result["labels"] == 0 and result["manifest"] is None:
        out.unlink(missing_ok=True)
        print("묶을 라벨(txt)과 검수표가 없습니다. 먼저 data/work 와 manifests/dataset_manifest.csv 를 확인하세요.")
        return 2
    print(f"묶었습니다: {out}")
    print(f"  라벨(txt) {result['labels']}개" + (f", 검수표 {result['manifest']}줄" if result["manifest"] is not None else ", 검수표 없음"))
    if args.first is not None:
        print(f"  번호 {args.first}~{args.last} 범위만 담았습니다. (범위 밖 라벨 {result['out_of_range']}개는 넣지 않음)")
    if result["skipped"]:
        print(f"  라벨이 아닌 파일 {result['skipped']}개는 넣지 않았습니다. (Zone.Identifier 등)")
    print(f"  크기: {out.stat().st_size / 1024:.0f} KB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
