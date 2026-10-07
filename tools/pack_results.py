"""내 작업 결과(라벨 txt + 검수표)를 압축 파일 하나로 묶는다. 팀원에게 전달하기 쉽게 하기 위한 도구다.

    python tools/pack_results.py                        # data/share/결과_날짜_시각.zip 을 만든다
    python tools/pack_results.py -o 내결과.zip           # 이름을 정한다

들어가는 것
  - data/work 안의 라벨(.txt) 전부  (폴더 구조를 그대로 유지: 데이터셋/labels/split/파일.txt)
  - manifests/dataset_manifest.csv  → zip 안에서는 '검수표.csv'
들어가지 않는 것
  - 사진(jpg), Windows 의 Zone.Identifier 표시 파일, _session.json 등 라벨이 아닌 모든 파일

받는 쪽은 압축을 푼 뒤 아래 두 줄이면 된다.
    python tools/import_labels.py <푼 폴더> --apply
    python tools/merge_manifests.py <푼 폴더>/검수표.csv --apply
라벨과 검수표는 사진 파일명이 들어 있는 회사 데이터다. 허용된 방법으로만 전달하고 Git 에는 올리지 않는다. (data/ 는 .gitignore 에 있다)
"""
import argparse
import csv
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


def pack(out_zip, work_dir=None, manifest_path=None):
    """zip 파일을 만들고 {'labels': 라벨 수, 'manifest': 검수표 줄 수 또는 None, 'skipped': 무시한 파일 수} 를 돌려준다."""
    work_dir = Path(work_dir or settings.WORK_DIR)
    manifest_path = Path(manifest_path or settings.MANIFEST_PATH)
    labels, skipped = collect(work_dir)
    out_zip = Path(out_zip)
    out_zip.parent.mkdir(parents=True, exist_ok=True)
    rows = None
    with zipfile.ZipFile(out_zip, "w", zipfile.ZIP_DEFLATED) as z:
        for p in labels:
            z.write(p, p.relative_to(work_dir).as_posix())
        if manifest_path.is_file():
            z.write(manifest_path, CSV_NAME)
            with open(manifest_path, encoding="utf-8-sig", newline="") as f:
                rows = max(0, sum(1 for _ in csv.reader(f)) - 1)         # 칸 안에 줄바꿈이 있어도 줄 수가 맞도록 csv 로 센다
    return {"labels": len(labels), "manifest": rows, "skipped": skipped}


def main(argv=None):
    ap = argparse.ArgumentParser(description="라벨(txt)과 검수표를 압축 파일 하나로 묶는다")
    ap.add_argument("-o", "--output", default=None, help="만들 zip 파일 (기본: data/share/결과_날짜_시각.zip)")
    args = ap.parse_args(argv)
    out = Path(args.output) if args.output else settings.PROJECT_DIR / "data" / "share" / f"결과_{time.strftime('%Y%m%d_%H%M%S')}.zip"
    result = pack(out)
    if result["labels"] == 0 and result["manifest"] is None:
        out.unlink(missing_ok=True)
        print("묶을 라벨(txt)과 검수표가 없습니다. 먼저 data/work 와 manifests/dataset_manifest.csv 를 확인하세요.")
        return 2
    print(f"묶었습니다: {out}")
    print(f"  라벨(txt) {result['labels']}개" + (f", 검수표 {result['manifest']}줄" if result["manifest"] is not None else ", 검수표 없음"))
    if result["skipped"]:
        print(f"  라벨이 아닌 파일 {result['skipped']}개는 넣지 않았습니다. (Zone.Identifier 등)")
    print(f"  크기: {out.stat().st_size / 1024:.0f} KB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
