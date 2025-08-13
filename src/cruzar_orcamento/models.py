# src/cruzar_orcamento/models.py
from __future__ import annotations

from typing import TypedDict, NotRequired, Dict, List


class Item(TypedDict):
    """
    Esquema canônico de um item para cruzamento de valores.
    """
    codigo: str
    descricao: str
    valor_unit: float
    banco: NotRequired[str]
    fonte: str  # ex.: "ORCAMENTO", "SUDECAP", "SINAPI"


# ---------- Estrutura de composições (nível 1) ----------

class ChildSpec(TypedDict):
    """
    Filho imediato de uma composição (pode ser Insumo ou Composição Auxiliar).
    Só guardamos o que será comparado: código e descrição.
    """
    codigo: str
    descricao: str


class CompEstrutura(TypedDict):
    """
    Estrutura de uma composição 'mestra': pai + seus filhos imediatos.
    A comparação de estrutura usará apenas os filhos (código/descrição).
    """
    codigo: str            # código da composição mestra (chave do match)
    descricao: str         # descrição da composição mestra (para exibição)
    filhos: List[ChildSpec]
    fonte: str             # 'ORCAMENTO' | 'SUDECAP' | 'SINAPI' | ...
    banco: NotRequired[str]

# Dicionários canônicos
CanonDict = Dict[str, Item]                    # código -> Item (para valores)
EstruturaDict = Dict[str, CompEstrutura]       # código -> CompEstrutura (para estrutura)

__all__ = [
    "Item",
    "CanonDict",
    "ChildSpec",
    "CompEstrutura",
    "EstruturaDict",
]
