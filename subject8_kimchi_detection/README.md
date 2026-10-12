# Subject 8: 조각김치 이물검출 Vision 객체검출 모듈

> **대상**: 교과 8 [중간] Vision 기반 객체검출 모듈  
> **선행 프로젝트**: 교과 7 조각김치 이물검출 라벨링 프로젝트  
> **입력 데이터**: 교과 7 검수 완료 4K JPG 900장 + YOLO TXT 900개 (\data/subject7_final/\)  
> **핵심 기술**: Python · Ultralytics YOLO11 (\yolo11n.pt\) · PyTorch · OpenCV · Pandas  
> **보안**: 기업 제공 데이터는 NDA와 기관 보안정책을 준수하며 외부 공개 저장소에 업로드하지 않습니다.

---

## 1. 프로젝트 목적
교과 7에서 구축한 고품질 정답 라벨 데이터를 기반으로, 조각김치 이물검출을 위한 객체검출 모델(YOLO11)을 학습·평가하고 체계적인 실패 원인 분석을 통해 1변수 개선 실험을 거쳐 신뢰할 수 있는 Final Model을 확정합니다.

---

## 2. 교과 7 → 교과 8 연결
- **교과 7 산출물 위치**: \data/subject7_final/\ (JPG 900장 + TXT 900개, classes.txt, 검수표.csv)
- **Class ID 0~6 체계**: 교과 7에서 확정한 라벨 체계를 100% 동일하게 계승하여 유지합니다.
- **역할 분리**: 교과 7은 사람이 정답을 만드는 과정, 교과 8은 모델이 스스로 검출하도록 학습·개선하는 과정입니다.

---

## 3. Dataset 설명
- **총 데이터**: 조각김치 4K 이미지 900장 + YOLO 포맷 라벨 900개
- **데이터 출처**: Dataset 1 (train), Dataset 2 (train, validation)
- **Class 정의 (0~6)**:
  - 0: \leaf_paper\ (나뭇잎·종이류)
  - 1: \plastic_stone_metal\ (플라스틱·돌·금속류)
  - 2: \ranch\ (나뭇가지류)
  - 3: \insect\ (곤충류)
  - 4: \ubber_glove_unused\ (미사용/예약)
  - 5: \disease_browning\ (갈변·병해)
  - 6: \green_onion_pepper\ (파·고추류 부속물)

---

## 4. 실행 환경
- **OS**: Ubuntu (WSL2)
- **Python**: TBD
- **PyTorch**: TBD
- **Ultralytics**: TBD
- **GPU (CUDA)**: TBD
- **사전학습 가중치**: \yolo11n.pt
---

## 5. Dataset Split (2~3일차)
- **분할 정책**: \docs/split_policy.md\ (TBD)
- **매니페스트**: \manifests/split_manifest.csv\ (TBD)
- **Train / Validation / Frozen Test / Bridge Holdout** 비율 및 명단 확정 예정

---

## 6. Baseline 모델 (4~5일차)
- **학습 조건**: \eports/baseline_training_condition.md\ (TBD)
- **성능 지표**: \eports/baseline_metrics.csv\ (TBD)
- **가중치**: \models/baseline/baseline_best.pt
---

## 7. Failure Analysis (6일차)
- **실패 분석표**: \eports/failure_analysis.csv\ (TBD)
- **원인 가설 및 개선 계획**: \eports/failure_hypothesis.md\ (TBD)
- **실패 시각화 이미지**: \demo/failure_analysis/
---

## 8. Improvement (7일차)
- **개선 실험 계획**: \eports/improvement_experiment.md\ (TBD)
- **실험 로그**: \eports/experiment_log.csv\ (TBD)
- **Baseline vs Improved 비교**: \eports/baseline_vs_improved.md\ (TBD)

---

## 9. Final Model (8일차)
- **선정 근거**: \eports/final_model_selection.md\ (TBD)
- **가중치**: \models/final/final_best.pt
---

## 10. Frozen Test (8일차)
- **최종 검증 지표**: \eports/final_metrics.csv\ (TBD)
- **혼동 행렬 및 곡선**: \eports/figures/\ (TBD)

---

## 11. Detection / Auto Label (8일차)
- **추론 이미지**: \demo/prediction_images/- **자동 라벨 후보 및 리뷰**: \eports/auto_label_review.csv\, \demo/auto_label/
---

## 12. 알려진 한계 및 운영 기준 (9일차)
- TBD

---

## 13. 교과 14 Handoff (9일차)
- **인계 문서**: \docs/handoff_subject14.md\ (TBD)
- **Bridge Holdout 전달**: \data/bridge_holdout/EOF
