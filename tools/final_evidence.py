"""최종본(data/final)의 증빙 자료를 글로 만든다. (reports/final_evidence.md)

    python tools/final_evidence.py              # 화면에 미리보기
    python tools/final_evidence.py --apply      # reports/final_evidence.md 로 저장

들어가는 것: 폴더 구조, 이미지·TXT 수량, 짝 일치, 최종본 자체의 Validation 결과, Class 분포, 대표 YOLO TXT 예시 3개
사진 파일명은 넣지 않는다. (실제 파일명은 회사 데이터라 공개 문서에 두지 않는다)
화면 캡처(폴더 구조·수량·대표 이미지)는 사람이 찍어서 따로 보관한다 — 이 문서는 그 캡처가 가리키는 숫자의 근거다.
"""
import argparse
import sys
import time
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src import settings                                    # noqa: E402
from src.validation import validator                        # noqa: E402

REPORT_PATH = settings.PROJECT_DIR / "reports" / "final_evidence.md"


def inspect(final_dir=None):
    """flat 구조(images/, labels/)의 최종본을 읽어 증빙 숫자를 모은다."""
    final_dir = Path(final_dir or settings.FINAL_DIR)
    images = sorted(p for p in (final_dir / "images").glob("*") if p.suffix.lower() in settings.IMAGE_EXTS)
    labels = sorted((final_dir / "labels").glob("*.txt"))
    istem, lstem = {p.stem for p in images}, {p.stem for p in labels}
    classes, issues, boxes_per_file, empty = Counter(), Counter(), [], 0
    for p in labels:
        rows, errors = validator.parse_label_file(p)
        empty += not rows
        boxes_per_file.append(len(rows))
        classes.update(r[0] for r in rows)
        for sev, code, _line, _msg in validator.validate_rows(rows, errors):
            issues[(sev, code)] += 1
    samples = []
    for p in labels:                                          # 박스 수가 다른 예시를 골라 3개
        n = len(p.read_text(encoding="utf-8-sig").splitlines())
        if n not in {len(s.splitlines()) for s in samples}:
            samples.append(p.read_text(encoding="utf-8-sig").strip())
        if len(samples) == 3:
            break
    return {"images": len(images), "labels": len(labels), "pairs": len(istem & lstem), "only_image": len(istem - lstem),
            "only_label": len(lstem - istem), "empty": empty, "classes": classes, "issues": issues, "boxes": sum(boxes_per_file),
            "samples": samples, "has_classes_txt": (final_dir / "classes.txt").is_file(), "has_manifest": (final_dir / "검수표.csv").is_file()}


def build_markdown(info, today=None):
    L = ["# FINAL 데이터 증빙", "",
         f"> `data/final/` 을 읽어 `tools/final_evidence.py` 로 만든 숫자 근거입니다. ({today or time.strftime('%Y-%m-%d')} 기준)",
         "> 사진 파일명은 넣지 않았습니다. 화면 캡처(폴더 구조 · 이미지 수량 · TXT 수량 · 대표 이미지 3~5장)는 사람이 찍어 따로 보관합니다.", "",
         "## 1. 폴더 구조", "", "```text", "data/final/",
         f"├── images/        {info['images']}장 (.jpg)",
         f"├── labels/        {info['labels']}개 (.txt)",
         f"├── classes.txt    {'있음' if info['has_classes_txt'] else '없음'}",
         f"└── 검수표.csv      {'있음' if info['has_manifest'] else '없음'}", "```", "",
         "## 2. 수량과 짝", "", "| 항목 | 수량 |", "|---|---:|",
         f"| FINAL 이미지 | {info['images']} |", f"| FINAL YOLO TXT | {info['labels']} |",
         f"| 이미지 ↔ TXT 짝 | {info['pairs']} |", f"| 짝이 없는 이미지 | {info['only_image']} |", f"| 짝이 없는 TXT | {info['only_label']} |",
         f"| 빈 TXT | {info['empty']} |", f"| BBox 합계 | {info['boxes']} |", "",
         "## 3. 최종본 자체 검사 (Validation)", ""]
    if info["issues"]:
        L += ["| 종류 | 수량 |", "|---|---:|"] + [f"| {s} · {c} | {n} |" for (s, c), n in sorted(info["issues"].items())]
    else:
        L.append("라벨 형식·Class 범위·좌표 범위·BBox 경계·중복 검사에서 오류와 경고가 **0건**입니다.")
    L += ["", "## 4. Class 별 BBox 수", "", "| Class | 이름 | BBox |", "|---:|---|---:|"]
    L += [f"| {c['id']} | {settings.class_name(c['id'])} | {info['classes'][c['id']]} |" for c in settings.CLASSES]
    L += ["", "## 5. 대표 YOLO TXT 예시", "", "한 줄이 BBox 하나입니다: `class_id x_center y_center width height` (0~1 비율값)", ""]
    for i, s in enumerate(info["samples"], 1):
        L += [f"예시 {i} (BBox {len(s.splitlines())}개):", "", "```text", s, "```", ""]
    L += ["## 6. 사람이 하는 것", "", "- 폴더 구조 · 이미지 수량 · TXT 수량 캡처, 대표 검수 완료 이미지 3~5장 캡처: 【기입】",
          "- 캡처에는 실제 사진이 나오므로 외부에 공유하지 않는 곳에만 보관합니다. (NDA)", ""]
    return "\n".join(L)


def main(argv=None):
    ap = argparse.ArgumentParser(description="최종본의 증빙 숫자를 reports/final_evidence.md 로 만든다")
    ap.add_argument("--apply", action="store_true", help="reports/final_evidence.md 로 저장한다 (없으면 화면에만 출력)")
    args = ap.parse_args(argv)
    md = build_markdown(inspect())
    if args.apply:
        REPORT_PATH.write_text(md, encoding="utf-8")
        print(f"저장했습니다: {REPORT_PATH}")
    else:
        print(md)
    return 0


if __name__ == "__main__":
    sys.exit(main())
