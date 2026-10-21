# `scripts/plot_portfolio.py`

> 기록된 CSV에서 README용 핵심 실험 요약 그래프를 만듭니다. 학습·추론·Test 재평가를 실행하지 않습니다.

[← 코드 문서 목차](../README.md) · [코드 보기](../../scripts/plot_portfolio.py)

## 실행

`subject8/`의 의존성이 설치된 환경에서 실행합니다.

```bash
python scripts/plot_portfolio.py
```

## 입력과 출력

| 구분 | 경로·역할 |
|---|---|
| 입력 | `reports/runs_summary.csv` — Baseline·exp001·exp002·공식 Final의 학습 중 best epoch Validation 값 |
| 입력 | `reports/05_final/final_metrics.csv` — 이미 기록된 공식 Final의 Test 결과 |
| 기준 | `src/constants.py`의 공식 Dataset Version과 `src/registry.py`의 Baseline·Final 이름 |
| 출력 | `reports/figures/comparison/portfolio_summary.svg` · `.png` |
| 사용하는 곳 | 루트 README·교과 8 README·보고서 목차 |

## 주요 구성요소

- `read_csv(path)`: UTF-8 CSV를 읽습니다.
- `load_metrics(root)`: 핵심 4개 실행을 읽고 중복·누락·Dataset Version 혼합, 공식 Final과 Test의 모델·버전·split 불일치를 거절합니다.
- `main()`: 같은 Val의 막대그래프와 별도 Test 패널을 그립니다. 입력 CSV를 수정하지 않습니다.

## 해석과 주의사항

- 선택한 네 실행은 전체 실험 중 일부입니다. 한 변수씩 이어진 인과 비교라는 뜻이 아닙니다. 전체 조건·채택 근거는 [모델 선택 보고서](../../reports/final_model_selection.md)를 봅니다.
- Validation은 best epoch, Final은 최고 seed의 값입니다. Test는 별도 패널로 표시하고 평가 이력·갈변·Negative 데이터 한계를 함께 안내합니다.
- 현재 핵심 비교 대상 exp001·exp002는 v5 실행입니다. 공식 버전이 바뀌면 비교 실행도 새 버전에 맞게 바꾸어야 하며, 기존 값이 다른 버전이면 생성이 실패합니다.
- 의존성은 Python 표준 라이브러리, Matplotlib, `src/constants.py`, `src/registry.py`입니다. 사진·GPU는 사용하지 않습니다.
