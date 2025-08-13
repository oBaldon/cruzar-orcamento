from __future__ import annotations

from typing import List, Dict, Any
import pandas as pd
import os

from ..validators.estrutura_compare import DivergenciaEstrutura, ChildDiffDesc


def export_estrutura_divergencias_excel(divs: List[DivergenciaEstrutura], path: str) -> None:
    """
    Gera um Excel com uma aba 'diverg_estrutura' no formato tabular:
    - pai_codigo, pai_desc_a, pai_desc_b
    - tipo: MISSING | EXTRA | DESC_DIF
    - filho_codigo
    - a_desc, b_desc (preenchidos conforme o tipo)
    """
    rows: List[Dict[str, Any]] = []

    for d in divs:
        pai = d["pai_codigo"]
        pda = d.get("pai_desc_a") or ""
        pdb = d.get("pai_desc_b") or ""

        for code in d["filhos_missing"]:
            rows.append({
                "pai_codigo": pai,
                "pai_desc_a": pda,
                "pai_desc_b": pdb,
                "tipo": "MISSING",             # A tem, B não tem
                "filho_codigo": code,
                "a_desc": "",                  # descrição do filho em A não veio no diff de conjunto
                "b_desc": "",
            })

        for code in d["filhos_extra"]:
            rows.append({
                "pai_codigo": pai,
                "pai_desc_a": pda,
                "pai_desc_b": pdb,
                "tipo": "EXTRA",               # B tem, A não tem
                "filho_codigo": code,
                "a_desc": "",
                "b_desc": "",
            })

        for mm in d["filhos_desc_mismatch"]:
            rows.append({
                "pai_codigo": pai,
                "pai_desc_a": pda,
                "pai_desc_b": pdb,
                "tipo": "DESC_DIF",            # mesmo código, descrições divergem
                "filho_codigo": mm["codigo"],
                "a_desc": mm["a_desc"],
                "b_desc": mm["b_desc"],
            })

    df = pd.DataFrame(rows, columns=[
        "pai_codigo", "pai_desc_a", "pai_desc_b",
        "tipo", "filho_codigo", "a_desc", "b_desc"
    ])

    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with pd.ExcelWriter(path, engine="openpyxl") as xw:
        df.to_excel(xw, sheet_name="diverg_estrutura", index=False)
