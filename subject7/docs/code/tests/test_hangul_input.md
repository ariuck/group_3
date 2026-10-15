# `tests/test_hangul_input.py`

> 한글 조합기 점검. 실제 Tk 입력칸에 키 이벤트를 보내 영문 자판 → 한글 조합을 확인한다.

[← 코드 문서 목차](../README.md) · [코드 보기](../../../tests/test_hangul_input.py) · 대상: [`src/ui/hangul_input`](../src/ui/hangul_input.md)

## 실행

```bash
python tests/test_hangul_input.py        # 직접 실행형, 화면(Tk) 필요. OK / FAIL 출력
```

## 점검 항목

| 묶음 | 내용 |
|---|---|
| 조합 (`compose`) | 여러 입력 → 기대 한글 |
| 입력칸 | 영어 상태는 그대로 · `Shift+Space` 로 한글 · `검수자` 입력 · Backspace 한 단계 · 조합이 끝나면 보통 지우기 · 공백·숫자 그대로 · 한/영 키로 영어 |
| Shift | Shift 를 먼저 눌러도 이어서 조합(`혜성`) · 쌍자음(`까치`) · 조합 중 Shift·CapsLock 만 눌러도 유지 |
| 한/영 키 | 눌렀다 떼면 한 번만 · 꾹 눌러 되풀이는 한 번 · 떼는 신호가 없어도 누를 때마다 · 떼는 신호만 와도 · 오른쪽 Alt 도 같음 · 입력칸이 아닌 곳에서도 · 입력칸에서 두 번 바뀌지 않음 |

## 주의사항

- WSL 창의 포커스 타이밍 때문에 간혹 실패한다. [`run_all`](run_all.md) 은 최대 3번 다시 돌린다.
