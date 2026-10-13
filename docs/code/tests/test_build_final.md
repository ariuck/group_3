# `tests/test_build_final.py`

> 최종본 만들기(`tools/build_final.py`) 시험. 가짜 RAW·WORK·검수표 폴더로 확인한다.

[← 코드 문서 목차](../README.md) · [코드 보기](../../../tests/test_build_final.py) · 대상: [`tools/build_final`](../tools/build_final.md)

## 실행

```bash
python -m unittest tests/test_build_final.py
```

## 시험 내용 (`BuildFinalTest`)

| 묶음 | 확인하는 것 |
|---|---|
| 조건 | 모두 검수되면 통과 · 검수 안 된 상태 / 검수자 없음 / 작성자=검수자 / 검수표에 줄 없음 / 검수표 파일 없음 / Validation CRITICAL 이면 막힘 |
| 구조 | `flat` 은 한 폴더 · `split` 은 train/validation 유지 · `split` 은 다른 split 의 같은 이름은 허용하고 같은 split 은 막음 · `flat` 에서 이름 겹치면 막음 |
| 만들기 | 구조 유지 + 검수한(WORK) 라벨 사용 · 사진은 똑같은 복사본이고 RAW 불변 · 막혔으면 만들지 않음 · 기존 최종본은 `--overwrite` 필요하고 백업됨 · 빈 골격(`.gitkeep`)은 기존 내용으로 보지 않음 |
