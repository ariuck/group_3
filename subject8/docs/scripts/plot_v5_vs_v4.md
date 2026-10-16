# `subject8/scripts/plot_v5_vs_v4.py`

> `kimchi_v4` → `kimchi_v5` 에서 달라진 점을 그림 한 장과 CSV 로 만든다. manifest · 라벨 · `runs_summary.csv` 만 읽으므로 사진·GPU 없이 다시 만들 수 있다.

[← 코드 문서 목차](../README.md) · [코드 보기](../../scripts/plot_v5_vs_v4.py)

## 사용법

```bash
cd subject8
python scripts/plot_v5_vs_v4.py
```

| 입력 | 출력 |
|---|---|
| `manifests/kimchi_v4/split_manifest.csv`, `manifests/split_manifest.csv` (v5, 공식), 라벨 수정본 v3·v5 + `subject7/data/final/labels`, `reports/runs_summary.csv` | `reports/figures/comparison/v5_vs_v4.png`, `reports/01_data/v5_vs_v4.csv` |

그림 4칸: ① 평가 사진 중 Train 과 같은 촬영 묶음 출신 비율 ② 평가 역할의 가장 적은 Class 박스 수 (기준 15) ③ Val Class 별 박스 수 ④ 학습 중 best Val mAP50-95 (640·1280·1920).

## 주요 구성요소

| 이름 | 설명 |
|---|---|
| `stats(version, manifest_dir)` | 역할별 장수, Train 과 같은 묶음 출신 수, 역할×Class 박스 수, 나눠진 묶음 수 |
| `best_map()` | `runs_summary.csv` 에서 Version 별 3개 실행의 best mAP50-95 |
| `bars(ax, cats, values, fmt)` | 두 Version 묶음 막대 + 값 표시 |
| `main()` | 그림·CSV 저장 |

## 의존성

- **사용하는 것**: [`src/split_builder`](../src/split_builder.md), `matplotlib`
- **사용하는 곳**: 직접 실행 ([`plot_runs`](plot_runs.md) 다음)

## 주의사항

- ④ 는 Val 구성이 달라 **직접 비교가 아니다** (그림에 표시). v5 Val 은 Train 이 보지 못한 촬영 묶음이라 점수가 낮게 나온다.
- 한글 글꼴(NanumGothic · Noto Sans CJK KR · Malgun Gothic)이 없으면 글자가 네모로 보일 수 있다.
