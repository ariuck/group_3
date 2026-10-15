"""
Dataset audit module for Subject 8 (Kimchi Foreign Object Detection).
Performs integrity validation on image-label pairs, YOLO normalization constraints, box-inside-image,
class ranges, duplicate names, empty labels vs. inspection records, and metadata distributions
(BBox per image, Class x scene_type).
"""
from pathlib import Path
import csv
import logging
import statistics
from collections import Counter
from typing import Any, Dict, Iterable, List, Optional, Tuple
import pandas as pd

from src.constants import CLASS_NAMES, NORMAL_SCENE, SCENE_TYPES  # noqa: F401 (다른 모듈이 여기서도 가져다 쓴다)

logger = logging.getLogger(__name__)

# BBox 가 사진 밖으로 나갔다고 볼 최소 초과량 (소수점 오차 허용)
BOX_EDGE_TOLERANCE = 1e-6


class DatasetAuditor:
    """교과 7 FINAL 데이터셋의 무결성 및 통계를 전수 감사하는 클래스"""

    def __init__(self, data_root: Path, report_dir: Path):
        self.data_root = Path(data_root)
        self.images_dir = self.data_root / 'images'
        self.labels_dir = self.data_root / 'labels'
        self.meta_csv = self.data_root / '검수표.csv'
        self.report_dir = Path(report_dir)
        self.report_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def validate_yolo_row(row: str, line_no: int, file_stem: str) -> Tuple[List[Dict[str, Any]], Optional[int]]:
        """
        단일 YOLO 바운딩 박스 라인을 검증합니다.

        Returns:
            Tuple[List[Dict], Optional[int]]: (발견된 이슈 목록, 파싱된 클래스 ID 또는 None)
        """
        issues: List[Dict[str, Any]] = []
        parts = row.strip().split()
        if not parts:
            return issues, None

        if len(parts) != 5:
            issues.append({'file': file_stem, 'line': line_no, 'issue': 'COLUMN_COUNT', 'detail': f'Count: {len(parts)}'})
            return issues, None

        try:
            cls_id = int(parts[0])
            x, y, w, h = map(float, parts[1:])
        except ValueError:
            issues.append({'file': file_stem, 'line': line_no, 'issue': 'PARSE_ERROR', 'detail': row})
            return issues, None

        # 클래스 범위 검사
        if cls_id < 0 or cls_id > 6:
            issues.append({'file': file_stem, 'line': line_no, 'issue': 'CLASS_RANGE', 'detail': f'Class: {cls_id}'})
        elif cls_id == 4:
            issues.append({'file': file_stem, 'line': line_no, 'issue': 'CLASS4_REVIEW', 'detail': 'Class 4 used (should be unused)'})

        # BBox 중심 좌표 (0 <= x, y <= 1) · 크기 (0 < w, h <= 1)
        center_ok = 0.0 <= x <= 1.0 and 0.0 <= y <= 1.0
        size_ok = 0.0 < w <= 1.0 and 0.0 < h <= 1.0
        if not center_ok:
            issues.append({'file': file_stem, 'line': line_no, 'issue': 'CENTER_OUT_OF_RANGE', 'detail': f'x={x}, y={y}'})
        if not size_ok:
            issues.append({'file': file_stem, 'line': line_no, 'issue': 'SIZE_OUT_OF_RANGE', 'detail': f'w={w}, h={h}'})

        # 중심과 크기가 각각은 정상이어도 박스 가장자리가 사진 밖으로 나갈 수 있다
        if center_ok and size_ok:
            overflow = max(w / 2 - x, x + w / 2 - 1.0, h / 2 - y, y + h / 2 - 1.0)
            if overflow > BOX_EDGE_TOLERANCE:
                issues.append({'file': file_stem, 'line': line_no, 'issue': 'BOX_OUT_OF_IMAGE', 'detail': f'overflow={overflow:.6f}'})

        return issues, cls_id

    @staticmethod
    def _index_by_stem(paths: Iterable[Path], kind: str, issues: List[Dict[str, Any]]) -> Dict[str, Path]:
        """stem → 경로. 하위 폴더(train/validation)에 같은 이름이 있으면 DUPLICATE_STEM 으로 남기고 첫 파일만 쓴다."""
        index: Dict[str, Path] = {}
        for p in sorted(paths):
            if p.stem in index:
                first = index[p.stem]
                issues.append({'file': p.stem, 'line': 0, 'issue': 'DUPLICATE_STEM',
                               'detail': f'{kind}: {first.parent.name}/{first.name} , {p.parent.name}/{p.name}'})
                continue
            index[p.stem] = p
        return index

    def _load_meta(self) -> pd.DataFrame:
        if not self.meta_csv.exists():
            return pd.DataFrame()
        try:
            return pd.read_csv(self.meta_csv, encoding='utf-8-sig')
        except Exception as e:
            logger.warning("Failed to read metadata CSV: %s", e)
            return pd.DataFrame()

    def run_audit(self) -> Dict[str, Any]:
        """
        전체 데이터셋 전수 감사를 실행하고 보고서 CSV 3개를 생성합니다.

        Returns:
            Dict[str, Any]: 감사 통계 및 생성된 파일 경로 딕셔너리
        """
        issues: List[Dict[str, Any]] = []
        # 하위 디렉토리(images/train, images/validation 등) 포함 재귀 탐색
        image_files = self._index_by_stem(
            (p for p in self.images_dir.rglob('*') if p.suffix.lower() in ['.jpg', '.jpeg', '.png']), 'image', issues)
        label_files = self._index_by_stem(self.labels_dir.rglob('*.txt'), 'label', issues)

        all_stems = sorted(set(image_files.keys()) | set(label_files.keys()))
        class_counts = {i: 0 for i in range(7)}
        image_bbox_counts: Dict[str, int] = {}
        image_classes: Dict[str, set] = {}
        empty_labels: List[str] = []

        for stem in all_stems:
            if stem not in image_files:
                issues.append({'file': stem, 'line': 0, 'issue': 'MISSING_IMAGE', 'detail': 'Label exists but JPG missing'})
                continue
            if stem not in label_files:
                issues.append({'file': stem, 'line': 0, 'issue': 'MISSING_LABEL', 'detail': 'JPG exists but TXT missing'})
                continue

            # utf-8-sig: Windows 메모장 등으로 저장해 BOM 이 붙은 TXT 도 첫 줄을 정상으로 읽는다
            with open(label_files[stem], 'r', encoding='utf-8-sig') as f:
                lines = [line.strip() for line in f if line.strip()]

            image_bbox_counts[stem] = len(lines)
            image_classes[stem] = set()
            if not lines:
                empty_labels.append(stem)
                continue

            for line_no, line in enumerate(lines, 1):
                row_issues, cls_id = self.validate_yolo_row(line, line_no, stem)
                issues.extend(row_issues)
                if cls_id is not None and 0 <= cls_id <= 6:
                    class_counts[cls_id] += 1
                    image_classes[stem].add(cls_id)

        # 검수표 메타데이터 분포 집계
        df_meta = self._load_meta()
        scene_counts: Dict[str, int] = {}
        source_counts: Dict[str, int] = {}
        split_counts: Dict[str, int] = {}
        scene_by_stem: Dict[str, str] = {}
        if '이미지 유형' in df_meta.columns:
            scene_counts = df_meta['이미지 유형'].value_counts().to_dict()
        if '출처 데이터셋' in df_meta.columns:
            source_counts = df_meta['출처 데이터셋'].value_counts().to_dict()
        if '원래 split' in df_meta.columns:
            split_counts = df_meta['원래 split'].value_counts().to_dict()
        if {'이미지 파일명', '이미지 유형'} <= set(df_meta.columns):
            scene_by_stem = {Path(str(n)).stem: str(s) for n, s in zip(df_meta['이미지 파일명'], df_meta['이미지 유형'])}

            # 교과 7 검수표와 대조: 기록이 없는 사진, 정상 김치로 기록되지 않은 빈 TXT
            for stem in image_bbox_counts:
                if stem not in scene_by_stem:
                    issues.append({'file': stem, 'line': 0, 'issue': 'NOT_IN_MANIFEST', 'detail': '검수표.csv 에 기록 없음'})
            for stem in empty_labels:
                scene = scene_by_stem.get(stem)
                if scene is not None and scene != NORMAL_SCENE:
                    issues.append({'file': stem, 'line': 0, 'issue': 'EMPTY_NOT_NORMAL', 'detail': f'빈 TXT 인데 이미지 유형={scene}'})

        # 1. 이슈 리포트 저장 (audit_issue.csv)
        issue_csv_path = self.report_dir / 'audit_issue.csv'
        with open(issue_csv_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['file', 'line', 'issue', 'detail'])
            writer.writeheader()
            writer.writerows(issues)

        bbox_values = sorted(image_bbox_counts.values())
        bbox_stats: Dict[str, Any] = {}
        if bbox_values:
            bbox_stats = {
                'min': bbox_values[0],
                'median': statistics.median(bbox_values),
                'mean': round(statistics.mean(bbox_values), 2),
                'max': bbox_values[-1],
            }
        bbox_distribution = dict(sorted(Counter(bbox_values).items()))

        # 2. 통계 리포트 작성 (audit_summary.csv)
        summary_rows = [
            {'Category': 'Overview', 'Item': 'Total Images', 'Count': len(image_files)},
            {'Category': 'Overview', 'Item': 'Total Labels', 'Count': len(label_files)},
            {'Category': 'Overview', 'Item': 'Total Pairs', 'Count': len(set(image_files.keys()) & set(label_files.keys()))},
            {'Category': 'Overview', 'Item': 'Empty Labels (No BBox)', 'Count': len(empty_labels)},
            {'Category': 'Overview', 'Item': 'Images with BBoxes', 'Count': len(image_bbox_counts) - len(empty_labels)},
            {'Category': 'Overview', 'Item': 'Total BBoxes', 'Count': sum(class_counts.values())},
            {'Category': 'Overview', 'Item': 'Total Issues Found', 'Count': len(issues)},
        ]
        for cls_id, cnt in class_counts.items():
            summary_rows.append({'Category': 'Class BBox', 'Item': f"Class {cls_id} ({CLASS_NAMES[cls_id]})", 'Count': cnt})
        for name, value in bbox_stats.items():
            summary_rows.append({'Category': 'BBox per Image', 'Item': name, 'Count': value})
        for n_boxes, n_images in bbox_distribution.items():
            summary_rows.append({'Category': 'BBox per Image Distribution', 'Item': f'{n_boxes} boxes', 'Count': n_images})
        for scene, cnt in scene_counts.items():
            summary_rows.append({'Category': 'Scene Type', 'Item': str(scene), 'Count': cnt})
        for src, cnt in source_counts.items():
            summary_rows.append({'Category': 'Source Dataset', 'Item': str(src), 'Count': cnt})
        for splt, cnt in split_counts.items():
            summary_rows.append({'Category': 'Original Split', 'Item': str(splt), 'Count': cnt})

        summary_csv_path = self.report_dir / 'audit_summary.csv'
        pd.DataFrame(summary_rows).to_csv(summary_csv_path, index=False, encoding='utf-8-sig')

        # 3. Class × scene_type: 각 Class 가 들어 있는 사진 수를 장면 유형별로 (가이드 15.2)
        class_scene: Dict[int, Dict[str, int]] = {}
        class_scene_csv_path = self.report_dir / 'audit_class_scene.csv'
        scene_order = [s for s in SCENE_TYPES if s in scene_counts] + [s for s in scene_counts if s not in SCENE_TYPES]
        rows = []
        for cls_id in range(7):
            per_scene = Counter(scene_by_stem.get(stem, 'unknown') for stem, cls in image_classes.items() if cls_id in cls)
            class_scene[cls_id] = dict(per_scene)
            row = {'class_id': cls_id, 'class_name': CLASS_NAMES[cls_id], 'images_total': sum(per_scene.values())}
            for scene in scene_order:
                row[SCENE_TYPES.get(scene, scene)] = per_scene.get(scene, 0)
            rows.append(row)
        pd.DataFrame(rows).to_csv(class_scene_csv_path, index=False, encoding='utf-8-sig')

        return {
            'total_images': len(image_files),
            'total_labels': len(label_files),
            'empty_labels': len(empty_labels),
            'total_bboxes': sum(class_counts.values()),
            'issues_count': len(issues),
            'class_counts': class_counts,
            'scene_counts': scene_counts,
            'source_counts': source_counts,
            'split_counts': split_counts,
            'bbox_per_image': bbox_stats,
            'bbox_distribution': bbox_distribution,
            'class_scene': class_scene,
            'issue_csv': str(issue_csv_path),
            'summary_csv': str(summary_csv_path),
            'class_scene_csv': str(class_scene_csv_path),
        }
