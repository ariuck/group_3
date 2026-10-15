# `tests/test_navigator.py`

> 사진 이동(navigator) 시험. 화면 없이 사진 목록 · 이전/다음 · 진행률 · 필터를 확인한다.

[← 코드 문서 목차](../README.md) · [코드 보기](../../../tests/test_navigator.py) · 대상: [`src/ui/navigator`](../src/ui/navigator.md)

## 실행

```bash
python -m unittest tests/test_navigator.py
```

## 시험 내용

| 클래스 | 확인하는 것 |
|---|---|
| `NavigatorTest` | 자연 정렬(`img2` < `img10`) · JPG 만 · 이전/다음과 진행률 · 아무것도 안 열었을 때 · 폴더가 바뀌면 목록 다시 만듦 · 목록에 없는 파일은 1장짜리로 · `load_folder` |
| `FilterTest` | 해당 사진만 · 현재 사진이 해당하면 위치 유지 · 걸러지면 `index = -1` · 필터 해제 시 복원 · 숨겨진 사진을 열면 필터 해제 · 새 폴더는 필터 초기화 · 번호 이동은 보이는 목록 기준 |
| `JumpToIndexTest` | 번호로 경로 찾기 |
| `LoadFolderTest` | 바로 아래 사진 · 데이터셋 폴더는 하위까지 · split 폴더끼리 묶고 이름으로 섞지 않음 · 빈 폴더는 `None` 이고 현재 목록 유지 · 안의 사진을 열어도 목록 유지 · 폴더 밖 사진은 자기 목록을 새로 만듦 |
