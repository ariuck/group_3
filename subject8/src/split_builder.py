"""
Dataset split builder for Subject 8 (Kimchi Foreign Object Detection).
Implements Plan B: 18 capture groups session-based split + per-version chronological block exceptions
(BLOCK_RULES in src/constants.py) and per-version label fixes.
"""
import re
import shutil
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
import pandas as pd

from src.constants import (
    BLOCK_RULES,
    CAPTURE_GROUP_INTERVAL_SECONDS,
    CLASS_NAMES,
    DEFAULT_DATASET_VERSION,
    LABEL_FIX_DIRS,
    ROLE_PURPOSES,
    ROLES,
    group_role_map,
)


class SplitBuilder:
    """데이터셋 분할, 매니페스트 생성 및 물리 디렉토리 배치를 담당하는 빌더 클래스"""

    def __init__(self, project_root: Path):
        self.project_root = Path(project_root)
        self.data_final_dir = self.project_root / "data" / "subject7_final"
        self.meta_csv = self.data_final_dir / "검수표.csv"
        self.images_dir = self.data_final_dir / "images"
        self.labels_dir = self.data_final_dir / "labels"

        self.manifest_dir = self.project_root / "manifests"
        self.yolo_dir = self.project_root / "data" / "yolo"
        self.bridge_dir = self.project_root / "data" / "bridge_holdout"
        self.configs_dir = self.project_root / "configs"
        self.reports_dir = self.project_root / "reports"

    @staticmethod
    def _build_file_index(base_dir: Path, pattern: str = "*") -> Dict[str, Path]:
        """
        디렉토리를 1회 스캔하여 파일명 -> 경로 매핑 인덱스를 생성합니다.
        (하위 폴더 images/train·validation 포함) 반복 탐색 비용을 O(1) 조회로 줄입니다.
        """
        index: Dict[str, Path] = {}
        if not base_dir.exists():
            return index
        for p in base_dir.rglob(pattern):
            if p.is_file() and p.name not in index:
                index[p.name] = p
        return index

    def assign_capture_groups(self, df: pd.DataFrame) -> pd.DataFrame:
        """파일명 타임스탬프 기준 CAPTURE_GROUP_INTERVAL_SECONDS(5분) 초과 간격으로 G00~G17 18개 묶음 부여"""
        records: List[Tuple[Any, str, datetime]] = []
        for idx, row in df.iterrows():
            fname = str(row["이미지 파일명"])
            m = re.match(r"^(\d{2})(\d{2})(\d{2})_(\d{2})(\d{2})(\d{2})", fname)
            if m:
                yy, mm, dd, hh, mi, ss = map(int, m.groups())
                dt = datetime(2000 + yy, mm, dd, hh, mi, ss)
            else:
                dt = datetime.min
            records.append((idx, fname, dt))

        # 시간순 정렬
        records.sort(key=lambda x: x[2])

        gid_map: Dict[Any, str] = {}
        curr_gid = 0
        prev_dt: Optional[datetime] = None
        for orig_idx, _, dt in records:
            if prev_dt is not None and (dt - prev_dt).total_seconds() > CAPTURE_GROUP_INTERVAL_SECONDS:
                curr_gid += 1
            gid_map[orig_idx] = f"G{curr_gid:02d}"
            prev_dt = dt

        df["capture_group"] = df.index.map(gid_map)
        return df

    def assign_splits(self, df: pd.DataFrame, dataset_version: str = DEFAULT_DATASET_VERSION) -> pd.DataFrame:
        """방안 B: 묶음 통째 배정 + BLOCK_RULES 의 묶음만 시간순 연속 블록 분할.

        kimchi_v1: G00 만 블록 (Train 26, Val 8, Test 8, Bridge 8)
        kimchi_v2/v3: G00 을 파/파+고추 구간별로 블록, G12 가운데 25장을 Train, G05 를 Val
        kimchi_v4: v3 + G09 마지막 배치(25장)를 Val
        """
        if dataset_version not in BLOCK_RULES:
            raise ValueError(f"알 수 없는 dataset_version: {dataset_version} (가능: {sorted(BLOCK_RULES)})")
        block_rules = BLOCK_RULES[dataset_version]
        role_map = group_role_map(dataset_version)

        # 1. 묶음 무결성 사전 검증 (Assertion)
        expected_groups = {f"G{i:02d}" for i in range(18)}
        actual_groups = set(df["capture_group"].unique())
        assert actual_groups == expected_groups, (
            f"Capture group 불일치! 예상: {len(expected_groups)}개 ({sorted(expected_groups)}), "
            f"실제: {len(actual_groups)}개 ({sorted(actual_groups)})"
        )

        g00_count = len(df[df["capture_group"] == "G00"])
        assert g00_count == 50, f"G00 장수 오류! 예상: 50장, 실제: {g00_count}장"

        g17_count = len(df[df["capture_group"] == "G17"])
        assert g17_count == 150, f"G17 장수 오류! 예상: 150장, 실제: {g17_count}장"

        # 정의되지 않거나 누락된 묶음 검증 (블록 묶음은 role_map 대신 BLOCK_RULES 를 쓴다)
        assert (set(role_map) - set(block_rules)) | set(block_rules) == actual_groups, "묶음 배정 맵과 실제 묶음 집합 불일치!"

        # 2. 블록 분할 묶음: 시간순(파일명 순) 정렬 후 규칙대로 배정
        block_roles: Dict[str, str] = {}
        for gid, blocks in block_rules.items():
            names = sorted(df.loc[df["capture_group"] == gid, "이미지 파일명"])
            starts_ok = blocks[0][0] == 0 and all(a[1] == b[0] for a, b in zip(blocks, blocks[1:]))
            assert starts_ok and blocks[-1][1] == len(names), (
                f"{gid} 블록 규칙 {blocks} 이 {len(names)}장을 빈틈없이 덮지 않습니다!")
            for start, end, role in blocks:
                for fname in names[start:end]:
                    block_roles[fname] = role

        # 3. 전체 데이터셋 역할 매핑
        split_roles: List[str] = []
        for _, row in df.iterrows():
            gid = row["capture_group"]
            fname = row["이미지 파일명"]
            if gid in block_rules:
                split_roles.append(block_roles[fname])
            else:
                assert gid in role_map, f"미정의된 묶음 ID: {gid}"
                split_roles.append(role_map[gid])

        df["split"] = split_roles
        df["dataset_version"] = dataset_version
        return df

    def generate_manifests(self, df: pd.DataFrame) -> Dict[str, Path]:
        """split_manifest.csv 및 역할별 csv 생성"""
        self.manifest_dir.mkdir(parents=True, exist_ok=True)

        main_manifest = self.manifest_dir / "split_manifest.csv"
        df.to_csv(main_manifest, index=False, encoding="utf-8-sig")

        role_paths: Dict[str, Path] = {}
        for role in ROLES:
            sub_df = df[df["split"] == role]
            csv_path = self.manifest_dir / f"{role}.csv"
            sub_df.to_csv(csv_path, index=False, encoding="utf-8-sig")
            role_paths[role] = csv_path

        role_paths["split_manifest"] = main_manifest
        return role_paths

    def generate_dataset_summary(self, df: pd.DataFrame, dataset_version: str = DEFAULT_DATASET_VERSION) -> Path:
        """reports/01_data/dataset_summary.csv 생성 (산출물 1 표준 양식)"""
        (self.reports_dir / "01_data").mkdir(parents=True, exist_ok=True)
        summary_path = self.reports_dir / "01_data" / "dataset_summary.csv"

        rows = []
        for role, purpose in ROLE_PURPOSES.items():
            count = int((df["split"] == role).sum())
            rows.append({
                "dataset_version": dataset_version,
                "role": role,
                "image_count": count,
                "purpose": purpose
            })
        pd.DataFrame(rows).to_csv(summary_path, index=False, encoding="utf-8")
        return summary_path

    def label_fix_dir(self, dataset_version: str) -> Optional[Path]:
        """버전의 라벨 수정본 폴더 (없는 버전이면 None). 수정본이 필요한데 비어 있으면 FileNotFoundError"""
        fix_rel = LABEL_FIX_DIRS.get(dataset_version)
        if fix_rel is None:
            return None
        fix_dir = self.project_root / fix_rel
        if not any(fix_dir.glob("*.txt")):
            raise FileNotFoundError(f"라벨 수정본이 없습니다: {fix_dir}\n  python scripts/04_import_label_fixes.py --apply 를 먼저 실행하세요.")
        return fix_dir

    def build_physical_dataset(self, df: pd.DataFrame, clean: bool = True):
        """
        data/yolo 및 data/bridge_holdout 폴더 구조화 및 파일 배치.
        라벨 수정본(kimchi_v3~)이 있으면 교과 7 최종본 라벨 대신 쓰고, 소스 폴더는 1회 인덱싱해 빠르게 찾는다.
        clean=True 시 기존 폴더를 지우고 다시 만든다 (재분할 때 이전 파일이 남아 누수되지 않게).
        """
        # 라벨 수정본 확인은 폴더를 지우기 전에 먼저
        versions = set(df["dataset_version"])
        assert len(versions) == 1, f"Dataset Version 이 하나가 아닙니다: {versions}"
        fix_dir = self.label_fix_dir(versions.pop())

        if clean:
            if self.yolo_dir.exists():
                shutil.rmtree(self.yolo_dir)
            if self.bridge_dir.exists():
                shutil.rmtree(self.bridge_dir)

        # 폴더 구조 생성
        for split in ["train", "val", "test"]:
            (self.yolo_dir / "images" / split).mkdir(parents=True, exist_ok=True)
            (self.yolo_dir / "labels" / split).mkdir(parents=True, exist_ok=True)
        (self.bridge_dir / "images").mkdir(parents=True, exist_ok=True)
        (self.bridge_dir / "labels").mkdir(parents=True, exist_ok=True)

        # 소스 디렉토리 1회 인덱싱 (O(1) 빠른 매핑)
        img_index = self._build_file_index(self.images_dir, "*")
        lbl_index = self._build_file_index(self.labels_dir, "*.txt")

        for _, row in df.iterrows():
            img_name = row["이미지 파일명"]
            lbl_name = row["라벨(TXT) 파일명"]
            split = row["split"]

            src_img = img_index.get(img_name, self.images_dir / img_name)
            fixed = fix_dir / lbl_name if fix_dir is not None else None
            src_lbl = fixed if fixed is not None and fixed.is_file() else lbl_index.get(lbl_name, self.labels_dir / lbl_name)

            if split in ["train", "val", "test"]:
                dst_img = self.yolo_dir / "images" / split / img_name
                dst_lbl = self.yolo_dir / "labels" / split / lbl_name
            else:  # bridge_holdout
                dst_img = self.bridge_dir / "images" / img_name
                dst_lbl = self.bridge_dir / "labels" / lbl_name

            if src_img.exists() and not dst_img.exists():
                shutil.copy2(src_img, dst_img)
            if src_lbl.exists() and not dst_lbl.exists():
                shutil.copy2(src_lbl, dst_lbl)

    def generate_dataset_yaml(self) -> Path:
        """configs/dataset.yaml 생성 (CLASS_NAMES 로부터 동적 생성)"""
        self.configs_dir.mkdir(parents=True, exist_ok=True)
        yaml_path = self.configs_dir / "dataset.yaml"

        class_lines = "\n".join(f"  {cid}: {name}" for cid, name in CLASS_NAMES.items())
        content = f"""# Subject 8: 조각김치 이물검출 YOLO11 Dataset 설정
path: data/yolo
train: images/train
val: images/val
test: images/test

names:
{class_lines}
"""
        with open(yaml_path, "w", encoding="utf-8") as f:
            f.write(content)
        return yaml_path
