# src/cruzar_orcamento/validators/estrutura_compare.py
from __future__ import annotations

from typing import Dict, List, TypedDict, Optional
from ..models import EstruturaDict, CompEstrutura
from ..utils.utils_text import norm_text            # já existe no projeto
from ..utils.utils_code import norm_code_canonical  # normaliza códigos (remove '.0' e zeros à esquerda)

class ChildDiffDesc(TypedDict):
    codigo: str
    a_desc: str
    b_desc: str

class DivergenciaEstrutura(TypedDict):
    pai_codigo: str
    pai_desc_a: Optional[str]
    pai_desc_b: Optional[str]
    filhos_missing: List[str]        # filhos que estão em A mas não em B (por código)
    filhos_extra: List[str]          # filhos que estão em B mas não em A (por código)
    filhos_desc_mismatch: List[ChildDiffDesc]  # mesmo código, mas descrições diferentes

def _index_children(comp: CompEstrutura) -> Dict[str, str]:
    """
    Indexa filhos por código normalizado -> descrição (primeiro nível).
    Usa norm_code_canonical para resolver '.0' e zeros à esquerda.
    """
    out: Dict[str, str] = {}
    for ch in comp.get("filhos", []):
        raw_code = str(ch.get("codigo", "")).strip()
        code = norm_code_canonical(raw_code)
        out[code] = str(ch.get("descricao", "")).strip()
    return out

def comparar_estruturas(A: EstruturaDict, B: EstruturaDict) -> List[DivergenciaEstrutura]:
    """
    Compara A (ex.: ORÇAMENTO) com B (ex.: SINAPI/SUDECAP) no nível 1:
    - Para cada pai presente em A, procura o mesmo pai em B (chaves de A/B já devem estar normalizadas pelos adapters).
    - Compara o CONJUNTO de códigos de filhos (normalizados).
    - Para códigos em comum, compara descrição com normalização (casefold+sem acento).
    """
    diverg: List[DivergenciaEstrutura] = []

    for pai_cod, comp_a in A.items():
        comp_b = B.get(pai_cod)
        filhos_missing: List[str] = []
        filhos_extra: List[str] = []
        filhos_desc_mismatch: List[ChildDiffDesc] = []

        if comp_b is None:
            # Pai inexistente em B
            filhos_missing = sorted(_index_children(comp_a).keys())
            diverg.append(DivergenciaEstrutura(
                pai_codigo=pai_cod,
                pai_desc_a=comp_a.get("descricao"),
                pai_desc_b=None,
                filhos_missing=filhos_missing,
                filhos_extra=[],
                filhos_desc_mismatch=[],
            ))
            continue

        idx_a = _index_children(comp_a)
        idx_b = _index_children(comp_b)

        set_a = set(idx_a.keys())
        set_b = set(idx_b.keys())

        # diferença de conjunto
        filhos_missing = sorted(set_a - set_b)  # em A e faltam em B
        filhos_extra   = sorted(set_b - set_a)  # em B e faltam em A

        # interseção: checar descrição (normalizada)
        inter = sorted(set_a & set_b)
        for code in inter:
            da = idx_a[code]
            db = idx_b[code]
            if norm_text(da) != norm_text(db):
                filhos_desc_mismatch.append(ChildDiffDesc(
                    codigo=code, a_desc=da, b_desc=db
                ))

        if filhos_missing or filhos_extra or filhos_desc_mismatch:
            diverg.append(DivergenciaEstrutura(
                pai_codigo=pai_cod,
                pai_desc_a=comp_a.get("descricao"),
                pai_desc_b=comp_b.get("descricao"),
                filhos_missing=filhos_missing,
                filhos_extra=filhos_extra,
                filhos_desc_mismatch=filhos_desc_mismatch,
            ))

    return diverg
