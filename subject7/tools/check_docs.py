"""코드 ↔ 문서 1:1 대응 점검. 모든 .py 에 docs/code/<같은 경로>.md 가 있는지, 코드가 사라진 문서는 없는지 확인한다.

    python tools/check_docs.py        # 문제가 있으면 목록을 보여 주고 종료 코드 1

규칙:  src/ui/tooltip.py  →  docs/code/src/ui/tooltip.md
내용이 없는 __init__.py 는 문서를 만들지 않는다. 문서 내용이 코드와 맞는지는 사람이 확인한다.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs" / "code"
INDEX = DOCS / "README.md"
SKIP_DIRS = {".git", ".venv", "venv", "__pycache__", ".pytest_cache", "data", "docs", ".vscode", ".idea"}


def code_files(root=ROOT):
    """문서가 있어야 하는 .py 의 상대 경로 목록"""
    out = []
    for p in sorted(Path(root).rglob("*.py")):
        rel = p.relative_to(root)
        if SKIP_DIRS & set(rel.parts[:-1]):
            continue
        if p.name == "__init__.py" and not p.read_text(encoding="utf-8").strip():
            continue
        out.append(rel)
    return out


def check(root=ROOT, docs=DOCS):
    """(문서가 없는 코드, 코드가 없는 문서) — 둘 다 상대 경로 목록"""
    codes = code_files(root)
    missing = [c for c in codes if not (Path(docs) / c.with_suffix(".md")).is_file()]
    orphans = [d.relative_to(docs) for d in sorted(Path(docs).rglob("*.md"))
               if d != Path(docs) / INDEX.name and not (Path(root) / d.relative_to(docs).with_suffix(".py")).is_file()]
    return codes, missing, orphans


def main():
    codes, missing, orphans = check()
    for c in missing:
        print(f"문서 없음      : {c.as_posix()}  →  docs/code/{c.with_suffix('.md').as_posix()}")
    for d in orphans:
        print(f"코드 없는 문서 : docs/code/{d.as_posix()}")
    print(f"점검 완료: 코드 {len(codes)}개 · 문서 없음 {len(missing)}개 · 코드 없는 문서 {len(orphans)}개")
    return 1 if missing or orphans else 0


if __name__ == "__main__":
    sys.exit(main())
