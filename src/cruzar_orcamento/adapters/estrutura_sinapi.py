# src/cruzar_orcamento/adapters/estrutura_sinapi.py
from __future__ import annotations

import logging
from typing import Optional
import pandas as pd

from ..models import CompEstrutura, ChildSpec, EstruturaDict
from ..utils.utils_code import norm_code_canonical  # <- normaliza códigos ('.0', zeros à esquerda)

logger = logging.getLogger(__name__)

def _strip(v) -> str:
    if pd.isna(v):
        return ""
    return str(v).strip()

def _find_header_row(df_raw: pd.DataFrame, max_scan: int = 25) -> Optional[int]:
    """
    Tenta localizar o cabeçalho procurando por 'Descrição' em alguma coluna.
    Se não achar, retorna None (leitura posicional).
    """
    for i in range(min(max_scan, len(df_raw))):
        row = df_raw.iloc[i].astype(str).str.lower()
        if row.str.contains("descri", regex=False).any():
            return i
    return None

def load_estrutura_sinapi_analitico(path: str, sheet_name: str = "Analítico") -> EstruturaDict:
    """
    Lê a aba 'Analítico' do SINAPI e constrói:
      { codigo_pai: {codigo, descricao, filhos:[{codigo, descricao}], fonte:'SINAPI'} }

    Convenção:
      - Código do PAI   → coluna B (idx 1)
      - Tipo (INSUMO/COMPOSICAO) → coluna C (idx 2)
      - Código do FILHO → coluna D (idx 3)
    Descrição: tenta localizar por nome via header; se não houver, usa posicional (coluna E, idx 4) como fallback.
    """
    # 1) tenta detectar header para descobrir a coluna de descrição por nome
    df_raw = pd.read_excel(path, sheet_name=sheet_name, header=None)
    header_row = _find_header_row(df_raw)
    desc_col = None

    if header_row is not None:
        df = pd.read_excel(path, sheet_name=sheet_name, header=header_row)
        cols_lower = {str(c).strip().lower(): c for c in df.columns}
        for k, real in cols_lower.items():
            if "descri" in k:
                desc_col = real
                break
        if desc_col is None:
            logger.warning("[SINAPI Analítico] Coluna de descrição não localizada pelo header; usando posicional.")
            df = df_raw.copy()
            header_row = None
    else:
        df = df_raw.copy()

    # 2) helpers de leitura
    def get_desc(row) -> str:
        if (header_row is not None) and (desc_col is not None):
            return _strip(row.get(desc_col))
        # fallback: coluna E (idx 4) costuma ser a descrição do item/linha
        try:
            return _strip(row.iloc[4])
        except Exception:
            return ""

    out: EstruturaDict = {}
    pai_atual: Optional[CompEstrutura] = None
    total_filhos = 0
    pais_duplicados = 0

    # 3) Varredura linha a linha
    for idx, row in df.iterrows():
        try:
            raw_pai = _strip(row.iloc[1])   # B
        except Exception:
            raw_pai = ""
        try:
            tipo = _strip(row.iloc[2]).casefold()   # C
        except Exception:
            tipo = ""
        try:
            raw_filho = _strip(row.iloc[3])  # D
        except Exception:
            raw_filho = ""

        # normalização de códigos (remove '.0', zeros à esquerda para numéricos puros)
        cod_pai = norm_code_canonical(raw_pai) if raw_pai else ""
        cod_filho = norm_code_canonical(raw_filho) if raw_filho else ""

        # pula linha vazia
        if not cod_pai and not cod_filho and not tipo:
            continue

        # Sempre que aparecer um novo código (coluna B), iniciamos/continuamos um pai
        if cod_pai:
            if (pai_atual is None) or (pai_atual["codigo"] != cod_pai):
                # fecha o anterior
                if pai_atual is not None:
                    if pai_atual["codigo"] in out:
                        pais_duplicados += 1
                        logger.warning(
                            "[SINAPI Analítico] Código de composição duplicado: %r "
                            "(substituindo '%s' → '%s')",
                            pai_atual["codigo"], out[pai_atual["codigo"]]["descricao"], pai_atual["descricao"]
                        )
                    out[pai_atual["codigo"]] = pai_atual

                # inicia novo pai
                pai_atual = CompEstrutura(
                    codigo=cod_pai,
                    descricao=get_desc(row),   # descrição exibida para o pai (se disponível nessa linha)
                    filhos=[],
                    fonte="SINAPI",
                )

        # Se há pai atual e a coluna D (filho) está preenchida, registra filho
        # quando tipo for INSUMO/COMPOSICAO (aceita 'composição' com acento)
        if pai_atual and cod_filho and (("insumo" in tipo) or ("composicao" in tipo) or ("composição" in tipo)):
            filho_desc = get_desc(row)
            filho: ChildSpec = {"codigo": cod_filho, "descricao": filho_desc}
            pai_atual["filhos"].append(filho)
            total_filhos += 1

    # fecha o último pai
    if pai_atual:
        if pai_atual["codigo"] in out:
            pais_duplicados += 1
            logger.warning(
                "[SINAPI Analítico] Código de composição duplicado: %r "
                "(substituindo '%s' → '%s')",
                pai_atual["codigo"], out[pai_atual["codigo"]]["descricao"], pai_atual["descricao"]
            )
        out[pai_atual["codigo"]] = pai_atual

    logger.info(
        "[SINAPI Analítico] Estrutura construída: %d composição(ões) com %d filho(s) no total. Duplicados de pai: %d.",
        len(out), total_filhos, pais_duplicados
    )
    return out
