# 시연 절차서 (교과 8) — 초안

> 담당: 5번(QA·시연 검증). 가이드 22.13: 모든 기능을 현장에서 다시 돌리지 않고 **핵심 2가지만** 보여준다.
> **초안 상태**: Final Model·Auto Label 이 아직 없어 `<…>` 로 표시한 곳은 8일차 이후 채운다. 아래 명령 중 `08_predict_images.py` 는 현재 있는 것이고, Auto Label 명령은 만들어진 뒤 확인한다.

| 시연 | 보여줄 것 | 목표 시간 |
|---|---|---|
| 1. 이미지 Detection | Final Model 이 새 이미지에서 BBox·Class·Confidence 를 그린다 | 2분 |
| 2. Auto Label + Human Review | 후보 TXT 를 만들고 교과 7 라벨링 도구에서 사람이 고쳐 승인한다 | 3분 |

## 발표 30분 전 점검

- [ ] 시연 PC 에서 `cd subject8 && python scripts/qa_acceptance_check.py` → **FAIL 0** (패키지·Weight 해시·Manifest 확인)
- [ ] 시연용 사진이 있다 (`<사진 위치>`) — 회사 사진이라 발표용 PC 외부로 보내지 않는다
- [ ] 시연 폴더가 비어 있다 (이전 결과가 섞이지 않게): `runs/predict/demo_detection/`, `demo/auto_label/candidate_labels/`
- [ ] 라벨링 프로그램이 열린다: `cd subject7 && python main.py`
- [ ] 백업 영상·화면 캡처를 바로 열 수 있다 (아래 "실패 대비")
- [ ] 화면 글자가 뒤에서도 보인다 (터미널 글꼴 크게)

## 시연 1 — 이미지 Detection

```text
Final Model Load → 새 이미지 입력 → BBox → Class → Confidence
```

```bash
cd ~/group_3/subject8
python scripts/08_predict_images.py \
    --weights <models/final/final_best.pt> --imgsz <학습 때와 같은 값> \
    --source <시연용 사진 1장 또는 폴더> --name demo_detection
```

- 결과: `runs/predict/demo_detection/compare/*.jpg` (왼쪽 정답, 오른쪽 예측) — 정답이 없는 새 사진이면 예측만 나온다.
- 말할 것: 사용한 모델과 Dataset Version, Confidence 기준 0.25, "작은 이물까지 찾도록 imgsz 를 키운 것이 개선의 핵심".
- 화면에서 확인: BBox 가 사진 안에 있고, Class 이름이 맞고, Confidence 숫자가 보인다.
- Frozen Test·Bridge 사진은 `--allow-test` 없이는 예측되지 않는다. **Final Model 을 확정한 뒤**에만 쓴다.

## 시연 2 — Auto Label + Human Review

```text
새 이미지 → Final Model → BBox·Class 후보 → YOLO TXT 후보 저장
        → 교과 7 라벨링 도구에서 열기 → 사람이 수정·삭제·추가 → 승인·저장
```

1. 후보 생성: `<python scripts/12_auto_label.py …>` (구현 후 확인) → `demo/auto_label/candidate_labels/<사진이름>.txt`
2. 교과 7 도구: `cd ~/group_3/subject7 && python main.py` → **[폴더 열기]** 로 사진과 후보 TXT 가 있는 폴더를 연다.
3. 사람이 확인: 틀린 BBox 삭제, 빠진 BBox 추가, Class 수정 → 저장.
4. 승인된 라벨을 `demo/auto_label/reviewed_labels/` 에 둔다.
- 말할 것: "Auto Label 결과를 바로 정답으로 쓰지 않고, 사람이 확인한 뒤에만 Final Label 이 된다" (교과 7 ↔ 교과 8 연결).

## 실패 대비

발표 중 환경 오류가 나도 발표가 멈추지 않게 미리 준비한다.

| 준비물 | 위치 |
|---|---|
| Detection 시연 영상 | `demo/final_detection_demo.mp4` |
| Auto Label → Human Review 영상 | `demo/auto_label_human_review_demo.mp4` |
| 예측 결과 이미지 | `demo/prediction_images/` |
| 후보·검수 라벨 | `demo/auto_label/candidate_labels/`, `reviewed_labels/` |
| 성능 숫자 | `reports/final_metrics.csv`, `reports/04_improvement/baseline_vs_improved.md` |

| 증상 | 바로 할 일 |
|---|---|
| `ultralytics`/`torch` import 오류 | 영상으로 대체. 발표 후 `pip install -r requirements.txt` |
| CUDA/GPU 오류, 메모리 부족 | `--imgsz` 를 줄이거나 영상으로 대체 |
| 사진·Weight 경로 오류 | 백업 영상 · `demo/prediction_images/` 의 결과 사진을 연다 |
| 라벨링 도구가 안 열림 | 승인 전·후 캡처 두 장으로 설명 |

## 시연 후 정리

- [ ] 시연으로 만든 `runs/predict/demo_detection/` 등 사진이 포함된 결과는 Git 에 올리지 않는다 (`git status` 로 확인)
- [ ] 시연 중 발견한 오류는 `reports/05_acceptance/acceptance_test.md` 의 FAIL 기록에 적는다
