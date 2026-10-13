# `tests/run_all.py`

> 모든 시험을 한 번에 돌리는 실행기. 약 1분 걸린다.

[← 코드 문서 목차](../README.md) · [코드 보기](../../../tests/run_all.py)

## 사용법

```bash
python tests/run_all.py
```

## 동작

시험 파일은 두 종류다.

| 종류 | 파일 | 실패 판정 |
|---|---|---|
| 직접 실행하는 것 | [`day1_selftest`](day1_selftest.md), [`test_viewport`](test_viewport.md), [`test_hangul_input`](test_hangul_input.md) | 출력에 `FAIL` 줄이 있으면 실패 |
| unittest | 나머지 `test_*.py` | unittest 결과 |

[`test_hangul_input`](test_hangul_input.md) 은 창 포커스 타이밍에 민감해서 실패하면 **최대 3번까지 다시** 돌린다.

| 함수 | 설명 |
|---|---|
| `run(cmd)` | 하위 프로세스 실행 |
| `run_script(name)` | 직접 실행형 시험 |
| `run_unittest(name)` | unittest 형 시험 |
| `main()` | 전체 실행 후 요약, 실패가 있으면 종료 코드 1 |

## 주의사항

- 화면(Tk)이 필요한 시험이 섞여 있어 디스플레이가 없는 환경(CI 등)에서는 일부가 실패한다.
- 새 시험 파일을 직접 실행형으로 만들었다면 이 파일의 목록에도 추가해야 한다.
