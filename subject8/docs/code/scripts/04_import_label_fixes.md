# `subject8/scripts/04_import_label_fixes.py`

> 라벨링 프로그램(저장소 루트 `main.py`)에서 고친 TXT 를 `kimchi_v3` 라벨 수정본으로 가져온다. 교과 7 최종본(`data/subject7_final`)은 건드리지 않고, **바뀐 사진의 TXT 만** `data/label_fixes/kimchi_v3/` 에 둔다.

[← 코드 문서 목차](../README.md) · [코드 보기](../../../../subject8/scripts/04_import_label_fixes.py)

## 사용법

```bash
cd subject8
python scripts/04_import_label_fixes.py            # 확인만 — 바뀐 사진 수, Class 별 BBox 변화, 작업 목록 대조
python scripts/04_import_label_fixes.py --apply    # 복사 + reports/class5/label_changes_kimchi_v3.csv
python scripts/03_build_split.py --version kimchi_v3 --copy-files
```

| 입력 | 출력 |
|---|---|
| `--src` (기본 `group_3/subject7/data/work/_RAW밖/`), `data/subject7_final/labels/`, `reports/class5/class5_relabel_worklist.csv` | `data/label_fixes/kimchi_v3/*.txt`, `reports/class5/label_changes_kimchi_v3.csv` |

## 주요 구성요소

| 이름 | 설명 |
|---|---|
| `same_box(a, b, tol)` | 같은 Class 이고 좌표 차이가 1e-4 이하이면 같은 BBox (프로그램이 저장하며 자릿수를 바꿔도 변경으로 보지 않음) |
| `compare(orig, new)` | 원본에서 사라진 줄 번호(1부터)와 새로 생긴 BBox 수 |
| `main()` | 비교 → 요약 출력 → 작업 목록 '삭제' 중 아직 남은 박스 · Class 5 외 변경 경고(BBox 단위 — 좌표만 바뀐 것도 잡음, 기록 칸 `Class 5 외 변경 BBox`) → (`--apply`) 복사·기록 |

## 핵심 동작

- 라벨링 프로그램은 `data/raw` 밖의 사진(예: `data/final`)을 고치면 `data/work/_RAW밖/<이름>.txt` 로 저장하고 검수표에는 기록하지 않는다 ([`data_paths.work_label_path`](../../../../subject7/docs/code/src/data_paths.md)). 그래서 교과 7 작업본(`data/work/이물검출_학습데이터*`)과 검수표가 바뀌지 않는다.
- 원본과 내용이 같은 TXT(열어서 Enter 만 누른 사진 등)는 가져오지 않는다.
- `--apply` 때 이전 수정본이 있으면 `kimchi_v3_이전_<시각>` 으로 옮기고 새로 만든다.

## 의존성

- **사용하는 것**: 표준 라이브러리만 (`csv`, `shutil`, `pathlib`)
- **사용하는 곳**: 직접 실행. 결과 폴더는 [`src/split_builder`](../src/split_builder.md) 의 `LABEL_FIX_DIRS` 가 읽는다

## 주의사항

- 작업 목록의 "라벨 목록 No" 는 **원본 TXT 줄 번호**다. 한 사진에서 여러 개를 지울 때는 큰 번호부터 지운다 (지우면 뒤 번호가 당겨짐). 대조는 원본 줄 기준이라 지운 순서와 관계없이 맞게 나온다.
- `_RAW밖` 은 파일 이름만으로 저장되므로, 다른 목적으로 `data/raw` 밖 사진을 고친 적이 있으면 그 TXT 도 함께 비교된다 (교과 7 최종본에 없는 이름은 건너뜀).
- `data/` 는 Git 에 올라가지 않는다. 변경 내역은 `reports/class5/label_changes_kimchi_v3.csv` 로 남는다.
