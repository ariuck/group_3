"""프로젝트 공통 설정 — 경로와 Class 기준.

  data/
  ├─ raw/     회사 제공 원본.  읽기만 한다.  ★ 절대 수정 금지 ★
  ├─ work/    작업본. RAW 와 같은 폴더 구조.  수정한 라벨(TXT)을 여기에 저장한다.
  └─ final/   검수가 모두 끝난 최종본 (QA 완료 후 정리)

Class 기준은 configs/classes.yaml 에서 읽는다. (회사 제공 Class ID 0~6 을 그대로 사용 — 번호를 바꾸지 않는다)
"""
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_DIR / "data" / "raw"                 # 회사 제공 원본 (읽기 전용)
WORK_DIR = PROJECT_DIR / "data" / "work"               # 작업본 (저장 위치)
FINAL_DIR = PROJECT_DIR / "data" / "final"             # 최종본
CONFIG_PATH = PROJECT_DIR / "configs" / "classes.yaml"  # Class 기준 파일

IMAGE_EXTS = {".jpg", ".jpeg"}
DEFAULT_COLOR = "#ff00ff"      # 설정에 색이 없거나 Class 범위 밖일 때

# classes.yaml 을 읽을 수 없을 때(PyYAML 미설치 등)만 쓰는 기본값. 내용은 classes.yaml 과 같아야 한다.
DEFAULT_CLASSES = [
    {"id": 0, "name": "나뭇잎·종이류",       "enabled": True,  "color": "#43a047"},
    {"id": 1, "name": "플라스틱류·돌·금속류", "enabled": True,  "color": "#e53935"},
    {"id": 2, "name": "나뭇가지류",          "enabled": True,  "color": "#1e88e5"},
    {"id": 3, "name": "벌레류",              "enabled": True,  "color": "#8e24aa"},
    {"id": 4, "name": "고무장갑",            "enabled": False, "color": "#757575"},
    {"id": 5, "name": "병해·갈변",           "enabled": True,  "color": "#fb8c00"},
    {"id": 6, "name": "파·고추",             "enabled": True,  "color": "#00897b"},
]


def load_classes(path=None):
    """configs/classes.yaml 을 읽어 [{id, name, enabled, color}, ...] 로 돌려준다.

    파일이 없거나 형식이 틀리면 기본값으로 대신하고 경고를 출력한다. (프로그램이 죽지 않게)
    ID 는 0, 1, 2, ... 순서로 빠짐없이 이어져야 한다. (재번호·결번 방지)
    """
    path = Path(path or CONFIG_PATH)
    try:
        import yaml                                   # PyYAML (requirements.txt)
        data = yaml.safe_load(path.read_text(encoding="utf-8"))["classes"]
        ids = sorted(int(k) for k in data)
        if ids != list(range(len(ids))):
            raise ValueError(f"Class ID 가 0부터 빠짐없이 이어져야 합니다: {ids}")
        return [{"id": i, "name": str(data[i]["name"]), "enabled": bool(data[i].get("enabled", True)),
                 "color": str(data[i].get("color", DEFAULT_COLOR))} for i in ids]
    except Exception as e:                            # noqa: BLE001 - 설정 오류는 경고 후 기본값으로 진행
        print(f"[경고] Class 설정을 읽지 못해 기본값을 사용합니다: {e}", file=sys.stderr)
        return [dict(c) for c in DEFAULT_CLASSES]


CLASSES = load_classes()
UNUSED_CLASSES = {c["id"] for c in CLASSES if not c["enabled"]}      # 사용 안 하는 Class (4번)


def class_name(cid, with_note=True):
    """Class 이름. 범위 밖이면 '?'.  사용 안 하는 Class 는 ' (사용 안 함)' 을 붙인다."""
    if not 0 <= cid < len(CLASSES):
        return "?"
    c = CLASSES[cid]
    return c["name"] + (" (사용 안 함)" if with_note and not c["enabled"] else "")


def class_color(cid):
    return CLASSES[cid]["color"] if 0 <= cid < len(CLASSES) else DEFAULT_COLOR
