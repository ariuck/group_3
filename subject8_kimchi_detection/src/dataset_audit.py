from pathlib import Path
import csv
import statistics
from collections import Counter
import pandas as pd
from typing import Dict, List

CLASS_NAMES = {
    0: 'leaf_paper',
    1: 'plastic_stone_metal',
    2: 'branch',
    3: 'insect',
    4: 'rubber_glove_unused',
    5: 'disease_browning',
    6: 'green_onion_pepper'
}

# 교과 7 검수표 `이미지 유형` 값 → 교과 8 scene_type 이름
SCENE_TYPES = {
    '김치+대상 객체': 'kimchi_with_target',
    '정상 김치': 'normal_kimchi',
    '대상 객체 단독': 'object_only',
    '판단 어려움': 'other_review',
}
NORMAL_SCENE = '정상 김치'

# BBox 가 사진 밖으로 나갔다고 볼 최소 초과량 (소수점 오차 허용)
BOX_EDGE_TOLERANCE = 1e-6


class DatasetAuditor:
    def __init__(self, data_root: Path, report_dir: Path):
        self.data_root = Path(data_root)
        self.images_dir = self.data_root / 'images'
        self.labels_dir = self.data_root / 'labels'
        self.meta_csv = self.data_root / '검수표.csv'
        self.report_dir = Path(report_dir)
        self.report_dir.mkdir(parents=True, exist_ok=True)

    def validate_yolo_row(self, row: str, line_no: int, file_stem: str) -> List[Dict]:
        issues = []
        parts = row.strip().split()
        if not parts:
            return issues

        if len(parts) != 5:
            issues.append({'file': file_stem, 'line': line_no, 'issue': 'COLUMN_COUNT', 'detail': f'Count: {len(parts)}'})
            return issues

        try:
            cls_id = int(parts[0])
            x, y, w, h = map(float, parts[1:])
        except ValueError:
            issues.append({'file': file_stem, 'line': line_no, 'issue': 'PARSE_ERROR', 'detail': row})
            return issues

        if cls_id < 0 or cls_id > 6:
            issues.append({'file': file_stem, 'line': line_no, 'issue': 'CLASS_RANGE', 'detail': f'Class: {cls_id}'})
        elif cls_id == 4:
            issues.append({'file': file_stem, 'line': line_no, 'issue': 'CLASS4_REVIEW', 'detail': 'Class 4 used (should be unused)'})

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

        return issues

    @staticmethod
    def _index_by_stem(paths, kind: str, issues: List[Dict]) -> Dict[str, Path]:
        """stem → 경로. 하위 폴더(train/validation)에 같은 이름이 있으면 DUPLICATE_STEM 으로 남기고 첫 파일만 쓴다."""
        index = {}
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
            print(f"[Warning] Failed to read metadata CSV: {e}")
            return pd.DataFrame()

    def run_audit(self) -> Dict:
        issues = []
        image_files = self._index_by_stem(
            (p for p in self.images_dir.rglob('*') if p.suffix.lower() in ['.jpg', '.jpeg', '.png']), 'image', issues)
        label_files = self._index_by_stem(self.labels_dir.rglob('*.txt'), 'label', issues)

        all_stems = sorted(set(image_files.keys()) | set(label_files.keys()))
        class_counts = {i: 0 for i in range(7)}
        image_bbox_counts = {}
        image_classes = {}
        empty_labels = []

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
                row_issues = self.validate_yolo_row(line, line_no, stem)
                issues.extend(row_issues)
                parts = line.split()
                if len(parts) == 5:
                    try:
                        c = int(parts[0])
                        if 0 <= c <= 6:
                            class_counts[c] += 1
                            image_classes[stem].add(c)
                    except ValueError:
                        pass

        df_meta = self._load_meta()
        scene_counts = {}
        source_counts = {}
        split_counts = {}
        scene_by_stem = {}
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

        issue_csv_path = self.report_dir / 'audit_issue.csv'
        with open(issue_csv_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['file', 'line', 'issue', 'detail'])
            writer.writeheader()
            writer.writerows(issues)

        bbox_values = sorted(image_bbox_counts.values())
        bbox_stats = {}
        if bbox_values:
            bbox_stats = {
                'min': bbox_values[0],
                'median': statistics.median(bbox_values),
                'mean': round(statistics.mean(bbox_values), 2),
                'max': bbox_values[-1],
            }
        bbox_distribution = dict(sorted(Counter(bbox_values).items()))

        summary_rows = []
        summary_rows.append({'Category': 'Overview', 'Item': 'Total Images', 'Count': len(image_files)})
        summary_rows.append({'Category': 'Overview', 'Item': 'Total Labels', 'Count': len(label_files)})
        summary_rows.append({'Category': 'Overview', 'Item': 'Total Pairs', 'Count': len(set(image_files.keys()) & set(label_files.keys()))})
        summary_rows.append({'Category': 'Overview', 'Item': 'Empty Labels (No BBox)', 'Count': len(empty_labels)})
        summary_rows.append({'Category': 'Overview', 'Item': 'Images with BBoxes', 'Count': len(image_bbox_counts) - len(empty_labels)})
        summary_rows.append({'Category': 'Overview', 'Item': 'Total BBoxes', 'Count': sum(class_counts.values())})
        summary_rows.append({'Category': 'Overview', 'Item': 'Total Issues Found', 'Count': len(issues)})

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

        # Class × scene_type: 각 Class 가 들어 있는 사진 수를 장면 유형별로 (가이드 15.2)
        class_scene = {}
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
