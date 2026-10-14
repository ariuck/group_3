"""
Project-wide constants and configurations for Subject 8 (Kimchi Foreign Object Detection).
Single Source of Truth (SSOT) for classes, capture groups, split rules, and deliverable schemas.
"""
from typing import Dict

# 7 Classes definition (교과 7/8 공통 확정 기준)
CLASS_NAMES: Dict[int, str] = {
    0: 'leaf_paper',
    1: 'plastic_stone_metal',
    2: 'branch',
    3: 'insect',
    4: 'rubber_glove_unused',
    5: 'disease_browning',
    6: 'green_onion_pepper'
}

# Plan B 세션 묶음 배정 맵 (17개 묶음 기본 역할)
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

# G00 시간순 블록 분할 기준 수량 (총 50장)
G00_SPLIT_COUNTS: Dict[str, int] = {
    "train": 26,
    "val": 8,
    "test": 8,
    "bridge_holdout": 8,
}

# 가이드 산출물 1 표준 요약표 목적 정의
ROLE_PURPOSES: Dict[str, str] = {
    "train": "model_training",
    "val": "model_validation",
    "test": "final_evaluation",
    "bridge_holdout": "subject14_bridge"
}

# 데이터셋 기본 버전
DEFAULT_DATASET_VERSION = "kimchi_v1"

# 촬영 묶음 분리 시간 임계값 (초 단위: 300초 = 5분)
CAPTURE_GROUP_INTERVAL_SECONDS = 300
