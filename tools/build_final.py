"""검수가 끝난 사진과 라벨을 data/final 로 정리한다. (최종본 만들기)

    python tools/build_final.py              # 미리보기: 조건을 확인하고 어떻게 만들지만 보여 준다
    python tools/build_final.py --apply      # 실제로 data/final 을 만든다
    python tools/build_final.py --apply --overwrite   # data/final 에 이미 있으면 data/backup 으로 옮기고 다시 만든다
    python tools/build_final.py --layout flat         # train/validation 구분 없이 한 폴더에 모은다
    python tools/build_final.py --layout nested       # 데이터셋·split 폴더를 그대로 두고 만든다

만드는 것 (기본, split — 원래 train / validation 구분을 폴더로 유지)
  data/final/images/train/<사진>.jpg · images/validation/<사진>.jpg      RAW 의 사진 (복사)
  data/final/labels/train/<사진>.txt · labels/validation/<사진>.txt      data/work 의 검수한 라벨 (없으면 RAW 라벨)
  data/final/classes.txt            Class 0~6 이름 (한 줄에 하나, 번호 순서)
  data/final/검수표.csv              들어간 사진의 검수표 줄 — 출처 데이터셋은 여기서 확인한다
  (split·flat 은 사진 이름이 겹치지 않을 때만 만든다. 겹치면 만들지 않고 알려 준다)
  flat 은 split 구분 없이 images/ · labels/ 한 폴더, nested 는 data/final/<데이터셋>/images|labels/<split>/ 로 원래 폴더를 그대로 둔다.
  어느 쪽이든 train/validation 을 새로 나누거나 섞지는 않는다 (교과 8 에서 결정)

만들기 전에 확인하는 것 (하나라도 어긋나면 만들지 않는다)
  - 모든 사진이 검수표에 있고 상태가 '검수 완료' 또는 '수정 완료' 이다 (검수 전·수정 필요·제외는 최종본에 넣지 않는다)
  - 검수자 칸이 채워져 있고, 작성자와 같지 않다
  - 짝이 맞고(사진 1 : 라벨 1) Validation 의 치명적 오류(CRITICAL)가 0건이다
RAW 와 data/work 는 읽기만 한다. data/final 은 회사 데이터라 Git 에 올리지 않는다. (data/ 는 .gitignore 에 있다)
"""
import argparse
import csv
import shutil
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src import settings                                   # noqa: E402
from src.validation import validator                       # noqa: E402

OK_STATUS = ("검수 완료", "수정 완료")
CLASSES_NAME = "classes.txt"
MANIFEST_NAME = "검수표.csv"


def _key(row):
    return row.get("출처 데이터셋", ""), row.get("원래 split", ""), row.get("이미지 파일명", "")


def collect_photos(raw_dir):
    """RAW 의 사진 목록 [(데이터셋, split, 사진 경로)] — 데이터셋 → split → 파일명 순"""
    out = []
    for ds in sorted(p for p in Path(raw_dir).iterdir() if p.is_dir()):
        images = ds / "images"
        if not images.is_dir():
            continue
        for img in sorted(images.rglob("*")):
            if img.is_file() and img.suffix.lower() in settings.IMAGE_EXTS:
                out.append((ds.name, img.parent.relative_to(images).as_posix(), img))
    return out


def label_source(raw_dir, work_dir, ds, split, stem):
    """최종본에 넣을 라벨 — data/work 에 있으면 그것, 없으면 RAW 라벨. 둘 다 없으면 None"""
    w = Path(work_dir) / ds / "labels" / split / f"{stem}.txt"
    if w.is_file():
        return w, False
    r = Path(raw_dir) / ds / "labels" / split / f"{stem}.txt"
    return (r, True) if r.is_file() else (None, False)


