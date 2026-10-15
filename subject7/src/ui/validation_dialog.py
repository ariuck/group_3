"""Validation 결과 다이얼로그 (Tkinter Toplevel 창).

데이터셋 무결성 검증 결과(CRITICAL, WARNING, INFO)를 요약 통계와 표(Treeview)로 표시한다.
행을 더블클릭하면 해당 이미지/파일로 이동하는 점프(on_jump) 콜백을 지원한다.
"""
import tkinter as tk
from pathlib import Path
from tkinter import ttk, messagebox


class ValidationDialog(tk.Toplevel):
    def __init__(self, parent, report, csv_path=None, on_jump=None):
        super().__init__(parent)
        self.title("Validation 무결성 검증 결과")
        self.geometry("980x540")
        self.minsize(750, 400)
        self.report = report or []
        self.csv_path = Path(csv_path) if csv_path else None
        self.on_jump = on_jump

        self._build_ui()

    def _build_ui(self):
        # 1. 상단 요약 바
        counts = {s: sum(1 for r in self.report if r.get("severity") == s)
                  for s in ("CRITICAL", "WARNING", "INFO")}
        total_issues = len(self.report)

        top_frame = ttk.Frame(self, padding=(12, 10))
        top_frame.pack(fill="x")

        title_lbl = ttk.Label(
            top_frame,
            text=f"검증 결과 총 {total_issues}건 발견",
            font=("Malgun Gothic", 12, "bold")
        )
        title_lbl.pack(anchor="w")

        summary_text = (
            f"❌ 치명적 오류(CRITICAL): {counts['CRITICAL']}건  |  "
            f"⚠️ 주의(WARNING): {counts['WARNING']}건  |  "
            f"ℹ️ 안내(INFO): {counts['INFO']}건"
        )
        summary_lbl = ttk.Label(top_frame, text=summary_text, font=("Malgun Gothic", 10))
        summary_lbl.pack(anchor="w", pady=(4, 2))

        guide_text = "※ 행을 더블클릭하면 해당 파일로 바로 이동합니다."
        if self.csv_path:
            guide_text += f" (보고서 저장 위치: {self.csv_path.name})"
        guide_lbl = ttk.Label(top_frame, text=guide_text, foreground="#666666", font=("Malgun Gothic", 9))
        guide_lbl.pack(anchor="w")

        # 2. 중앙 결과 목록 (Treeview)
        tree_frame = ttk.Frame(self, padding=(12, 0, 12, 8))
        tree_frame.pack(fill="both", expand=True)

        cols = ("sev", "code", "file", "line", "msg")
        self.tree = ttk.Treeview(tree_frame, columns=cols, show="headings", selectmode="browse")

        col_defs = [
            ("sev", "심각도", 90),
            ("code", "검증 코드", 160),
            ("file", "파일명 / 상대경로", 260),
            ("line", "줄", 45),
            ("msg", "상세 내용", 400),
        ]
        for col_id, heading_text, width in col_defs:
            self.tree.heading(col_id, text=heading_text)
            self.tree.column(col_id, width=width, anchor="w")

        # 스크롤바 연결
        scrollbar_y = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        scrollbar_x = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        scrollbar_y.grid(row=0, column=1, sticky="ns")
        scrollbar_x.grid(row=1, column=0, sticky="ew")

        tree_frame.rowconfigure(0, weight=1)
        tree_frame.columnconfigure(0, weight=1)

        # 데이터 채우기 및 태그 색상 설정
        self.tree.tag_configure("CRITICAL", foreground="#d32f2f")  # 빨강
        self.tree.tag_configure("WARNING", foreground="#e65100")   # 주황
        self.tree.tag_configure("INFO", foreground="#1976d2")      # 파랑

        for r in self.report:
            sev = r.get("severity", "INFO")
            self.tree.insert(
                "",
                "end",
                values=(
                    sev,
                    r.get("code", ""),
                    r.get("relative_path", ""),
                    r.get("line", 0),
                    r.get("message", ""),
                ),
                tags=(sev,)
            )

        self.tree.bind("<Double-1>", self._on_double_click)

        # 3. 하단 버튼 바
        bottom_frame = ttk.Frame(self, padding=(12, 8))
        bottom_frame.pack(fill="x")

        close_btn = ttk.Button(bottom_frame, text="닫기", command=self.destroy, width=10)
        close_btn.pack(side="right")

    def _on_double_click(self, _event):
        sel = self.tree.selection()
        if not sel:
            return
        item_vals = self.tree.item(sel[0], "values")
        rel_file = item_vals[2] if len(item_vals) > 2 else None
        if rel_file and self.on_jump:
            try:
                self.on_jump(rel_file)
            except Exception as e:
                messagebox.showwarning("이동 오류", f"해당 항목으로 이동할 수 없습니다: {e}", parent=self)


def show_validation_dialog(parent, report, csv_path=None, on_jump=None):
    """Validation 다이얼로그 헬퍼 함수."""
    return ValidationDialog(parent, report, csv_path=csv_path, on_jump=on_jump)
