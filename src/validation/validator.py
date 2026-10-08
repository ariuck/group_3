"""데이터 조사 및 자동 Validation 모듈.

1. scan_inventory(): RAW 의 전체 개수·짝(Pair)·빈 TXT·Class 분포 조사
2. validate_dataset(): 개별 이미지/TXT 의 무결성(Class, 좌표 범위, 경계 초과, 중복 등) 정밀 검증
"""
import csv
from collections import Counter
from pathlib import Path

from src import settings

EPS = 1e-6
REPORT_FIELDS = ["severity", "code", "relative_path", "line", "message"]


def scan_inventory(raw_dir):
    """raw_dir 안의 데이터셋을 조사해 (rows, summary) 를 돌려준다."""
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
                text = path.read_text(encoding="utf-8-sig", errors="replace")
                if not text.strip():
                    empty += 1
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
                        bad += 1
            rows.append({"dataset": ds_dir.name, "split": split, "image": len(images), "label": len(labels),
                         "pair": len(images & set(labels)), "empty": empty, "bad": bad})
    summary = {"class_bbox": class_bbox, "bad_lines": sum(r["bad"] for r in rows),
               "out_of_range": sorted(c for c in class_bbox if not 0 <= c < len(settings.CLASSES))}
    return rows, summary


def inventory_markdown(rows, summary):
    """조사 결과를 마크다운 표로 만든다."""
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


def _iou(a, b):
    """두 YOLO BBox (cls, xc, yc, w, h) 간의 IoU 계산."""
    ax1, ay1, ax2, ay2 = a[1] - a[3] / 2, a[2] - a[4] / 2, a[1] + a[3] / 2, a[2] + a[4] / 2
    bx1, by1, bx2, by2 = b[1] - b[3] / 2, b[2] - b[4] / 2, b[1] + b[3] / 2, b[2] + b[4] / 2
    iw = min(ax2, bx2) - max(ax1, bx1)
    ih = min(ay2, by2) - max(ay1, by1)
    if iw <= 0 or ih <= 0:
        return 0.0
    inter = iw * ih
    union = (a[3] * a[4]) + (b[3] * b[4]) - inter
    return inter / union if union > 0 else 0.0


def validate_rows(rows, errors):
    """한 TXT 파일의 BBox 행들을 검사한다.
    
    returns: [(severity, code, line_no, message), ...]
    severity: CRITICAL / WARNING / INFO
    """
    out = [("CRITICAL", code, no, msg) for no, code, msg in errors]
    num_classes = len(settings.CLASSES)

    for i, (cls, xc, yc, w, h) in enumerate(rows, 1):
        # 1. Class ID 범위 검사
        if not 0 <= cls < num_classes:
            out.append(("CRITICAL", "CLASS_RANGE", i, f"Class {cls} 는 0~{num_classes - 1} 범위를 벗어남"))
        elif cls in settings.UNUSED_CLASSES:
            out.append(("WARNING", "CLASS_DISABLED", i, f"Class {cls} 는 사용하지 않는 Class → REVIEW 대상으로 처리"))

        # 2. 좌표 및 크기 유효성 검사
        if any(not 0 <= v <= 1 for v in (xc, yc, w, h)):
            out.append(("CRITICAL", "COORD_RANGE", i, f"좌표/크기가 0~1 범위를 벗어남: {xc} {yc} {w} {h}"))
        
        if w <= 0 or h <= 0:
            out.append(("CRITICAL", "SIZE_INVALID", i, f"Width/Height 가 0 이하: w={w}, h={h}"))
            continue

        # 3. 이미지 경계 이탈 검사
        if (xc - w / 2 < -EPS) or (yc - h / 2 < -EPS) or (xc + w / 2 > 1 + EPS) or (yc + h / 2 > 1 + EPS):
            out.append(("CRITICAL", "BOX_OUT_OF_IMAGE", i, "BBox 가 이미지 경계 밖으로 나감"))

        # 4. 너무 작은 BBox 경고
        if w < 0.002 or h < 0.002:
            out.append(("WARNING", "TINY_BOX", i, f"BBox 가 매우 작음 (w={w:.4f}, h={h:.4f})"))

    # 5. 중복 박스 검사 (IoU >= 0.95)
    for i in range(len(rows)):
        for j in range(i + 1, len(rows)):
            if rows[i][0] == rows[j][0] and _iou(rows[i], rows[j]) >= 0.95:
                out.append(("WARNING", "DUPLICATE_BOX", j + 1, f"{i + 1}번 줄과 거의 같은 BBox (중복 의심)"))

    # 6. 빈 라벨 안내
    if not rows and not errors:
        out.append(("INFO", "EMPTY_LABEL", 0, "빈 TXT — 정상 김치(객체 없음)인지 확인 필요"))

    return out


