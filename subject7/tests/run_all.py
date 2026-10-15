"""모든 시험을 한 번에 돌린다.   사용: python tests/run_all.py

시험 파일은 두 종류다.
  - 직접 실행하는 것 (day1_selftest.py, test_viewport.py, test_hangul_input.py): 'FAIL' 줄이 있으면 실패
  - unittest 로 도는 것 (나머지 test_*.py)
한글 입력 시험은 창의 포커스 타이밍에 민감해서, 실패하면 최대 3번까지 다시 해 본다.
"""
import subprocess
import sys
from pathlib import Path

TESTS = Path(__file__).resolve().parent
ROOT = TESTS.parent
SCRIPTS = ("day1_selftest.py", "test_viewport.py", "test_hangul_input.py")
RETRY = {"test_hangul_input.py": 3}


def run(cmd):
    r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return r.returncode, r.stdout + r.stderr


def run_script(name):
    code, out = run([sys.executable, str(TESTS / name)])
    fails = sum(1 for line in out.splitlines() if line.startswith("FAIL"))
    passes = sum(1 for line in out.splitlines() if line.startswith("PASS"))
    return code == 0 and fails == 0, f"PASS {passes} / FAIL {fails}", out


def run_unittest(name):
    code, out = run([sys.executable, "-m", "unittest", str(Path("tests") / name)])
    tail = [line for line in out.splitlines() if line.startswith(("Ran", "OK", "FAILED"))]
    return code == 0, " ".join(tail), out


def main():
    failed = []
    names = sorted(p.name for p in TESTS.glob("*.py") if p.name == "day1_selftest.py" or p.name.startswith("test_"))
    for name in names:
        runner = run_script if name in SCRIPTS else run_unittest
        for attempt in range(RETRY.get(name, 1)):
            ok, summary, out = runner(name)
            if ok:
                break
        print(f"{'통과' if ok else '실패'}  {name}: {summary}")
        if not ok:
            failed.append((name, out))
    print()
    if failed:
        print(f"실패 {len(failed)}개: " + ", ".join(n for n, _ in failed))
        for name, out in failed:
            print(f"\n----- {name} -----\n{out[-1500:]}")
        return 1
    print(f"모든 시험 통과 ({len(names)}개 파일)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
