# `src/settings.py`

> 프로젝트 공통 설정. 데이터 폴더 경로(RAW / WORK / FINAL), 검수표 경로, `configs/classes.yaml` 에서 읽은 Class 기준을 한곳에 모은다.

[← 코드 문서 목차](../README.md) · [코드 보기](../../src/settings.py)

## 역할

- 모든 모듈이 같은 경로·Class 정보를 쓰도록 하는 기준점이다.
- Class 설정 파일을 읽지 못해도 프로그램이 죽지 않도록 기본값(`DEFAULT_CLASSES`)으로 대신한다.

## 주요 구성요소

| 이름 | 값 / 형태 | 설명 |
|---|---|---|
| `PROJECT_DIR` | `Path` | 저장소 루트 |
| `RAW_DIR` | `data/raw` | 회사 제공 원본. **읽기만 한다** |
| `WORK_DIR` | `data/work` | 수정한 라벨 저장 위치 (RAW 와 같은 폴더 구조) |
| `FINAL_DIR` | `data/final` | 검수 완료 최종본 |
| `CONFIG_PATH` | `configs/classes.yaml` | Class 기준 파일 |
| `MANIFEST_PATH` | `manifests/dataset_manifest.csv` | 검수표 CSV |
| `IMAGE_EXTS` | `{".jpg", ".jpeg"}` | 이미지로 인정하는 확장자 (대소문자 무시는 호출하는 쪽에서 `.lower()`) |
| `DEFAULT_COLOR` | `#ff00ff` | 색이 없거나 Class 범위 밖일 때 |
| `DEFAULT_CLASSES` | `list[dict]` | YAML 을 못 읽을 때 쓰는 Class 0~6 기본값 |
| `load_classes(path=None)` | `-> [{id, name, enabled, color}]` | YAML 을 읽고 ID 가 0부터 빠짐없이 이어지는지 확인. 실패하면 경고 출력 후 기본값 |
| `CLASSES` | `list[dict]` | import 시점에 `load_classes()` 결과 |
| `UNUSED_CLASSES` | `set[int]` | `enabled: false` 인 Class. 현재 `{4}` (고무장갑) |
| `class_name(cid, with_note=True)` | `-> str` | Class 이름. 범위 밖이면 `?`, 사용 안 하는 Class 는 ` (사용 안 함)` 을 붙임 |
| `class_color(cid)` | `-> str` | Class 색. 범위 밖이면 `DEFAULT_COLOR` |

## 의존성

- **사용하는 것**: `configs/classes.yaml`, PyYAML (`requirements.txt`)
- **사용하는 곳**: [`data_paths`](data_paths.md), [`manifest_writer`](manifest/manifest_writer.md), [`validator`](validation/validator.md), [`ui/main_window`](ui/main_window.md), [`ui/session`](ui/session.md), `tools/` 의 [`build_final`](../tools/build_final.md) · [`export_manifest_xlsx`](../tools/export_manifest_xlsx.md) · [`final_evidence`](../tools/final_evidence.md) · [`import_labels`](../tools/import_labels.md) · [`merge_manifests`](../tools/merge_manifests.md) · [`pack_results`](../tools/pack_results.md) · [`qa_summary`](../tools/qa_summary.md), 대부분의 `tests/`

## 사용 예

```python
from src import settings

settings.class_name(4)              # '고무장갑 (사용 안 함)'
settings.class_color(2)             # '#1e88e5'
4 in settings.UNUSED_CLASSES        # True
```

## 주의사항

- **경로는 모듈 변수다.** 테스트는 `settings.RAW_DIR = 임시폴더` 처럼 바꿔서 쓴다. 그래서 [`data_paths`](data_paths.md) 등은 경로를 import 할 때 복사하지 않고 **호출할 때마다 `settings.XXX` 로 읽는다.** 새 코드도 `from src.settings import RAW_DIR` 대신 `settings.RAW_DIR` 로 써야 테스트가 동작한다.
- `classes.yaml` 과 `DEFAULT_CLASSES` 는 **내용이 같아야 한다.** 한쪽만 고치면 PyYAML 이 없는 PC 에서 Class 이름이 달라진다.
- Class ID 는 회사 번호 0~6 을 그대로 쓴다. 사용하지 않는 Class 도 지우지 말고 `enabled: false` 로 둔다 (결번이 생기면 기본값으로 돌아간다).
