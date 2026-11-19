"""In ket qua chan doan thanh van ban tieng Viet (dung cho demo va GV cham)."""

from __future__ import annotations

from typing import Any


def _name(cid: str, concepts: dict | None) -> str:
    if concepts and cid in concepts:
        return f"{cid} {concepts[cid].get('name_vi', '')}".strip()
    return cid


def format_report(res: dict[str, Any], concepts: dict | None = None, max_paths: int = 5) -> str:
    lines = []
    weak = sorted(res["weak"])
    lines.append(f"Số khái niệm chưa vững: {len(weak)}"
                 f" | chưa có câu hỏi: {len(res.get('unobserved', ()))}")
    if not res["roots"]:
        lines.append("Không phát hiện lỗ hổng gốc.")
        return "\n".join(lines)
    lines.append("")
    lines.append("LỖ HỔNG GỐC (ưu tiên học trước):")
    for rank, r in enumerate(res["roots"], 1):
        ev = res["evidence"][r]
        lines.append(f"{rank}. {_name(r, concepts)}  (mức thành thạo {ev['mastery']:.2f})")
        if ev["wrong_items"]:
            lines.append(f"   Câu làm sai: {', '.join(ev['wrong_items'])}")
        if ev["prerequisites_mastered"]:
            lines.append(f"   Tiên quyết đã vững: {', '.join(ev['prerequisites_mastered'])}")
        if ev["explains"]:
            lines.append(f"   Giải thích {len(ev['explains'])} khái niệm yếu khác, ví dụ:")
            for c in ev["explains"][:max_paths]:
                lines.append("     " + " -> ".join(ev["paths"][c]))
    return "\n".join(lines)
