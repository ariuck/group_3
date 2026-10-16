# `subject8/scripts/08_predict_images.py`

> 5일차 이미지 Detection. 모델로 사진을 예측하고 정답과 나란히 그린 비교 이미지, 예측 목록, 사진별 TP·CLASS_ERROR·FP·FN 표를 만든다. 6일차 실패분석 후보(틀린 것이 많은 사진 Top 10)도 보여 준다.

[← 코드 문서 목차](../README.md) · [코드 보기](../../scripts/08_predict_images.py)

## 사용법

```bash
cd subject8
python scripts/08_predict_images.py                                  # 공식 Baseline × 그 Version 의 Validation
python scripts/08_predict_images.py --model exp002_v5_imgsz1920      # 다른 모델 (models/README.md 의 실행 이름)
python scripts/08_predict_images.py --model exp004_v5_tile2x2        # 타일링 모델은 조각 예측을 합쳐서
python scripts/08_predict_images.py --conf 0.5 --limit 10            # 확신도 기준 바꿔서 10장만
python scripts/08_predict_images.py --source data/yolo/images/val/250424_133746717037.jpg   # 1장
```

| 옵션 | 기본값 | 설명 |
|---|---|---|
| `--model` | `baseline` | `baseline` · `final` · 실행 이름 · `.pt` 경로 ([`registry.resolve`](../src/registry.md)) |
| `--source` | 그 모델 Version 의 `…/images/val` | 사진 폴더 또는 1장 |
| `--conf` | 0.25 | 이 확신도 이상 예측만 사용 |
| `--imgsz` | 그 모델을 학습할 때의 값 (`runs/<실행>/args.yaml`) | |
| `--name` | `<실행>_val` | `runs/predict/<name>/` |
| `--limit` | 0 (전부) | 앞에서부터 N장 |
| `--allow-test` | 끔 | Frozen Test·Bridge 사진 예측 허용 (8일차 이후) |

| 출력 (`runs/predict/<name>/`, Git 제외) | 내용 |
|---|---|
| `compare/*.jpg` | 왼쪽 정답 · 오른쪽 예측 ([`draw_comparison`](../src/inference.md)) |
| `predictions.csv` | `image, class_id, class_name, conf, x1, y1, x2, y2, result, gt_class` |
| `per_image.csv` | `image, gt, pred, tp, class_error, fp, fn` |

콘솔: 전체 TP·CLASS_ERROR·FP·FN, Class 별 FN·FP, 종류를 틀린 조합(정답 → 예측) 상위 8개, 틀린 것이 많은 사진 Top 10.

## 주요 구성요소

| 이름 | 설명 |
|---|---|
| `PROTECTED` | 모든 Version 의 `data/yolo*/images/test`, `data/bridge_holdout*` — `--allow-test` 없이는 거부 |
| `label_for(img)` | `.../images/<split>/a.jpg` → `.../labels/<split>/a.txt`. 라벨이 없으면 예측만 하고 비교는 생략 |
| `main()` | 예측 → [`match`](../src/inference.md) → 비교 이미지 · CSV · 콘솔 요약. 타일링 모델(`tile2x2`)은 [`tiling.predict_full`](../src/tiling.md) 로 조각 예측을 합친다 |

## 의존성

- **사용하는 것**: [`src/registry`](../src/registry.md), [`src/inference`](../src/inference.md), [`src/tiling`](../src/tiling.md), [`src/split_builder`](../src/split_builder.md), [`src/train_detector`](../src/train_detector.md) (`rel`), `ultralytics.YOLO`
- **사용하는 곳**: 직접 실행 (교과 8 5·6일차, 개선 모델 비교, 발표용 비교 사진)

## 주의사항

- 집계는 `--conf` 한 기준에서의 개수다. `07` 의 mAP·Recall 과 숫자가 다르다.
- 같은 `--name` 으로 다시 실행하면 비교 이미지·CSV 를 덮어쓴다.
- 비교 이미지는 김치 사진이라 Git 에 올리지 않는다.
