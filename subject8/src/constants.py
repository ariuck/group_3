"""
Project-wide constants and configurations for Subject 8 (Kimchi Foreign Object Detection).
Single Source of Truth (SSOT) for classes, scene types, capture groups, split rules, and deliverable schemas.
"""
from typing import Dict, List, Tuple

# 7 Classes definition (교과 7/8 공통 확정 기준) — Class 4 는 미사용이지만 번호 유지
CLASS_NAMES: Dict[int, str] = {
    0: 'leaf_paper',
    1: 'plastic_stone_metal',
    2: 'branch',
    3: 'insect',
    4: 'rubber_glove_unused',
    5: 'disease_browning',
    6: 'green_onion_pepper'
}

# 교과 7 검수표 `이미지 유형` 값 → 교과 8 scene_type 이름
SCENE_TYPES: Dict[str, str] = {
    '김치+대상 객체': 'kimchi_with_target',
    '정상 김치': 'normal_kimchi',
    '대상 객체 단독': 'object_only',
    '판단 어려움': 'other_review',
}
NORMAL_SCENE = '정상 김치'

# 교과 7 결과물 위치 (subject8/ 기준). 라벨·검수표·classes.txt 는 subject7/data/final (Git),
# 사진은 subject7/data/raw (각 PC 에 회사 원본 그대로) — subject7/tools/restore_from_final.py 참고
SUBJECT7_FINAL_DIR = "../subject7/data/final"
SUBJECT7_RAW_DIR = "../subject7/data/raw"

# 촬영 묶음 분리 시간 임계값 (초 단위: 300초 = 5분)
CAPTURE_GROUP_INTERVAL_SECONDS = 300

# 현재 공식 Dataset Version (03_build_split.py 기본값)
DEFAULT_DATASET_VERSION = "kimchi_v4"
DATASET_VERSIONS: List[str] = ["kimchi_v1", "kimchi_v2", "kimchi_v3", "kimchi_v4", "kimchi_v5"]
# 기존 공용 폴더(data/yolo, manifests/, configs/dataset.yaml) 대신 따로 만드는 Version → 폴더 이름 끝
# kimchi_v5: data/yolo_v5 · data/bridge_holdout_v5 · manifests/kimchi_v5/ · configs/dataset_v5.yaml (v4 폴더는 그대로)
SEPARATE_DIR_VERSIONS: Dict[str, str] = {"kimchi_v5": "v5"}

# 방안 B 묶음 통째 배정 맵 (kimchi_v1 기준). 블록 분할 묶음(BLOCK_RULES)은 여기 값을 쓰지 않는다
GROUP_ROLE_MAP: Dict[str, str] = {
    "G01": "val",
    "G02": "train",
    "G03": "train",
    "G04": "train",
    "G05": "train",
    "G06": "train",
    "G07": "test",
    "G08": "train",
    "G09": "train",
    "G10": "bridge_holdout",
    "G11": "train",
    "G12": "val",
    "G13": "bridge_holdout",
    "G14": "test",
    "G15": "bridge_holdout",
    "G16": "train",
    "G17": "train",  # 이물 단독 150장 전량 Train
}

# Version 별로 GROUP_ROLE_MAP 에서 바뀌는 묶음
# kimchi_v2~: Val 이 G12 한 회차에 몰리지 않게 G05 를 통째로 Val 로 (대부분 플라스틱 — Train 에 가장 넉넉한 Class)
GROUP_ROLE_OVERRIDES: Dict[str, Dict[str, str]] = {
    "kimchi_v1": {},
    "kimchi_v2": {"G05": "val"},
    "kimchi_v3": {"G05": "val"},
    "kimchi_v4": {"G05": "val"},
    # kimchi_v5 (C안, docs/project/kimchi_v5_split.md): 묶음 통째 배정, 예외는 G00 하나
    "kimchi_v5": {"G01": "train", "G05": "val", "G11": "bridge_holdout", "G12": "bridge_holdout",
                  "G13": "val", "G15": "train"},
}