def check(raw_dir=None, work_dir=None, manifest_path=None, layout="split"):
    """최종본을 만들 수 있는지 확인한다.

    {'items': 들어갈 사진 목록, 'blocked': {이유: [사진...]}, 'validation': {CRITICAL 등 개수}, 'raw_labels': RAW 라벨을 쓴 수, 'rows': 검수표 줄}
    blocked 가 비어 있어야 만들 수 있다.  layout 이 flat · split 이면 사진 이름이 겹치는 경우도 막는다.
    """
    raw_dir = Path(raw_dir or settings.RAW_DIR)
    work_dir = Path(work_dir or settings.WORK_DIR)
    manifest_path = Path(manifest_path or settings.MANIFEST_PATH)
    photos = collect_photos(raw_dir)
    blocked = {}

    def block(reason, name):
        blocked.setdefault(reason, []).append(name)

    rows = {}
    if manifest_path.is_file():
        with open(manifest_path, encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            header = reader.fieldnames
            for r in reader:
                rows[_key(r)] = r
    else:
        header = None
        blocked["검수표(manifests/dataset_manifest.csv)가 없음"] = [str(manifest_path)]

    items, raw_labels, kept_rows = [], 0, []
    for ds, split, img in photos:
        name = f"{ds}/{split}/{img.name}"
        row = rows.get((ds, split, img.name))
        if row is None:
            block("검수표에 줄이 없음", name)
            continue
        if row.get("상태") not in OK_STATUS:
            block(f"상태가 '검수 완료'·'수정 완료'가 아님 ({row.get('상태') or '비어 있음'})", name)
            continue
        if not (row.get("검수자") or "").strip():
            block("검수자 칸이 비어 있음", name)
            continue
        if (row.get("작성자") or "").strip() == row["검수자"].strip():
            block("작성자와 검수자가 같음", name)
            continue
        label, from_raw = label_source(raw_dir, work_dir, ds, split, img.stem)
        if label is None:
            block("라벨(TXT)이 없음", name)
            continue
        raw_labels += from_raw
        items.append({"dataset": ds, "split": split, "image": img, "label": label, "name": name})
        kept_rows.append(row)

    if layout in ("flat", "split"):
        seen = {}
        for it in items:
            seen.setdefault((it["split"] if layout == "split" else "", it["image"].name), []).append(it["name"])
        for names in seen.values():
            if len(names) > 1:
                for n in names:
                    block(f"{layout} 구조에서 사진 이름이 겹침 (--layout nested 로 만들 수 있음)", n)
    report = validator.validate_dataset(raw_dir=raw_dir, work_dir=work_dir)
    counts = {}
    for item in report:
        counts[item["severity"]] = counts.get(item["severity"], 0) + 1
    for item in report:
        if item["severity"] == "CRITICAL":
            block(f"Validation 치명적 오류 ({item['code']})", item["relative_path"])
    return {"items": items, "blocked": blocked, "validation": counts, "raw_labels": raw_labels,
            "rows": kept_rows, "header": header}


def existing_content(final_dir):
    """data/final 에 이미 들어 있는 파일 수 (.gitkeep 과 빈 폴더 골격은 세지 않는다)"""
    final_dir = Path(final_dir)
    if not final_dir.is_dir():
        return 0
    return sum(1 for p in final_dir.rglob("*") if p.is_file() and p.name != ".gitkeep")


def build(result, final_dir=None, overwrite=False, backup_dir=None, classes=None, layout="split"):
    """check() 결과로 data/final 을 만든다. 만든 사진 수를 돌려준다.  이미 내용이 있으면 overwrite 가 있어야 하고, 옛것은 backup_dir 로 옮긴다."""
    final_dir = Path(final_dir or settings.FINAL_DIR)
    if result["blocked"]:
        raise ValueError("조건을 채우지 못해 만들지 않았습니다.")
    moved = None
    if existing_content(final_dir):
        if not overwrite:
            raise FileExistsError(f"{final_dir} 에 이미 파일이 있습니다. 다시 만들려면 --overwrite (옛것은 data/backup 으로 옮깁니다)")
        moved = Path(backup_dir or settings.PROJECT_DIR / "data" / "backup" / f"final_교체전_{time.strftime('%Y%m%d_%H%M%S')}")
        moved.mkdir(parents=True)
        for p in sorted(final_dir.iterdir()):
            if p.name != ".gitkeep":
                shutil.move(str(p), str(moved / p.name))
    final_dir.mkdir(parents=True, exist_ok=True)
    for it in result["items"]:
        for kind, src in (("images", it["image"]), ("labels", it["label"])):
            if layout == "flat":
                dst_dir = final_dir / kind
            elif layout == "split":
                dst_dir = final_dir / kind / it["split"]
            else:
                dst_dir = final_dir / it["dataset"] / kind / it["split"]
            dst_dir.mkdir(parents=True, exist_ok=True)
            dst = dst_dir / (src.name if kind == "images" else f"{it['image'].stem}.txt")
            shutil.copyfile(src, dst)
            if dst.stat().st_size != src.stat().st_size:
                raise OSError(f"복사 결과가 원본과 다릅니다: {dst}")
    names = [c["name"] for c in (classes or settings.CLASSES)]
    (final_dir / CLASSES_NAME).write_text("\n".join(names) + "\n", encoding="utf-8")
    if result["header"]:
        with open(final_dir / MANIFEST_NAME, "w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=result["header"], lineterminator="\r\n")
            w.writeheader()
            w.writerows(result["rows"])
    return {"photos": len(result["items"]), "moved_old_to": moved}


def summarize(result):
    """들어가는 사진을 데이터셋/split 별로 센다."""
    counts = {}
    for it in result["items"]:
        counts[(it["dataset"], it["split"])] = counts.get((it["dataset"], it["split"]), 0) + 1
    return counts


def main(argv=None):
    ap = argparse.ArgumentParser(description="검수가 끝난 사진과 라벨을 data/final 로 정리한다")
    ap.add_argument("--apply", action="store_true", help="실제로 만든다 (없으면 미리보기만)")
    ap.add_argument("--overwrite", action="store_true", help="data/final 에 이미 있으면 data/backup 으로 옮기고 다시 만든다")
    ap.add_argument("--layout", choices=("split", "flat", "nested"), default="split",
                    help="split: images/train · images/validation 처럼 원래 split 을 폴더로 유지 (기본)  flat: 한 폴더에 모은다  nested: 데이터셋·split 폴더를 그대로 둔다")
    args = ap.parse_args(argv)

    result = check(layout=args.layout)
    print(f"원본 사진 중 최종본에 들어갈 사진: {len(result['items'])}장   (구조: {args.layout})")
    for (ds, split), n in sorted(summarize(result).items()):
        print(f"  {ds} / {split}: {n}장")
    print(f"Validation: {result['validation'] or '문제 없음'}   (CRITICAL 만 막고, WARNING·INFO 는 알려 주기만 함)")
    if result["raw_labels"]:
        print(f"  ⚠ 작업본(data/work)에 없어서 RAW 라벨을 쓴 사진: {result['raw_labels']}장")
    if result["blocked"]:
        print("\n⚠ 아래 문제 때문에 만들 수 없습니다. 먼저 해결하세요.")
        for reason, names in result["blocked"].items():
            print(f"  - {reason}: {len(names)}장")
            for n in names[:5]:
                print(f"      {n}")
            if len(names) > 5:
                print(f"      … 외 {len(names) - 5}장")
        return 1
    if not args.apply:
        print("\n미리보기입니다. 만들려면 --apply 를 붙이세요.")
        return 0
    try:
        done = build(result, overwrite=args.overwrite, layout=args.layout)
    except FileExistsError as e:
        print(e)
        return 1
    print(f"\n만들었습니다: {settings.FINAL_DIR}  (사진 {done['photos']}장 + 라벨 {done['photos']}개)")
    if done["moved_old_to"]:
        print(f"이전 최종본은 {done['moved_old_to']} 로 옮겨 두었습니다.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
