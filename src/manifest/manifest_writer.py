"""검수표(Manifest) CSV 자동 기록 — [저장]할 때 객관적으로 알 수 있는 칸만 채운다.

파일: manifests/dataset_manifest.csv  (칸 19개, manifests/dataset_manifest.xlsx 검수표 틀과 같은 머리글)

자동으로 채우는 칸
    No · 이미지 파일명 · 라벨(TXT) 파일명 · 원본 BBox 수 · 최종 BBox 수 · Class ·
    TXT 줄 수 = 화면 BBox 수 · 상태(고쳤으면 '수정 완료') · 출처 데이터셋 · 원래 split

사람이 직접 채우는 칸 (프로그램은 건드리지 않고 비워 둔다 — 사람이 판단하는 내용이므로)
    이미지 유형 · 위치 맞음 · Class 맞음 · 누락 객체 여부 · 발견된 문제 · 작성자 · 검수자 · 검수일 · 비고

같은 사진을 다시 저장하면 새 줄을 만들지 않고 그 줄을 갱신한다.
(키 = 이미지 파일명 + 출처 데이터셋 + 원래 split,  '원본 BBox 수'는 처음 한 번만 기록하고 바꾸지 않는다)
"""
import csv
import os
import tempfile
from pathlib import Path

from src import settings
from src.data_paths import locate_in_raw
from src.yolo.yolo_loader import label_signature, read_yolo_rows

HEADERS = ["No", "이미지 파일명", "라벨(TXT) 파일명", "이미지 유형", "원본 BBox 수", "최종 BBox 수", "Class",
           "TXT 줄 수 = 화면 BBox 수", "위치 맞음", "Class 맞음", "누락 객체 여부", "상태", "발견된 문제",
           "작성자", "검수자", "검수일", "비고(수정 내용)", "출처 데이터셋", "원래 split"]

STATUS_BEFORE, STATUS_EDITED = "검수 전", "수정 완료"


class ManifestError(Exception):
    """검수표를 읽거나 쓰지 못했을 때. (TXT 저장과는 별개 — TXT 는 이미 저장된 뒤다)"""


def _count_lines(txt_path):
    """TXT 의 비어 있지 않은 줄 수 (읽을 수 없는 줄도 포함해서 '줄 수'를 센다)."""
    p = Path(txt_path)
    if not p.is_file():
        return 0
    return sum(1 for line in p.read_text(encoding="utf-8", errors="replace").splitlines() if line.strip())


def _load(path):
    """CSV 를 읽는다. 없으면 빈 목록. 머리글이 기준과 다르면 덮어쓰지 않도록 중단한다."""
    if not path.is_file():
        return []
    try:
        with open(path, encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            if reader.fieldnames != HEADERS:
                raise ManifestError(f"검수표 머리글이 기준 {len(HEADERS)}칸과 다릅니다. 열을 바꾸거나 지우지 않았는지 확인하세요.\n{path}")
            return list(reader)
    except UnicodeDecodeError:
        raise ManifestError("검수표를 읽을 수 없습니다. 엑셀에서 저장할 때 'CSV UTF-8' 형식으로 저장해 주세요.\n" + str(path))


def _save(path, rows):
    """임시 파일에 쓴 뒤 교체한다. 저장 도중 실패해도 기존 파일이 깨지지 않는다."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=HEADERS)
            w.writeheader()
            w.writerows(rows)
        os.replace(tmp, path)
    except OSError as e:
        if os.path.exists(tmp):
            os.remove(tmp)
        raise ManifestError(f"검수표를 저장하지 못했습니다. 엑셀 등에서 파일이 열려 있으면 닫고 다시 저장하세요.\n{e}")


def record_save(image_path, raw_txt, work_txt, screen_count, manifest_path=None):
    """[저장] 직후 호출 — 이 사진의 줄을 만들거나 갱신하고, 화면에 보여 줄 짧은 메시지를 돌려준다.

    image_path   : 이미지 경로          raw_txt : 원본 TXT 경로(없으면 None)
    work_txt     : 방금 저장한 WORK TXT   screen_count : 저장 당시 화면의 BBox 수
    """
    dataset, split = locate_in_raw(image_path)
    if dataset is None:
        return "RAW 밖의 이미지라 검수표에는 기록하지 않았습니다."

    path = Path(manifest_path or settings.MANIFEST_PATH)
    rows = _load(path)
    name = Path(image_path).name
    row = next((r for r in rows if r["이미지 파일명"] == name and r["출처 데이터셋"] == dataset
                and r["원래 split"] == split), None)

    raw_rows = read_yolo_rows(raw_txt) if raw_txt else []
    saved_rows = read_yolo_rows(work_txt)
    if row is None:                                                   # 처음 저장하는 사진 → 새 줄
        row = {h: "" for h in HEADERS}
        numbers = [int(r["No"]) for r in rows if str(r["No"]).isdigit()]
        row["No"] = str(max(numbers, default=0) + 1)
        rows.append(row)
    if row["원본 BBox 수"] == "":                                      # 원본 수는 처음 한 번만 기록
        row["원본 BBox 수"] = str(len(raw_rows))

    row["이미지 파일명"] = name
    row["라벨(TXT) 파일명"] = Path(work_txt).name
    row["출처 데이터셋"], row["원래 split"] = dataset, split
    row["최종 BBox 수"] = str(len(saved_rows))
    row["Class"] = ", ".join(str(c) for c in sorted({r[0] for r in saved_rows}))
    row["TXT 줄 수 = 화면 BBox 수"] = "O" if _count_lines(work_txt) == screen_count else "X"

    # 상태: 프로그램이 알 수 있는 것은 '원본과 달라졌는가' 뿐이다.
    #   달라졌다 → 아직 상태가 없거나 '검수 전'/'검수 완료'였으면 '수정 완료'로 바꾼다
    #   같다     → '수정 완료'였던 것(되돌린 경우)과 빈 상태는 '검수 전'으로 둔다
    #   사람이 정한 '수정 필요'(REVIEW 표시)와 '제외'는 어떤 경우에도 바꾸지 않는다.
    changed = label_signature(work_txt) != label_signature(raw_txt) if raw_txt else bool(saved_rows)
    if changed and row["상태"] in ("", STATUS_BEFORE, "검수 완료"):
        row["상태"] = STATUS_EDITED
    elif not changed and row["상태"] in ("", STATUS_EDITED):
        row["상태"] = STATUS_BEFORE

    _save(path, rows)
    return f"검수표 기록: No.{row['No']} · 상태 {row['상태']} · BBox {row['원본 BBox 수']}→{row['최종 BBox 수']}"
