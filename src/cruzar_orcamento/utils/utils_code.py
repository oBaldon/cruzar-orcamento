# src/cruzar_orcamento/utils/utils_code.py
from __future__ import annotations
import math
import re
from typing import Any

def norm_code_canonical(x: Any) -> str:
    """
    Normaliza códigos vindos de Excel/CSV para uma forma canônica:
    - Remove sufixo '.0' quando o valor é inteiro (ex.: '37370.0' -> '37370').
    - Remove zeros à esquerda quando o código é puramente numérico
      (ex.: '00037370' -> '37370', '000000' -> '0').
    - Mantém códigos segmentados com ponto como estão (ex.: '01.12.01' permanece).
    - Converte ints/floats para string; None/NaN -> "".

    Exemplos:
      norm_code_canonical(37370.0)          -> "37370"
      norm_code_canonical("37370.0")        -> "37370"
      norm_code_canonical("00037370")       -> "37370"
      norm_code_canonical("95344.0")        -> "95344"
      norm_code_canonical("01.12.01")       -> "01.12.01"   # preserva segmentação
      norm_code_canonical(None)             -> ""
    """
    # 1) nulos
    if x is None:
        return ""

    # 2) tipos numéricos
    if isinstance(x, int):
        return str(x)

    if isinstance(x, float):
        if math.isnan(x):
            return ""
        # se for inteiro exato, remove '.0'
        if x.is_integer():
            return str(int(x))
        # raro: float com casas != 0 — mantém representação padrão
        return str(x).strip()

    # 3) strings (ou demais tipos -> str)
    s = str(x).strip()
    if not s:
        return ""

    # Se for puramente dígitos com opcional '.0...' no final, normaliza:
    # exemplos válidos: "00037370", "37370.0", "95344.000"
    if re.fullmatch(r"\d+(?:\.0+)?", s):
        s = s.split(".")[0]  # remove sufixo .0...
        s = s.lstrip("0")    # remove zeros à esquerda
        return s or "0"      # se era tudo zero, vira "0"

    # Se tiver pontos (ex.: '01.12.01'), não mexe — evita perder zeros significativos
    # Outras formas mistas (letras, hífens etc.) também são mantidas.
    return s
