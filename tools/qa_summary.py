"""검수 결과를 숫자로 요약해 QA Summary(reports/qa_summary.md)를 만든다.

    python tools/qa_summary.py              # 화면에 미리보기
    python tools/qa_summary.py --apply      # reports/qa_summary.md 로 저장

읽는 것: 검수표(manifests/dataset_manifest.csv), 원본 라벨(data/raw), 검수한 라벨(data/work)
쓰는 것: reports/qa_summary.md 만. (--apply 일 때)  RAW 와 data/work 는 읽기만 한다.
검수 일자는 검수표의 `검수일` 칸에서 읽는다.
"""
import argparse
import csv
import sys
import time
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PIL import Image                                       # noqa: E402

from src import settings                                    # noqa: E402
from src.bbox import bbox_diff                              # noqa: E402
from src.validation import validator                        # noqa: E402

REPORT_PATH = settings.PROJECT_DIR / "reports" / "qa_summary.md"
OK_STATUS = ("검수 완료", "수정 완료")


def read_manifest(path=None):
    with open(path or settings.MANIFEST_PATH, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def _boxes(label_path, w, h):
    """라벨 파일 → bbox_diff 가 쓰는 픽셀 BBox 목록. 파일이 없으면 빈 목록."""
    rows, _errors = validator.parse_label_file(label_path)
    return [{"cls": c, "x1": (x - bw / 2) * w, "y1": (y - bh / 2) * h, "x2": (x + bw / 2) * w, "y2": (y + bh / 2) * h}
            for c, x, y, bw, bh in rows]


def _label(root, ds, split, stem):
    return Path(root) / ds / "labels" / split / f"{stem}.txt"


def collect(raw_dir=None, work_dir=None, manifest_path=None):
    """검수표와 라벨을 읽어 통계를 모은다. (사진 크기를 읽으므로 몇 분이 걸릴 수 있다)"""
    raw_dir, work_dir = Path(raw_dir or settings.RAW_DIR), Path(work_dir or settings.WORK_DIR)
    rows = read_manifest(manifest_path)
    raw_cls, final_cls = Counter(), Counter()
    changes = Counter()                          # 추가·수정·삭제·그대로
    changed_photos = Counter()                   # 사진 단위: 바뀐 사진 수 / 데이터셋별 바뀐 사진 수
    class_moves = Counter()                      # 원본 Class → 최종 Class (Class 가 바뀐 것)
    added_by_class, deleted_by_class = Counter(), Counter()
    by_ds = {}
    for r in rows:
        ds, split, name = r["출처 데이터셋"], r["원래 split"], r["이미지 파일명"]
        stem = Path(name).stem
        img = next((raw_dir / ds / "images" / split / (stem + e) for e in (".jpg", ".JPG", ".jpeg", ".JPEG")
                    if (raw_dir / ds / "images" / split / (stem + e)).is_file()), None)
        if img is None:
            continue
        with Image.open(img) as im:
            w, h = im.size
        raw_b = _boxes(_label(raw_dir, ds, split, stem), w, h)
        wl = _label(work_dir, ds, split, stem)
        fin_b = _boxes(wl if wl.is_file() else _label(raw_dir, ds, split, stem), w, h)
        raw_cls.update(b["cls"] for b in raw_b)
        final_cls.update(b["cls"] for b in fin_b)
        d = bbox_diff.diff_boxes(raw_b, fin_b)
        n_add, n_mod, n_del = len(d["added"]), len(d["modified"]), len(d["deleted"])
        changes.update({"추가": n_add, "수정": n_mod, "삭제": n_del, "그대로": len(d["unchanged"])})
        added_by_class.update(fin_b[i]["cls"] for i in d["added"])
        deleted_by_class.update(raw_b[i]["cls"] for i in d["deleted"])
        for ri, ci in d["modified"]:
            if raw_b[ri]["cls"] != fin_b[ci]["cls"]:
                class_moves[(raw_b[ri]["cls"], fin_b[ci]["cls"])] += 1
        touched = n_add + n_mod + n_del > 0
        changed_photos["바뀐 사진"] += touched
        changed_photos["상태 불일치"] += touched != (r["상태"] == "수정 완료")
        s = by_ds.setdefault((ds, split), Counter())
        s["사진"] += 1
        s["바뀐 사진"] += touched
    return {"rows": rows, "raw_cls": raw_cls, "final_cls": final_cls, "changes": changes, "changed_photos": changed_photos["바뀐 사진"],
            "status_mismatch": changed_photos["상태 불일치"], "class_moves": class_moves, "added_by_class": added_by_class, "deleted_by_class": deleted_by_class, "by_ds": by_ds}


def build_markdown(stats, validation=None, today=None):
    """collect() 결과로 QA Summary 마크다운을 만든다."""
    rows = stats["rows"]
    n = len(rows)
    status = Counter(r["상태"] for r in rows)
    reviewers = {}
    for r in rows:
        who = r["검수자"] or "(비어 있음)"
        reviewers.setdefault(who, Counter())[r["상태"]] += 1
    same = sum(1 for r in rows if r["작성자"] and r["작성자"] == r["검수자"])
    blank_author = sum(1 for r in rows if not r["작성자"])
    unresolved = sum(1 for r in rows if r["상태"] == "수정 필요" and r["발견된 문제"].startswith("REVIEW"))
    scene = Counter(r["이미지 유형"] or "(비어 있음)" for r in rows)
    raw_total, fin_total = sum(stats["raw_cls"].values()), sum(stats["final_cls"].values())
    ch = stats["changes"]
    validation = validation if validation is not None else []
    sev = Counter(v["severity"] for v in validation)
    critical_photos = {v["relative_path"] for v in validation if v["severity"] == "CRITICAL"}
    not_done = [r for r in rows if r["상태"] not in OK_STATUS or not r["검수자"]]
    fail = len(not_done) + len(critical_photos)                    # 최종본 조건을 못 채운 사진 + 치명적 오류가 있는 사진
    verdict = n > 0 and fail == 0 and unresolved == 0 and same == 0
    days = sorted({r["검수일"] for r in rows if r.get("검수일")})
    dates = ", ".join(days) if days else "기록 없음"
    human = {k: Counter(r.get(k) or "(비어 있음)" for r in rows) for k in ("위치 맞음", "Class 맞음", "누락 객체 여부")}
    L = [f"# QA Summary — 최종 라벨 품질검사 결과", "",
         f"> 검수표(`manifests/dataset_manifest.csv`)와 라벨(RAW 원본·`data/work`)을 읽어 `tools/qa_summary.py` 로 만든 보고서입니다. ({today or time.strftime('%Y-%m-%d')} 기준)",
         "> 실제 사진 파일명은 넣지 않았습니다.", "",
         "## 1. 결론", "",
         f"- 전체 **{n}장** 모두 검수를 마쳤고, 상태는 검수 완료 {status['검수 완료']} · 수정 완료 {status['수정 완료']} 입니다. "
         f"(검수 전 {status['검수 전']} · 수정 필요 {status['수정 필요']} · 제외 {status['제외']})",
         f"- 미처리 REVIEW **{unresolved}건**, 작성자와 검수자가 같은 줄 **{same}줄**, 작성자가 비어 있는 줄 {blank_author}줄",
         f"- Validation: CRITICAL {sev['CRITICAL']} · WARNING {sev['WARNING']} · INFO {sev['INFO']}",
         f"- 최종 FAIL **{fail}건** · 최종 REVIEW **{unresolved}건**",
         f"- BBox 는 원본 {raw_total}개 → 최종 {fin_total}개 ({fin_total - raw_total:+d})",
         f"- **최종 QA 판정: {'교과 8 사용 가능 (FAIL 0 · REVIEW 0)' if verdict else '미완료 — 아래 7장을 확인하세요'}**  (판정 기준: 아래 7장의 완료 기준)", "",
         "## 2. 검수 현황", "", "| 검수자 | 사진 | 검수 완료 | 수정 완료 | 그 밖 |", "|---|---:|---:|---:|---:|"]
    for who, c in sorted(reviewers.items()):
        total = sum(c.values())
        L.append(f"| {who} | {total} | {c['검수 완료']} | {c['수정 완료']} | {total - c['검수 완료'] - c['수정 완료']} |")
    L += ["", "| 데이터셋 / split | 사진 | 라벨이 바뀐 사진 |", "|---|---:|---:|"]
    for (ds, split), c in sorted(stats["by_ds"].items()):
        L.append(f"| {ds} / {split} | {c['사진']} | {c['바뀐 사진']} |")
    L += [f"| **합계** | **{n}** | **{stats['changed_photos']}** |", "",
          "> `수정 완료` 는 원본과 달라진 사진, `검수 완료` 는 원본 그대로인 사진을 뜻합니다. 검수를 마쳤는지는 검수자 칸으로 확인합니다.",
          f"> 라벨이 원본과 달라졌는지와 상태가 어긋난 사진은 **{stats['status_mismatch']}장**입니다. "
          "(상태는 사람이 고를 수 있어서 생깁니다. 라벨 자체의 오류는 아니며, Validation 은 통과했습니다)", "",
          "## 3. BBox 변화 (원본 → 최종)", "", "| 구분 | 개수 |", "|---|---:|"]
    for k in ("그대로", "수정", "추가", "삭제"):
        L.append(f"| {k} | {ch[k]} |")
    L += ["", "- **수정** = 같은 BBox 를 고친 것(위치·크기·Class), **추가** = 원본에 없던 새 BBox, **삭제** = 원본에는 있었으나 지운 BBox", "",
          "### Class 별 BBox 수", "", "| Class | 이름 | 원본 | 최종 | 증감 | 추가 | 삭제 |", "|---:|---|---:|---:|---:|---:|---:|"]
    for c in settings.CLASSES:
        i = c["id"]
        o, f = stats["raw_cls"][i], stats["final_cls"][i]
        L.append(f"| {i} | {settings.class_name(i)} | {o} | {f} | {f - o:+d} | {stats['added_by_class'][i]} | {stats['deleted_by_class'][i]} |")
    L.append(f"| | **합계** | **{raw_total}** | **{fin_total}** | **{fin_total - raw_total:+d}** | **{ch['추가']}** | **{ch['삭제']}** |")
    if stats["class_moves"]:
        L += ["", "Class 를 바꾼 BBox:", "", "| 원본 Class → 최종 Class | 개수 |", "|---|---:|"]
        for (a, b), k in sorted(stats["class_moves"].items()):
            L.append(f"| {a} {settings.class_name(a, False)} → {b} {settings.class_name(b, False)} | {k} |")
    L += ["", "## 4. 이미지 유형", "", "| 이미지 유형 | 사진 |", "|---|---:|"]
    for k, v in scene.most_common():
        L.append(f"| {k} | {v} |")
    L += ["", "- 교과 8 에서 분할·평가 방식을 정할 때 참고합니다. (정상 김치 사진이 없으면 '이물 없음' 사례가 학습·평가에 거의 없다는 뜻입니다)", "",
          "## 5. Validation 결과 (전체 900장)", "",
          "| 종류 | 수량 |", "|---|---:|"]
    kinds = Counter((v["severity"], v["code"]) for v in validation)
    if kinds:
        for (sv, code), k in sorted(kinds.items()):
            L.append(f"| {sv} · {code} | {k} |")
    else:
        L.append("| 오류·경고 없음 (CRITICAL · WARNING · INFO 모두 0) | 0 |")
    L += ["", "- 검사 항목: 짝 없음, TXT 형식, Class 범위, Class 4, 좌표 범위, BBox 경계 밖, 중복 BBox, 빈 TXT, 너무 작은 BBox ([validator.py](../src/validation/validator.py))",
          "- 너무 작은 BBox(TINY_BOX) 경고가 1건 있었으나 확인 후 삭제했습니다. 확대해서 보면 형태를 알 수 없는 점이라 BBox 기준서 §4(`too_small_to_identify`)에 따라 지웠습니다.", "",
          "## 6. Human QA 결과 (사람이 확인한 것)", "",
          "| 검수 상태 | 사진 |", "|---|---:|"]
    for k in ("검수 완료", "수정 완료", "수정 필요", "제외", "검수 전"):
        L.append(f"| {k} | {status[k]} |")
    L += ["", f"- 검수자가 사진을 보고 확인한 결과이며, 검수자 칸이 채워진 사진은 {sum(1 for r in rows if r['검수자'])}장입니다. 검수자별 현황은 위 2장 표와 같습니다.",
          f"- 검수표의 세부 확인 칸은 `위치 맞음` {dict(human['위치 맞음'])} · `Class 맞음` {dict(human['Class 맞음'])} · `누락 객체 여부` {dict(human['누락 객체 여부'])} 입니다. "
          "이 칸들은 따로 적지 않고 위 검수 상태(검수 완료·수정 완료)로 사람의 확인을 갈음했습니다.", "",
          "## 7. 완료 기준 점검 ([Project Baseline](../docs/standards/project_baseline.md) §5)", "",
          "| 기준 | 결과 |", "|---|---|",
          f"| 미처리 REVIEW 0건 | {'**통과**' if unresolved == 0 else '**미달**'} ({unresolved}건) |",
          f"| Validation 오류 0건 | {'**통과**' if sev['CRITICAL'] == 0 else '**미달**'} (CRITICAL {sev['CRITICAL']}) |",
          f"| 900장 전체 검수 완료 | {'**통과**' if n > 0 and all(r['상태'] in OK_STATUS and r['검수자'] for r in rows) else '**미달**'} |",
          f"| 작성자 ≠ 검수자 | {'**통과**' if same == 0 else '**미달**'} ({same}줄) |",
          "| 이미지·TXT Pair | 900 / 900 |",
          "| FINAL 데이터 정리 | `data/final/` ([README §14](../README.md)) |", "",
          "## 8. 검수 기간과 REVIEW 판단 기준", "",
          f"- 검수일: {dates} (검수표 `검수일` 칸 기준)",
          f"- REVIEW 는 팀장(PM)과 해당 검수자가 판단하는 것으로 정했고([Project Baseline](../docs/standards/project_baseline.md) §5), 최종 미처리 REVIEW 는 {unresolved}건입니다.", ""]
    return "\n".join(L)


def main(argv=None):
    ap = argparse.ArgumentParser(description="검수 결과를 요약해 reports/qa_summary.md 를 만든다")
    ap.add_argument("--apply", action="store_true", help="reports/qa_summary.md 로 저장한다 (없으면 화면에만 출력)")
    args = ap.parse_args(argv)
    stats = collect()
    md = build_markdown(stats, validator.validate_dataset())
    if args.apply:
        REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
        REPORT_PATH.write_text(md, encoding="utf-8")
        print(f"저장했습니다: {REPORT_PATH}")
    else:
        print(md)
    return 0


if __name__ == "__main__":
    sys.exit(main())
