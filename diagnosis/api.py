"""Giao dien chung cho moi bo chan doan (M1 o day; M2, M3 o 2.4 dung cung giao dien).

    diagnose(responses, Q, G) -> {
        "mastery":    {concept: float},       # trung binh hau nghiem, 0..1
        "weak":       set[str],                # chua vung
        "roots":      list[str],               # nut goc, da xep uu tien
        "evidence":   {root: {...}},           # dau vet bang chung cho moi nut goc
        "unobserved": set[str],                # (them) khai niem khong co cau nao
        "details":    {concept: {...}},        # (them) alpha, beta, p_mastered...
    }
"""

from __future__ import annotations

from typing import Any, Mapping

import networkx as nx

from .m1 import M1Params, estimate_mastery
from .qmatrix import check_graph, to_qdict
from .roots import PrereqMode, explained_by, find_roots, rank_roots

WRONG_BELOW = 0.5  # diem < 0.5 duoc coi la "lam sai" khi liet ke bang chung


def diagnose(
    responses: Mapping[str, object],
    Q: object,
    G: nx.DiGraph,
    params: M1Params | None = None,
    mode: PrereqMode = "direct",
) -> dict[str, Any]:
    """Chan doan mot sinh vien.

    responses: {item_id: diem 0..1}; None/NaN = khong lam.
    Q:         DataFrame (cau x khai niem) hoac {item: {concept: weight}}.
    G:         DiGraph, canh A -> B nghia la A la tien quyet cua B.
    """
    params = params or M1Params()
    q = to_qdict(Q)
    check_graph(G, q)
    concepts = list(G.nodes)

    est = estimate_mastery(responses, q, concepts, params)
    observed = {c for c, e in est.items() if e.weight > params.min_weight}
    unobserved = set(concepts) - observed
    mastery = {c: est[c].mean for c in concepts}
    weak = {c for c in observed if mastery[c] < params.threshold}

    roots = rank_roots(G, find_roots(G, weak, mode), weak, mastery)

    items_of: dict[str, list[str]] = {c: [] for c in concepts}
    for item, row in q.items():
        for c in row:
            items_of[c].append(item)

    def wrong_items(c: str) -> list[str]:
        out = []
        for i in items_of[c]:
            v = responses.get(i)
            try:
                if v is not None and float(v) < WRONG_BELOW:
                    out.append(i)
            except (TypeError, ValueError):
                pass
        return sorted(out)

    evidence = {}
    for r in roots:
        paths = explained_by(G, r, weak)
        evidence[r] = {
            "mastery": round(mastery[r], 4),
            "wrong_items": wrong_items(r),
            "explains": sorted(paths),
            "paths": {c: p for c, p in sorted(paths.items())},
            "downstream_wrong_items": {c: wrong_items(c) for c in sorted(paths)},
            "prerequisites_mastered": sorted(G.predecessors(r)),
        }

    details = {
        c: {
            "alpha": est[c].alpha,
            "beta": est[c].beta,
            "evidence_weight": est[c].weight,
            "n_items": est[c].n_items,
            "p_mastered": est[c].p_mastered(params.threshold),
        }
        for c in concepts
    }
    return {
        "mastery": mastery,
        "weak": weak,
        "roots": roots,
        "evidence": evidence,
        "unobserved": unobserved,
        "details": details,
    }


def diagnose_batch(
    responses_by_student: Mapping[str, Mapping[str, object]] | Any,
    Q: object,
    G: nx.DiGraph,
    params: M1Params | None = None,
    mode: PrereqMode = "direct",
) -> dict[str, dict[str, Any]]:
    """Nhieu sinh vien: dict {student: {item: diem}} hoac DataFrame (hang = SV, cot = cau)."""
    if hasattr(responses_by_student, "iterrows"):
        rows = {str(s): r.to_dict() for s, r in responses_by_student.iterrows()}
    else:
        rows = dict(responses_by_student)
    return {s: diagnose(r, Q, G, params, mode) for s, r in rows.items()}
