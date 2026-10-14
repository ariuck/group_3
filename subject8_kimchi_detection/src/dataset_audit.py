"""
Dataset audit module for Subject 8 (Kimchi Foreign Object Detection).
Performs integrity validation on image-label pairs, YOLO normalization constraints,
class ranges, empty labels, and metadata distributions.
"""
from pathlib import Path
import csv
import logging
from typing import Dict, List, Optional, Tuple, Any
import pandas as pd

from src.constants import CLASS_NAMES

logger = logging.getLogger(__name__)

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
            issues.append({
                'file': file_stem, 'line': line_no,
                'issue': 'COLUMN_COUNT', 'detail': f'Count: {len(parts)}'
            })
            return issues, None

        try:
            cls_id = int(parts[0])
            x, y, w, h = map(float, parts[1:])
        except ValueError:
            issues.append({
                'file': file_stem, 'line': line_no,
                'issue': 'PARSE_ERROR', 'detail': row
            })
            return issues, None

        # 클래스 범위 검사
        if cls_id < 0 or cls_id > 6:
            issues.append({
                'file': file_stem, 'line': line_no,
                'issue': 'CLASS_RANGE', 'detail': f'Class: {cls_id}'
            })
        elif cls_id == 4:
            issues.append({
                'file': file_stem, 'line': line_no,
                'issue': 'CLASS4_REVIEW', 'detail': 'Class 4 used (should be unused)'
            })

        # BBox 중심 좌표 정규화 검사 (0.0 <= x, y <= 1.0)
        if not (0.0 <= x <= 1.0 and 0.0 <= y <= 1.0):
            issues.append({
                'file': file_stem, 'line': line_no,
                'issue': 'CENTER_OUT_OF_RANGE', 'detail': f'x={x}, y={y}'
            })

        # BBox 크기 검사 (0.0 < w, h <= 1.0)
        if not (0.0 < w <= 1.0 and 0.0 < h <= 1.0):
            issues.append({
                'file': file_stem, 'line': line_no,
                'issue': 'SIZE_OUT_OF_RANGE', 'detail': f'w={w}, h={h}'
            })

        return issues, cls_id

    def run_audit(self) -> Dict[str, Any]:
        """
        전체 데이터셋 전수 감사를 실행하고 요약 보고서 CSV를 생성합니다.
        
        Returns:
            Dict[str, Any]: 감사 통계 및 생성된 파일 경로 딕셔너리
        """
        # 하위 디렉토리(images/train, images/val 등) 포함 재귀 탐색
        image_files = {p.stem: p for p in self.images_dir.rglob('*') if p.suffix.lower() in ['.jpg', '.jpeg', '.png']}
        label_files = {p.stem: p for p in self.labels_dir.rglob('*.txt')}

        all_stems = sorted(set(image_files.keys()) | set(label_files.keys()))
        issues: List[Dict[str, Any]] = []
        class_counts = {i: 0 for i in range(7)}
        empty_labels: List[str] = []

        for stem in all_stems:
            if stem not in image_files:
                issues.append({'file': stem, 'line': 0, 'issue': 'MISSING_IMAGE', 'detail': 'Label exists but JPG missing'})
                continue
            if stem not in label_files:
                issues.append({'file': stem, 'line': 0, 'issue': 'MISSING_LABEL', 'detail': 'JPG exists but TXT missing'})
                continue

            lbl_path = label_files[stem]
            with open(lbl_path, 'r', encoding='utf-8') as f:
                lines = [line.strip() for line in f if line.strip()]

            if not lines:
                empty_labels.append(stem)
                continue

            for line_no, line in enumerate(lines, 1):
                row_issues, cls_id = self.validate_yolo_row(line, line_no, stem)
                issues.extend(row_issues)
                if cls_id is not None and 0 <= cls_id <= 6:
                    class_counts[cls_id] += 1

        # 검수표 메타데이터 분포 집계
        scene_counts: Dict[str, int] = {}
        source_counts: Dict[str, int] = {}
        split_counts: Dict[str, int] = {}
        if self.meta_csv.exists():
            try:
                df_meta = pd.read_csv(self.meta_csv, encoding='utf-8-sig')
                if '이미지 유형' in df_meta.columns:
                    scene_counts = df_meta['이미지 유형'].value_counts().to_dict()
                if '출처 데이터셋' in df_meta.columns:
                    source_counts = df_meta['출처 데이터셋'].value_counts().to_dict()
                if '원래 split' in df_meta.columns:
                    split_counts = df_meta['원래 split'].value_counts().to_dict()
            except Exception as e:
                logger.warning("Failed to read metadata CSV: %s", e)

        # 1. 이슈 리포트 저장 (audit_issue.csv)
        issue_csv_path = self.report_dir / 'audit_issue.csv'
        with open(issue_csv_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['file', 'line', 'issue', 'detail'])
            writer.writeheader()
            writer.writerows(issues)

        # 2. 통계 리포트 작성 (audit_summary.csv)
        summary_rows = [
            {'Category': 'Overview', 'Item': 'Total Images', 'Count': len(image_files)},
            {'Category': 'Overview', 'Item': 'Total Labels', 'Count': len(label_files)},
            {'Category': 'Overview', 'Item': 'Total Pairs', 'Count': len(set(image_files.keys()) & set(label_files.keys()))},
            {'Category': 'Overview', 'Item': 'Empty Labels (No BBox)', 'Count': len(empty_labels)},
            {'Category': 'Overview', 'Item': 'Images with BBoxes', 'Count': len(image_files) - len(empty_labels)},
            {'Category': 'Overview', 'Item': 'Total BBoxes', 'Count': sum(class_counts.values())},
            {'Category': 'Overview', 'Item': 'Total Issues Found', 'Count': len(issues)},
        ]

        for cls_id, cnt in class_counts.items():
            summary_rows.append({'Category': 'Class BBox', 'Item': f"Class {cls_id} ({CLASS_NAMES[cls_id]})", 'Count': cnt})

        for scene, cnt in scene_counts.items():
            summary_rows.append({'Category': 'Scene Type', 'Item': str(scene), 'Count': cnt})

        for src, cnt in source_counts.items():
            summary_rows.append({'Category': 'Source Dataset', 'Item': str(src), 'Count': cnt})

        for splt, cnt in split_counts.items():
            summary_rows.append({'Category': 'Original Split', 'Item': str(splt), 'Count': cnt})

        summary_csv_path = self.report_dir / 'audit_summary.csv'
        pd.DataFrame(summary_rows).to_csv(summary_csv_path, index=False, encoding='utf-8-sig')

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
            'issue_csv': str(issue_csv_path),
            'summary_csv': str(summary_csv_path)
        }