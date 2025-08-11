# src/cruzar_orcamento/models.py
from __future__ import annotations

from typing import TypedDict, NotRequired, Dict


class Item(TypedDict):
    """
    Esquema canônico de um item para cruzamento.
    """
    codigo: str
    descricao: str
    valor_unit: float
    banco: NotRequired[str]
    fonte: str  # ex.: "ORCAMENTO", "SUDECAP", "SINAPI"


# Dicionário canônico: chave = código
CanonDict = Dict[str, Item]

__all__ = ["Item", "CanonDict"]
