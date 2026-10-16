# `tools/restore_from_final.py`

> 다른 PC 준비: Git 에 올린 **최종본 라벨·검수표**와 `data/raw` 의 회사 원본 사진으로 `data/work`·검수표·`data/final/images` 를 되살린다.

[← 코드 문서 목차](../README.md) · [코드 보기](../../tools/restore_from_final.py)

## 사용법

```bash
python tools/restore_from_final.py            # 미리보기 (만들 파일 수 · 없는 파일 · 내용이 다른 파일)
python tools/restore_from_final.py --apply    # 실제로 만든다
```

| Git 에 있는 것 | 각 PC 에 넣을 것 | `--apply` 가 만드는 것 |
|---|---|---|
| `data/final/labels/<split>/*.txt` (900), `data/final/검수표.csv`, `data/final/classes.txt` | `data/raw/<데이터셋>/images|labels/<split>/` 회사 원본 그대로 | `data/work/<데이터셋>/labels/<split>/*.txt` (최종 라벨), `manifests/dataset_manifest.csv` (= `검수표.csv`), `data/final/images/<split>/*.jpg` (RAW 하드 링크) |

끝나면 [`build_final.check`](build_final.md) 를 돌려 **지금 RAW·work·검수표로 다시 만들어도 Git 의 최종 라벨과 같은지** 확인한다.

## 주요 구성요소

| 함수 | 설명 |
|---|---|
| `read_rows(final_dir)` | `data/final/검수표.csv` 줄 목록 |
| `plan(raw_dir, work_dir, final_dir, manifest_path)` | `{copy: [(원본, 대상, 종류)], same, conflict, missing}` — 검수표의 `출처 데이터셋`·`원래 split` 으로 위치를 정한다 |
| `link_or_copy(src, dst)` | 하드 링크, 안 되면 복사 (사진) |
| `verify(...)` | `build_final.check` 결과의 막힘 + 라벨이 Git 최종본과 다른 사진 + 장수 차이 → 문제 목록 (비면 통과) |
| `main(argv)` | CLI. RAW 사진이나 최종 라벨이 없으면 종료 코드 1 |

## 의존성

- **사용하는 것**: [`src/settings`](../src/settings.md), [`tools/build_final`](build_final.md) (`check`, `MANIFEST_NAME`)
- **사용하는 곳**: 직접 실행 (다른 PC 처음 설정), 교과 8 README "다른 PC 에서 시작하기"

## 주의사항

- RAW 는 읽기만 한다. 이미 있는 파일은 내용이 같으면 건너뛰고, **다르면 덮어쓰지 않고** 목록만 보여 준다 (누군가 작업 중인 라벨·검수표 보호).
- 사진은 하드 링크라 용량을 더 쓰지 않는다. RAW 와 다른 디스크면 복사한다.
- `data/work/_RAW밖/` (RAW 밖 폴더를 열어 저장한 라벨) 은 되살리지 않는다. 교과 8 의 라벨 수정본은 `subject8/data/label_fixes/` 에 따로 있다.