# 묶음 안을 시간순 연속 블록으로 나누는 예외 규칙: {묶음: [(시작, 끝(미포함), 역할), ...]}
# 시간순(파일명 순) index 기준. 여기 없는 묶음은 GROUP_ROLE_MAP 대로 통째로 배정한다.
Block = Tuple[int, int, str]
BLOCK_RULES: Dict[str, Dict[str, List[Block]]] = {
    "kimchi_v1": {
        "G00": [(0, 26, "train"), (26, 34, "val"), (34, 42, "test"), (42, 50, "bridge_holdout")],
    },
    "kimchi_v2": {
        # 파 구간(0~24)과 파+고추 구간(25~49)을 각각 13/4/4/4 로 — v1 은 고추가 Train 에 3개뿐이었다 (H2)
        "G00": [(0, 13, "train"), (13, 17, "val"), (17, 21, "test"), (21, 25, "bridge_holdout"),
                (25, 38, "train"), (38, 42, "val"), (42, 46, "test"), (46, 50, "bridge_holdout")],
        # 잎 1장(0~24) · 잎 5장(25~49) · 잎 2~3장(50~74) 세 배치 중 가운데를 Train
        # — v1 은 마른 잎·작은 반점 갈변이 Train 에 거의 없었다 (H1). 24|25 사이는 촬영 간격 165초
        "G12": [(0, 25, "val"), (25, 50, "train"), (50, 75, "val")],
    },
}
# kimchi_v3: 분할은 v2 와 같고 라벨만 다르다 (Class 5 기준 개정 — docs/project/standards/class_guide.md)
BLOCK_RULES["kimchi_v3"] = BLOCK_RULES["kimchi_v2"]
# kimchi_v4: v3 라벨 + G09 마지막 배치(50~74, 갈변 67개·다른 이물 섞인 장면)를 Val 로
# — v3 는 갈변 256개 중 207개가 G09(전부 Train) 라 Val 갈변이 8개뿐이었다. 24|25 사이 262초, 49|50 은 배치 변경(플라스틱 4 → 43)
BLOCK_RULES["kimchi_v4"] = {**BLOCK_RULES["kimchi_v2"], "G09": [(0, 50, "train"), (50, 75, "val")]}
# kimchi_v5: G00 만 블록 — 파(0~24)·파+고추(25~49) 구간마다 평가 역할에 3장씩. Val 파 블록은 2|3 사이 182초 끊김에서 자른다
BLOCK_RULES["kimchi_v5"] = {
    "G00": [(0, 3, "val"), (3, 19, "train"), (19, 22, "test"), (22, 25, "bridge_holdout"),
            (25, 41, "train"), (41, 44, "val"), (44, 47, "test"), (47, 50, "bridge_holdout")],
}

# 교과 7 최종본 라벨 대신 쓸 수정본 폴더 (프로젝트 루트 기준). 같은 이름 TXT 가 있으면 그것을 쓴다
# kimchi_v5: v3 수정본 + 이물 없는 박스 3개 삭제 (G12 #508·#520·#541 — reports/01_data/label_fixes_kimchi_v5/)
LABEL_FIX_DIRS: Dict[str, str] = {"kimchi_v3": "data/label_fixes/kimchi_v3", "kimchi_v4": "data/label_fixes/kimchi_v3",
                                  "kimchi_v5": "data/label_fixes/kimchi_v5"}

# 역할 순서와 가이드 산출물 1 표준 요약표 목적 정의
ROLES: List[str] = ["train", "val", "test", "bridge_holdout"]
ROLE_PURPOSES: Dict[str, str] = {
    "train": "model_training",
    "val": "model_validation",
    "test": "final_evaluation",
    "bridge_holdout": "subject14_bridge"
}


def group_role_map(dataset_version: str) -> Dict[str, str]:
    """Version 의 묶음 통째 배정 맵 = GROUP_ROLE_MAP + GROUP_ROLE_OVERRIDES"""
    return {**GROUP_ROLE_MAP, **GROUP_ROLE_OVERRIDES[dataset_version]}
