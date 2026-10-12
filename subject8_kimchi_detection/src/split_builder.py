import os
import re
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple
import pandas as pd

class SplitBuilder:
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

    def _find_file(self, base_dir: Path, filename: str) -> Path:
        """직접 경로 또는 재귀 탐색(rglob)을 통해 파일 경로 반환"""
        direct = base_dir / filename
        if direct.exists():
            return direct
        matches = list(base_dir.rglob(filename))
        if matches:
            return matches[0]
        return direct

    def assign_capture_groups(self, df: pd.DataFrame) -> pd.DataFrame:
        """파일명 타임스탬프 기준 5분(300초) 초과 간격으로 G00~G17 18개 묶음 부여"""
        records = []
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
        
        gid_map = {}
        curr_gid = 0
        prev_dt = None
        for item in records:
            orig_idx, fname, dt = item
            if prev_dt is not None and (dt - prev_dt).total_seconds() > 300:
                curr_gid += 1
            gid_map[orig_idx] = f"G{curr_gid:02d}"
            prev_dt = dt

        df["capture_group"] = df.index.map(gid_map)
        return df

    def assign_splits(self, df: pd.DataFrame, dataset_version: str = "kimchi_v1") -> pd.DataFrame:
        """방안 B: 17개 묶음 통째 배정 + G00 50장 시간순 연속 블록 분할 (Train 26, Val 8, Test 8, Bridge 8)"""
        # 1. 묶음 무결성 사전 검증 (Assertion)
        expected_groups = {f"G{i:02d}" for i in range(18)}
        actual_groups = set(df["capture_group"].unique())
        assert actual_groups == expected_groups, (
            f"Capture group 불일치! 예상: {len(expected_groups)}개 ({sorted(expected_groups)}), 실제: {len(actual_groups)}개 ({sorted(actual_groups)})"
        )

        g00_count = len(df[df["capture_group"] == "G00"])
        assert g00_count == 50, f"G00 장수 오류! 예상: 50장, 실제: {g00_count}장"

        g17_count = len(df[df["capture_group"] == "G17"])
        assert g17_count == 150, f"G17 장수 오류! 예상: 150장, 실제: {g17_count}장"

        # 그룹별 기본 역할 맵 (17개 묶음)
        group_role_map = {
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

        # 정의되지 않거나 누락된 묶음 검증
        assert set(group_role_map.keys()) | {"G00"} == actual_groups, "group_role_map과 실제 묶음 집합 불일치!"

        # G00 시간순 정렬 후 블록 분할
        df_g00 = df[df["capture_group"] == "G00"].copy()
        df_g00 = df_g00.sort_values("이미지 파일명").reset_index(drop=True)
        g00_roles = {}
        for i, row in df_g00.iterrows():
            if i < 26:
                role = "train"
            elif i < 34:
                role = "val"
            elif i < 42:
                role = "test"
            else:
                role = "bridge_holdout"
            g00_roles[row["이미지 파일명"]] = role

        split_roles = []
        for idx, row in df.iterrows():
            gid = row["capture_group"]
            fname = row["이미지 파일명"]
            if gid == "G00":
                split_roles.append(g00_roles[fname])
            else:
                assert gid in group_role_map, f"미정의된 묶음 ID: {gid}"
                split_roles.append(group_role_map[gid])

        df["split"] = split_roles
        df["dataset_version"] = dataset_version
        return df

    def generate_manifests(self, df: pd.DataFrame) -> Dict[str, Path]:
        """split_manifest.csv 및 역할별 csv 생성"""
        self.manifest_dir.mkdir(parents=True, exist_ok=True)
        
        main_manifest = self.manifest_dir / "split_manifest.csv"
        df.to_csv(main_manifest, index=False, encoding="utf-8-sig")

        role_paths = {}
        for role in ["train", "val", "test", "bridge_holdout"]:
            sub_df = df[df["split"] == role]
            csv_path = self.manifest_dir / f"{role}.csv"
            sub_df.to_csv(csv_path, index=False, encoding="utf-8-sig")
            role_paths[role] = csv_path

        role_paths["split_manifest"] = main_manifest
        return role_paths

    def generate_dataset_summary(self, df: pd.DataFrame, dataset_version: str = "kimchi_v1") -> Path:
        """reports/dataset_summary.csv 생성 (산출물 1 표준 양식)"""
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        summary_path = self.reports_dir / "dataset_summary.csv"

        purposes = {
            "train": "model_training",
            "val": "model_validation",
            "test": "final_evaluation",
            "bridge_holdout": "subject14_bridge"
        }
        
        rows = []
        for role, purpose in purposes.items():
            count = int((df["split"] == role).sum())
            rows.append({
                "dataset_version": dataset_version,
                "role": role,
                "image_count": count,
                "purpose": purpose
            })
        summary_df = pd.DataFrame(rows)
        summary_df.to_csv(summary_path, index=False, encoding="utf-8")
        return summary_path

    def build_physical_dataset(self, df: pd.DataFrame, clean: bool = True):
        """data/yolo 및 data/bridge_holdout 폴더 구조화 및 파일 배치 (clean=True 시 기존 디렉토리 초기화 후 재배치)"""
        if clean:
            if self.yolo_dir.exists():
                shutil.rmtree(self.yolo_dir)
            if self.bridge_dir.exists():
                shutil.rmtree(self.bridge_dir)

        # 폴더 생성
        for split in ["train", "val", "test"]:
            (self.yolo_dir / "images" / split).mkdir(parents=True, exist_ok=True)
            (self.yolo_dir / "labels" / split).mkdir(parents=True, exist_ok=True)

        (self.bridge_dir / "images").mkdir(parents=True, exist_ok=True)
        (self.bridge_dir / "labels").mkdir(parents=True, exist_ok=True)

        # 파일 복사 또는 심볼릭 링크
        for idx, row in df.iterrows():
            img_name = row["이미지 파일명"]
            lbl_name = row["라벨(TXT) 파일명"]
            split = row["split"]

            src_img = self._find_file(self.images_dir, img_name)
            src_lbl = self._find_file(self.labels_dir, lbl_name)

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
        """configs/dataset.yaml 생성"""
        self.configs_dir.mkdir(parents=True, exist_ok=True)
        yaml_path = self.configs_dir / "dataset.yaml"

        content = """# Subject 8: 조각김치 이물검출 YOLO11 Dataset 설정
path: data/yolo
train: images/train
val: images/val
test: images/test

names:
  0: leaf_paper
  1: plastic_stone_metal
  2: branch
  3: insect
  4: rubber_glove_unused
  5: disease_browning
  6: green_onion_pepper
"""
        with open(yaml_path, "w", encoding="utf-8") as f:
            f.write(content)
        return yaml_path
