"""데이터 조사(Validation 의 기초) — RAW 의 개수·짝(Pair)·빈 TXT·Class 분포를 조사한다.

RAW 를 "읽기만" 한다. 파일을 고치거나 복사하지 않는다.
(좌표 범위·BBox 경계 같은 자세한 자동 검사는 이후 단계에서 이 모듈에 추가한다)
"""
from collections import Counter
from pathlib import Path

from src import settings


def scan_inventory(raw_dir):
    """raw_dir 안의 데이터셋을 조사해 (rows, summary) 를 돌려준다.

    rows    : [{dataset, split, image, label, pair, empty, bad}, ...]  (데이터셋/split 별 한 줄)
    summary : {"class_bbox": Counter, "bad_lines": int, "out_of_range": [..]}
    """
    rows = []
    class_bbox = Counter()
    raw_dir = Path(raw_dir)
    if not raw_dir.is_dir():
        return rows, {"class_bbox": class_bbox, "bad_lines": 0, "out_of_range": []}

    for ds_dir in sorted(p for p in raw_dir.iterdir() if p.is_dir()):
        img_root, lbl_root = ds_dir / "images", ds_dir / "labels"
        splits = set()
        for root in (img_root, lbl_root):
            if root.is_dir():
                splits |= {p.name for p in root.iterdir() if p.is_dir()}
        for split in sorted(splits):
            images = {p.stem for p in (img_root / split).glob("*")
                      if p.is_file() and p.suffix.lower() in settings.IMAGE_EXTS} if (img_root / split).is_dir() else set()
            labels = {p.stem: p for p in (lbl_root / split).glob("*.txt")} if (lbl_root / split).is_dir() else {}
            empty = bad = 0
            for path in labels.values():
                text = path.read_text(encoding="utf-8", errors="replace")
                if not text.strip():
                    empty += 1                                    # 내용이 빈 TXT (정상 김치 후보)
                for line in text.splitlines():
                    parts = line.split()
                    if not parts:
                        continue
                    try:
                        if len(parts) != 5:
                            raise ValueError
                        class_bbox[int(parts[0])] += 1
                        [float(v) for v in parts[1:]]
                    except ValueError:
                        bad += 1                                  # 읽을 수 없는 줄
            rows.append({"dataset": ds_dir.name, "split": split, "image": len(images), "label": len(labels),
                         "pair": len(images & set(labels)), "empty": empty, "bad": bad})
    summary = {"class_bbox": class_bbox, "bad_lines": sum(r["bad"] for r in rows),
               "out_of_range": sorted(c for c in class_bbox if not 0 <= c < len(settings.CLASSES))}
    return rows, summary


def inventory_markdown(rows, summary):
    """조사 결과를 옵시디언/문서에 그대로 붙여 넣을 수 있는 마크다운 표로 만든다."""
    L = ["| source_dataset | original_split | image_count | label_count | pair_count | empty_label_count |",
         "|---|---|---:|---:|---:|---:|"]
    for r in rows:
        L.append(f"| {r['dataset']} | {r['split']} | {r['image']} | {r['label']} | {r['pair']} | {r['empty']} |")
    tot = {k: sum(r[k] for r in rows) for k in ("image", "label", "pair", "empty")}
    L.append(f"| **합계** | | **{tot['image']}** | **{tot['label']}** | **{tot['pair']}** | **{tot['empty']}** |")
    L += ["", f"- JPG 만 있고 TXT 없음: {tot['image'] - tot['pair']}개  /  TXT 만 있고 JPG 없음: {tot['label'] - tot['pair']}개",
          f"- 읽을 수 없는 TXT 줄: {summary['bad_lines']}줄", "", "| Class | 이름 | BBox 수 |", "|---:|---|---:|"]
    for c in settings.CLASSES:
        L.append(f"| {c['id']} | {settings.class_name(c['id'])} | {summary['class_bbox'].get(c['id'], 0)} |")
    L.append("")
    L.append(f"- 0~{len(settings.CLASSES) - 1} 범위를 벗어난 Class ID: {summary['out_of_range'] or '없음'}")
    unused = sum(summary["class_bbox"].get(c, 0) for c in settings.UNUSED_CLASSES)
    if unused:
        L.append(f"- ⚠ 사용 안 하는 Class 의 BBox {unused}개 → 삭제하지 말고 REVIEW 대상으로 기록")
    return "\n".join(L)
