from pathlib import Path
import csv
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

        if not (0.0 <= x <= 1.0 and 0.0 <= y <= 1.0):
            issues.append({'file': file_stem, 'line': line_no, 'issue': 'CENTER_OUT_OF_RANGE', 'detail': f'x={x}, y={y}'})

        if not (0.0 < w <= 1.0 and 0.0 < h <= 1.0):
            issues.append({'file': file_stem, 'line': line_no, 'issue': 'SIZE_OUT_OF_RANGE', 'detail': f'w={w}, h={h}'})

        return issues

    def run_audit(self) -> Dict:
        image_files = {p.stem: p for p in self.images_dir.rglob('*') if p.suffix.lower() in ['.jpg', '.jpeg', '.png']}
        label_files = {p.stem: p for p in self.labels_dir.rglob('*.txt')}

        all_stems = sorted(set(image_files.keys()) | set(label_files.keys()))
        issues = []
        class_counts = {i: 0 for i in range(7)}
        image_bbox_counts = {}
        empty_labels = []

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
                image_bbox_counts[stem] = 0
                continue

            image_bbox_counts[stem] = len(lines)
            for line_no, line in enumerate(lines, 1):
                row_issues = self.validate_yolo_row(line, line_no, stem)
                issues.extend(row_issues)
                parts = line.split()
                if len(parts) == 5:
                    try:
                        c = int(parts[0])
                        if 0 <= c <= 6:
                            class_counts[c] += 1
                    except ValueError:
                        pass

        scene_counts = {}
        source_counts = {}
        split_counts = {}
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
                print(f"[Warning] Failed to read metadata CSV: {e}")

        issue_csv_path = self.report_dir / 'audit_issue.csv'
        with open(issue_csv_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['file', 'line', 'issue', 'detail'])
            writer.writeheader()
            writer.writerows(issues)

        summary_rows = []
        summary_rows.append({'Category': 'Overview', 'Item': 'Total Images', 'Count': len(image_files)})
        summary_rows.append({'Category': 'Overview', 'Item': 'Total Labels', 'Count': len(label_files)})
        summary_rows.append({'Category': 'Overview', 'Item': 'Total Pairs', 'Count': len(set(image_files.keys()) & set(label_files.keys()))})
        summary_rows.append({'Category': 'Overview', 'Item': 'Empty Labels (No BBox)', 'Count': len(empty_labels)})
        summary_rows.append({'Category': 'Overview', 'Item': 'Images with BBoxes', 'Count': len(image_files) - len(empty_labels)})
        summary_rows.append({'Category': 'Overview', 'Item': 'Total BBoxes', 'Count': sum(class_counts.values())})
        summary_rows.append({'Category': 'Overview', 'Item': 'Total Issues Found', 'Count': len(issues)})

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