def parse_label_file(path):
    """TXT 파일을 파싱하여 (rows, errors) 반환."""
    rows = []
    errors = []
    path = Path(path)
    if not path.is_file():
        return rows, errors

    text = path.read_text(encoding="utf-8-sig", errors="replace")
    for no, line in enumerate(text.splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        parts = line.split()
        if len(parts) != 5:
            errors.append((no, "BAD_FORMAT", f"한 줄은 5개 값이어야 함 (실제 {len(parts)}개)"))
            continue
        try:
            cls = int(parts[0])
            coords = [float(v) for v in parts[1:]]
            rows.append((cls, coords[0], coords[1], coords[2], coords[3]))
        except ValueError:
            errors.append((no, "BAD_NUMBER", f"숫자로 변환할 수 없음: {line}"))
    return rows, errors


def validate_dataset(items=None, raw_dir=None, work_dir=None):
    """데이터셋의 모든 이미지와 라벨을 검사하여 결함 보고서 목록을 반환한다."""
    report = []
    raw_dir = Path(raw_dir or settings.RAW_DIR)
    work_dir = Path(work_dir or settings.WORK_DIR)

    if items:
        for it in items:
            lbl_path = getattr(it, "effective_label", None) or getattr(it, "label_path", None)
            rel_name = getattr(it, "key", str(getattr(it, "image_path", "")))
            if not lbl_path or not Path(lbl_path).is_file():
                report.append(dict(severity="CRITICAL", code="PAIR_MISSING_TXT",
                                   relative_path=rel_name, line=0, message="JPG 는 있는데 TXT 가 없음"))
                continue
            rows, errors = parse_label_file(Path(lbl_path))
            for sev, code, line, msg in validate_rows(rows, errors):
                report.append(dict(severity=sev, code=code, relative_path=rel_name, line=line, message=msg))
        return report

    if not raw_dir.is_dir():
        return report

    for ds_dir in sorted(p for p in raw_dir.iterdir() if p.is_dir()):
        img_root = ds_dir / "images"
        raw_lbl_root = ds_dir / "labels"
        work_lbl_root = work_dir / ds_dir.name / "labels"

        splits = set()
        for root in (img_root, raw_lbl_root):
            if root.is_dir():
                splits |= {p.name for p in root.iterdir() if p.is_dir()}

        for split in sorted(splits):
            img_split_dir = img_root / split
            raw_lbl_split_dir = raw_lbl_root / split
            work_lbl_split_dir = work_lbl_root / split

            images = {p.stem: p for p in img_split_dir.glob("*")
                      if p.is_file() and p.suffix.lower() in settings.IMAGE_EXTS} if img_split_dir.is_dir() else {}
            raw_labels = {p.stem: p for p in raw_lbl_split_dir.glob("*.txt")} if raw_lbl_split_dir.is_dir() else {}

            all_stems = sorted(set(images.keys()) | set(raw_labels.keys()))

            for stem in all_stems:
                rel_path = f"{ds_dir.name}/{split}/{stem}"
                has_img = stem in images
                
                work_lbl = work_lbl_split_dir / f"{stem}.txt" if work_lbl_split_dir.is_dir() else None
                lbl_path = work_lbl if (work_lbl and work_lbl.is_file()) else raw_labels.get(stem)

                if has_img and not lbl_path:
                    report.append(dict(severity="CRITICAL", code="PAIR_MISSING_TXT",
                                       relative_path=rel_path, line=0, message="JPG 는 있는데 TXT 가 없음"))
                    continue
                if not has_img and lbl_path:
                    report.append(dict(severity="CRITICAL", code="PAIR_MISSING_JPG",
                                       relative_path=rel_path, line=0, message="TXT 는 있는데 JPG 가 없음"))
                    continue

                rows, errors = parse_label_file(lbl_path)
                for sev, code, line, msg in validate_rows(rows, errors):
                    report.append(dict(severity=sev, code=code, relative_path=rel_path, line=line, message=msg))

    return report


def write_report(report, path):
    """검증 보고서를 CSV 파일로 저장한다."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=REPORT_FIELDS)
        writer.writeheader()
        writer.writerows(report)
