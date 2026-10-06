"""검수표(Manifest) CSV 기록 — [저장]할 때 자동 칸을 채우고, 입력칸에서 받은 사람 칸을 함께 기록한다.

파일: manifests/dataset_manifest.csv  (칸 19개, manifests/dataset_manifest.xlsx 검수표 틀과 같은 머리글)

자동으로 채우는 칸
    No · 이미지 파일명 · 라벨(TXT) 파일명 · 원본 BBox 수 · 최종 BBox 수 · Class ·
    TXT 줄 수 = 화면 BBox 수 · 상태(고쳤으면 '수정 완료') · 출처 데이터셋 · 원래 split

사람이 직접 채우는 칸 (입력칸 화면 form_panel.py 에서 받은 값만 기록한다 — 사람이 판단하는 내용이므로)
    이미지 유형 · 위치 맞음 · Class 맞음 · 누락 객체 여부 · 발견된 문제 · 작성자 · 검수자 · 검수일 · 비고
    상태는 사람이 입력칸에서 직접 바꾼 경우에만 그 값을 쓰고, 아니면 프로그램이 자동으로 정한다.

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
STATUS_DONE, STATUS_REVIEW, STATUS_EXCLUDED = "검수 완료", "수정 필요", "제외"
STATUS_CHOICES = [STATUS_BEFORE, STATUS_EDITED, STATUS_DONE, STATUS_REVIEW, STATUS_EXCLUDED]

# 사람이 직접 채우는 칸. record_save(human=...) 로 받은 값 중 이 칸(과 상태)만 기록한다.
HUMAN_FIELDS = ["이미지 유형", "위치 맞음", "Class 맞음", "누락 객체 여부", "발견된 문제",
                "작성자", "검수자", "검수일", "비고(수정 내용)"]
FORM_FIELDS = ["상태"] + HUMAN_FIELDS


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


def _find_row(rows, name, dataset, split):
    """키(이미지 파일명 + 출처 데이터셋 + 원래 split)가 같은 줄을 찾는다. 없으면 None."""
    return next((r for r in rows if r["이미지 파일명"] == name and r["출처 데이터셋"] == dataset
                 and r["원래 split"] == split), None)


def _clean_human(human):
    """입력칸 값에서 상태와 사람 칸만 골라 낸다.

    - 자동 칸(No, 출처 데이터셋 등)은 들어 있어도 버린다.
    - 값이 None 인 칸은 '건드리지 않음'으로 보고 뺀다. 빈 글자("")는 '지움'이다.
    - 상태가 정해진 값이 아니면 기록하지 않고 중단한다.
    """
    cleaned = {}
    for key, value in (human or {}).items():
        if key in FORM_FIELDS and value is not None:
            cleaned[key] = str(value).strip()
    status = cleaned.get("상태", "")
    if status and status not in STATUS_CHOICES:
        raise ManifestError(f"상태는 {', '.join(STATUS_CHOICES)} 중 하나여야 합니다: {status}")
    return cleaned


def read_human(image_path, manifest_path=None):
    """이미지를 열 때 호출 — 이 사진의 상태와 사람 칸을 돌려준다(입력칸에 다시 보여 주는 용도).

    검수표에 아직 줄이 없거나 RAW 밖의 이미지면 모두 빈칸이다.
    """
    blank = {h: "" for h in FORM_FIELDS}
    dataset, split = locate_in_raw(image_path)
    if dataset is None:
        return blank
    rows = _load(Path(manifest_path or settings.MANIFEST_PATH))
    row = _find_row(rows, Path(image_path).name, dataset, split)
    if row is None:
        return blank
    return {h: (row[h] or "") for h in FORM_FIELDS}


def record_save(image_path, raw_txt, work_txt, screen_count, manifest_path=None, human=None):
    """[저장] 직후 호출 — 이 사진의 줄을 만들거나 갱신하고, 화면에 보여 줄 짧은 메시지를 돌려준다.

    image_path   : 이미지 경로          raw_txt : 원본 TXT 경로(없으면 None)
    work_txt     : 방금 저장한 WORK TXT   screen_count : 저장 당시 화면의 BBox 수
    human        : 입력칸 값 {머리글: 값} (form_panel 의 get_values()). None 이면 사람 칸은 그대로 둔다.
    """
    dataset, split = locate_in_raw(image_path)
    if dataset is None:
        return "RAW 밖의 이미지라 검수표에는 기록하지 않았습니다."

    human = _clean_human(human)                                       # 잘못된 상태면 여기서 중단(파일은 그대로)
    path = Path(manifest_path or settings.MANIFEST_PATH)
    rows = _load(path)
    name = Path(image_path).name
    row = _find_row(rows, name, dataset, split)

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

    # 사람 칸: 입력칸에서 받은 값을 그대로 적는다. (받지 않은 칸은 건드리지 않는다)
    chosen = human.pop("상태", "")
    for key, value in human.items():
        row[key] = value

    # 상태
    #   사람이 입력칸에서 상태를 '이번에 직접 바꿨으면'(저장돼 있던 값과 다르면) 그 값을 쓴다.
    #   바꾸지 않았으면 프로그램이 정한다. 프로그램이 알 수 있는 것은 '원본과 달라졌는가' 뿐이다.
    #     달라졌다 → 아직 상태가 없거나 '검수 전'/'검수 완료'였으면 '수정 완료'로 바꾼다
    #     같다     → '수정 완료'였던 것(되돌린 경우)과 빈 상태는 '검수 전'으로 둔다
    #     사람이 정한 '수정 필요'(REVIEW 표시)와 '제외'는 프로그램이 바꾸지 않는다.
    changed = label_signature(work_txt) != label_signature(raw_txt) if raw_txt else bool(saved_rows)
    if chosen and chosen != (row["상태"] or STATUS_BEFORE):
        row["상태"] = chosen
    elif changed and row["상태"] in ("", STATUS_BEFORE, STATUS_DONE):
        row["상태"] = STATUS_EDITED
    elif not changed and row["상태"] in ("", STATUS_EDITED):
        row["상태"] = STATUS_BEFORE

    _save(path, rows)
    return f"검수표 기록: No.{row['No']} · 상태 {row['상태']} · BBox {row['원본 BBox 수']}→{row['최종 BBox 수']}"
