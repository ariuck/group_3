"""코드 ↔ 문서 1:1 대응 점검. 모든 .py 에 docs/<같은 경로>.md 가 있는지, 코드가 사라진 문서는 없는지 확인한다.

    python tools/check_docs.py              # subject7 점검. 문제가 있으면 목록을 보여 주고 종료 코드 1
    python tools/check_docs.py ../subject8  # 다른 과목 폴더도 같은 규칙으로 점검

규칙:  src/ui/tooltip.py  →  docs/src/ui/tooltip.md   (과목 폴더 기준, 코드와 같은 경로)
내용이 없는 __init__.py 는 문서를 만들지 않는다. 문서 내용이 코드와 맞는지는 사람이 확인한다.
docs/ 에는 주제별 문서(standards/, design/ …)도 함께 있으므로, '코드 없는 문서'는 코드가 있는 폴더
(src/, tools/, tests/, scripts/ …)와 같은 이름의 docs 하위 폴더 안에서만 찾는다.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKIP_DIRS = {".git", ".venv", "venv", "__pycache__", ".pytest_cache", "data", "docs", "runs", ".vscode", ".idea"}


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


def _has_source(root, doc_rel):
    """문서와 같은 경로·같은 이름의 원본 파일이 있는가 (.py 뿐 아니라 설정 파일 .yaml 등도 인정)"""
    folder = Path(root) / doc_rel.parent
    return folder.is_dir() and any(p.is_file() and p.stem == doc_rel.stem and p.suffix != ".md"
                                   for p in folder.iterdir())


def check(root=ROOT):
    """(코드 목록, 문서가 없는 코드, 코드가 없는 문서) — 모두 과목 폴더 기준 상대 경로"""
    root = Path(root)
    docs = root / "docs"
    codes = code_files(root)
    missing = [c for c in codes if not (docs / c.with_suffix(".md")).is_file()]
    code_dirs = {c.parts[0] for c in codes if len(c.parts) > 1}         # src, tools, tests, scripts …
    orphans = [d.relative_to(docs) for top in sorted(code_dirs) for d in sorted((docs / top).rglob("*.md"))
               if not _has_source(root, d.relative_to(docs))]
    return codes, missing, orphans


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    root = Path(argv[0]).resolve() if argv else ROOT
    codes, missing, orphans = check(root)
    for c in missing:
        print(f"문서 없음      : {c.as_posix()}  →  docs/{c.with_suffix('.md').as_posix()}")
    for d in orphans:
        print(f"코드 없는 문서 : docs/{d.as_posix()}")
    print(f"[{root.name}] 점검 완료: 코드 {len(codes)}개 · 문서 없음 {len(missing)}개 · 코드 없는 문서 {len(orphans)}개")
    return 1 if missing or orphans else 0


if __name__ == "__main__":
    sys.exit(main())
