# src/cruzar_orcamento/processor_estrutura.py
from __future__ import annotations

from typing import TypedDict, List, Dict, Tuple
from .models import EstruturaDict, CompEstrutura, ChildSpec
from .utils.utils_text import norm_text


class EstruturaMismatch(TypedDict):
    """Divergências para um pai específico."""
    codigo_pai: str
    desc_pai_a: str
    desc_pai_b: str
    # diferenças de conjunto (apenas código)
    filhos_faltando_na_base: List[str]  # presentes no A (orc) mas ausentes no B (base)
    filhos_sobrando_na_base: List[str]  # presentes no B mas ausentes no A
    # diferenças de descrição (mesmos códigos em ambos)
    desc_divergentes: List[Tuple[str, str, str]]  # (codigo, desc_A, desc_B)


def _index_filhos(filhos: List[ChildSpec]) -> Dict[str, str]:
    """Mapeia codigo -> descricao (última ocorrência vence; ordem não importa)."""
    out: Dict[str, str] = {}
    for f in filhos:
        out[f["codigo"]] = f["descricao"]
    return out


def comparar_estruturas(
    estrutura_a: EstruturaDict,
    estrutura_b: EstruturaDict,
) -> List[EstruturaMismatch]:
    """
    Compara estruturas (nível 1: filhos diretos) do ORÇAMENTO (A) contra a BASE (B).

    Regras:
      - Para cada pai em A:
         * se pai não existir em B -> conta como "faltando_na_base" TUDO? Não.
           **Aqui** só reportamos como "filhos_faltando_na_base" = todos os filhos de A,
           e "filhos_sobrando_na_base" = [] (já que B não tem nada).
         * se existir em B: comparamos conjuntos de filhos por CÓDIGO.
           - faltando_na_base: filhos de A que não estão em B
           - sobrando_na_base: filhos de B que não estão em A
           - para códigos em comum: comparar descrição normalizada; se difere, entra em desc_divergentes
    """
    divergencias: List[EstruturaMismatch] = []

    for cod_pai, comp_a in estrutura_a.items():
        comp_b: CompEstrutura | None = estrutura_b.get(cod_pai)
        filhos_a = _index_filhos(comp_a["filhos"])

        if comp_b is None:
            # Pai não existe na base: tudo que A possui aparece como "faltando_na_base"
            mismatch = EstruturaMismatch(
                codigo_pai=cod_pai,
                desc_pai_a=comp_a["descricao"],
                desc_pai_b="",
                filhos_faltando_na_base=sorted(filhos_a.keys()),
                filhos_sobrando_na_base=[],
                desc_divergentes=[],
            )
            divergencias.append(mismatch)
            continue

        filhos_b = _index_filhos(comp_b["filhos"])

        set_a = set(filhos_a.keys())
        set_b = set(filhos_b.keys())

        faltando_na_base = sorted(set_a - set_b)
        sobrando_na_base = sorted(set_b - set_a)

        # comuns: checar descrição (normalizada)
        desc_div: List[Tuple[str, str, str]] = []
        for cod in sorted(set_a & set_b):
            da = filhos_a[cod]
            db = filhos_b[cod]
            if norm_text(da) != norm_text(db):
                desc_div.append((cod, da, db))

        if faltando_na_base or sobrando_na_base or desc_div:
            divergencias.append(EstruturaMismatch(
                codigo_pai=cod_pai,
                desc_pai_a=comp_a["descricao"],
                desc_pai_b=comp_b["descricao"],
                filhos_faltando_na_base=faltando_na_base,
                filhos_sobrando_na_base=sobrando_na_base,
                desc_divergentes=desc_div,
            ))

    return divergencias
