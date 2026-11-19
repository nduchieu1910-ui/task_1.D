"""Ket luan tong cho mot sinh vien (dong dau tien nguoi dung doc tren giao dien)."""

from __future__ import annotations

from typing import Any


def overall_verdict(res: dict[str, Any], concepts: dict | None = None) -> dict[str, Any]:
    """Tra ve {'level': 'ok'|'weak', 'title': ..., 'detail': ...}.

    'ok'  : khong co khai niem nao chua vung (trong so khai niem co cau hoi).
    'weak': co khai niem chua vung -> neu nut goc can hoc truoc.
    """
    name = (lambda c: concepts.get(c, {}).get("name_vi", "")) if concepts else (lambda c: "")
    observed = len(res["mastery"]) - len(res.get("unobserved", ()))
    n_weak = len(res["weak"])
    if n_weak == 0:
        return {
            "level": "ok",
            "title": f"Sinh viên VỮNG tất cả {observed} khái niệm đã kiểm tra.",
            "detail": "Không phát hiện lỗ hổng gốc." + (
                f" {len(res['unobserved'])} khái niệm chưa có câu hỏi nên chưa kết luận."
                if res.get("unobserved") else ""),
        }
    roots = res["roots"]
    first = roots[0] if roots else None
    roots_txt = "; ".join(f"{r} {name(r)}".strip() for r in roots)
    return {
        "level": "weak",
        "title": f"Sinh viên CHƯA VỮNG {n_weak}/{observed} khái niệm đã kiểm tra.",
        "detail": (f"Lỗ hổng gốc ({len(roots)}): {roots_txt}. "
                   + (f"Nên học lại {first} trước: nó giải thích "
                      f"{len(res['evidence'][first]['explains'])} khái niệm yếu khác." if first else "")),
    }
