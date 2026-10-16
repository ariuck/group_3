# `tests/test_manifest_input.py`

> 사람 칸 기록 시험 — `record_save(human=...)` 와 `read_human`. 임시 폴더의 작은 TXT·검수표로 확인한다.

[← 코드 문서 목차](../README.md) · [코드 보기](../../tests/test_manifest_input.py) · 대상: [`src/manifest/manifest_writer`](../src/manifest/manifest_writer.md)

## 실행

```bash
python3 tests/test_manifest_input.py      # subject7 폴더에서
```

## 시험 내용 (`ManifestInputTest`)

| 묶음 | 확인하는 것 |
|---|---|
| 기록·읽기 | 사람 칸 저장 후 다시 읽기 · 자동 칸도 채워짐 · 머리글 유지 · 다시 저장하면 같은 줄 갱신 · 두 사진이 섞이지 않음 · 쉼표·따옴표·줄바꿈 보존 |
| `None` 과 `""` | `human` 없이 저장하면 입력값 유지 · 빠진 키는 그대로, 빈 값은 지움 · 입력으로 자동 칸을 덮어쓸 수 없음 |
| 읽기 | 기록 없는 사진은 빈칸 · 검수표가 아직 없어도 빈칸 |
| 상태 | 사람이 안 고르면 자동 · 사람이 고른 상태 유지 · REVIEW 를 끝냄으로 바꿀 수 있음 · 잘못된 상태는 거부하고 파일 불변 |
| 안전 | 임시 파일이 남지 않음 |
