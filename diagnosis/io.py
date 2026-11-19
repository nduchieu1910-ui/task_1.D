"""Nap do thi khai niem cua nhom vao bo chan doan.

Quy uoc cua nhom (scripts/init_db.py, B):
    (a:Concept)-[:REQUIRES]->(b:Concept)  nghia la: de hoc a can nam vung b.
    Khoa cua nut la thuoc tinh `concept_id` (vi du "C03_09").

Bo chan doan dung networkx voi canh  tien_quyet -> phu_thuoc,  tuc b -> a.
Moi ham o day deu tra ve do thi theo chieu cua bo chan doan.
"""

from __future__ import annotations

import ast
import csv
from pathlib import Path
from typing import Iterable

import networkx as nx

from .qmatrix import graph_from_requires


def load_concepts(path: str | Path) -> dict[str, dict[str, str]]:
    """Doc data/concepts_v0.csv (cot concept_id, name_vi, name_en, definition, chapter)."""
    with open(path, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    out = {}
    for r in rows:
        cid = r["concept_id"].strip()
        if cid in out:
            raise ValueError(f"concept_id bi trung: {cid}")
        out[cid] = r
    return out


def load_requires_csv(path: str | Path) -> list[tuple[str, str]]:
    """Doc data/edges_v0.csv voi cot src,dst nghia la (src)-[:REQUIRES]->(dst)."""
    with open(path, encoding="utf-8-sig", newline="") as f:
        return [(r["src"].strip(), r["dst"].strip()) for r in csv.DictReader(f)]


def load_requires_from_init_db(path: str | Path = "scripts/init_db.py") -> list[tuple[str, str]]:
    """Lay INITIAL_REQUIRES_EDGES tu scripts/init_db.py ma khong can import file do
    (file do import neo4j). Doc bang ast nen khong chay code nao trong file."""
    tree = ast.parse(Path(path).read_text(encoding="utf-8"))
    for node in tree.body:
        if (isinstance(node, ast.Assign) and len(node.targets) == 1
                and getattr(node.targets[0], "id", None) == "INITIAL_REQUIRES_EDGES"):
            return [tuple(e) for e in ast.literal_eval(node.value)]
    raise ValueError(f"Khong tim thay INITIAL_REQUIRES_EDGES trong {path}")


def build_graph(concept_ids: Iterable[str], requires: Iterable[tuple[str, str]]) -> nx.DiGraph:
    """Tao do thi cho bo chan doan va kiem tra: id ton tai, khong tu vong, khong chu trinh."""
    ids = set(concept_ids)
    requires = list(requires)
    unknown = sorted({x for e in requires for x in e} - ids)
    if unknown:
        raise ValueError(f"Canh tham chieu concept_id khong co trong danh sach: {unknown}")
    loops = [a for a, b in requires if a == b]
    if loops:
        raise ValueError(f"Khai niem tu yeu cau chinh no: {loops}")
    G = graph_from_requires(requires, nodes=sorted(ids))
    if not nx.is_directed_acyclic_graph(G):
        raise ValueError(f"Do thi tien quyet co chu trinh: {nx.find_cycle(G)}")
    return G


def load_graph_from_files(concepts_csv: str | Path = "data/concepts_v0.csv",
                          edges: str | Path = "data/edges_v0.csv") -> tuple[nx.DiGraph, dict]:
    """Tien nhat khi chua bat Neo4j. `edges` co the la edges_v0.csv hoac scripts/init_db.py."""
    concepts = load_concepts(concepts_csv)
    edges = Path(edges)
    pairs = (load_requires_from_init_db(edges) if edges.suffix == ".py"
             else load_requires_csv(edges))
    return build_graph(concepts, pairs), concepts


def load_q_csv(path: str | Path) -> dict[str, dict[str, float]]:
    """Doc Q-matrix dang dai: cot item_id, concept_id, weight (weight tuy chon, mac dinh 1).

    Moi dong la mot cap (cau, khai niem). Mot cau gan 2 khai niem thi co 2 dong.
    """
    Q: dict[str, dict[str, float]] = {}
    with open(path, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        need = {"item_id", "concept_id"}
        if not need <= set(reader.fieldnames or []):
            raise ValueError(f"Q-matrix can cot {sorted(need)}, nhan {reader.fieldnames}")
        for r in reader:
            w = float(r.get("weight") or 1)
            Q.setdefault(r["item_id"].strip(), {})[r["concept_id"].strip()] = w
    return Q


def load_responses_csv(path: str | Path) -> dict[str, dict[str, float]]:
    """Doc bai lam nhieu sinh vien. Nhan 2 dang:
    - dang dai: cot student_id, item_id, score  (moi dong mot cau tra loi)
    - dang rong: cot student_id + moi cau mot cot (o trong = khong lam)
    Tra ve {student_id: {item_id: diem}}.
    """
    with open(path, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        cols = reader.fieldnames or []
        if "student_id" not in cols:
            raise ValueError("File bai lam can cot student_id")
        out: dict[str, dict[str, float]] = {}
        long_form = {"item_id", "score"} <= set(cols)
        for r in reader:
            sid = r["student_id"].strip()
            row = out.setdefault(sid, {})
            if long_form:
                row[r["item_id"].strip()] = float(r["score"])
            else:
                for c in cols:
                    if c != "student_id" and (r[c] or "").strip() != "":
                        row[c] = float(r[c])
    return out


CYPHER_CONCEPTS ="MATCH (c:Concept) RETURN c.concept_id AS id, c.name_vi AS name_vi, c.chapter AS chapter"
CYPHER_REQUIRES = ("MATCH (a:Concept)-[:REQUIRES]->(b:Concept) "
                   "RETURN a.concept_id AS src, b.concept_id AS dst")


def load_graph_from_neo4j(driver, database: str | None = None) -> tuple[nx.DiGraph, dict]:
    """Doc tu Neo4j dang chay (docker compose up). `driver` = neo4j.GraphDatabase.driver(...)."""
    with driver.session(database=database) as s:
        concepts = {r["id"]: dict(r) for r in s.run(CYPHER_CONCEPTS)}
        pairs = [(r["src"], r["dst"]) for r in s.run(CYPHER_REQUIRES)]
    return build_graph(concepts, pairs), concepts
