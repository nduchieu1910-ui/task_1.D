"""M1: muc thanh thao theo Beta-Binomial co trong so.

Voi moi khai niem c, moi cau hoi i gan voi c (trong Q-matrix, trong so w_ic > 0)
va diem s_i trong [0, 1]:

    alpha_c = a0 + sum_i w_ic * s_i
    beta_c  = b0 + sum_i w_ic * (1 - s_i)
    mastery_c = alpha_c / (alpha_c + beta_c)        (trung binh hau nghiem)
    p_mastered_c = P(theta_c >= threshold)          (dung cho ROC o GD3)

Khai niem khong co cau hoi nao duoc tra loi -> "unobserved": khong ket luan yeu.
(Neu khong tach rieng, prior Beta(1,1) cho mastery = 0.5 < 0.6 va moi khai niem
chua kiem tra deu bi gan nham la yeu.)
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Mapping

from scipy.stats import beta as beta_dist

from .qmatrix import QDict


@dataclass(frozen=True)
class M1Params:
    threshold: float = 0.6     # nguong "vung"; se chon lai bang ROC o GD3
    prior_alpha: float = 1.0   # a0
    prior_beta: float = 1.0    # b0
    min_weight: float = 0.0    # tong trong so toi thieu de coi la "da quan sat"
    normalize_rows: bool = False  # True: chia deu trong so moi cau cho cac khai niem

    def __post_init__(self) -> None:
        if not 0.0 < self.threshold < 1.0:
            raise ValueError("threshold phai nam trong (0, 1)")
        if self.prior_alpha <= 0 or self.prior_beta <= 0:
            raise ValueError("prior_alpha, prior_beta phai > 0")


@dataclass(frozen=True)
class ConceptEstimate:
    alpha: float
    beta: float
    weight: float          # tong trong so bang chung (0 = chua quan sat)
    n_items: int

    @property
    def mean(self) -> float:
        return self.alpha / (self.alpha + self.beta)

    def p_mastered(self, threshold: float) -> float:
        return float(beta_dist.sf(threshold, self.alpha, self.beta))


def _clean_score(item: str, value: object) -> float | None:
    if value is None:
        return None
    try:
        x = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Diem cua cau {item!r} khong phai so: {value!r}") from exc
    if math.isnan(x):
        return None  # bo trong = khong lam cau nay
    if not 0.0 <= x <= 1.0:
        raise ValueError(f"Diem cua cau {item!r} phai trong [0, 1], nhan {x}")
    return x


def estimate_mastery(
    responses: Mapping[str, object],
    Q: QDict,
    concepts: list[str],
    params: M1Params,
) -> dict[str, ConceptEstimate]:
    acc = {c: [params.prior_alpha, params.prior_beta, 0.0, 0] for c in concepts}
    for item, raw in responses.items():
        s = _clean_score(item, raw)
        if s is None:
            continue
        if item not in Q:
            raise KeyError(f"Cau {item!r} co trong responses nhung khong co trong Q-matrix")
        row = Q[item]
        total = sum(row.values()) if params.normalize_rows else 1.0
        for c, w in row.items():
            w = w / total
            a = acc[c]
            a[0] += w * s
            a[1] += w * (1.0 - s)
            a[2] += w
            a[3] += 1
    return {c: ConceptEstimate(a, b, wt, n) for c, (a, b, wt, n) in acc.items()}
