from __future__ import annotations
from datetime import date
from ..base import FetchPlan

_BASE = ("https://prefeitura.pbh.gov.br/sites/default/files/"
         "estrutura-de-governo/obras-e-infraestrutura")

def sudecap_url_builder(d: date) -> str:
    # Ex.: 2025.04-tabela-de-construcao-desonerada.xls
    return f"{_BASE}/{d.year:04d}.{d.month:02d}-tabela-de-construcao-desonerada.xls"

SUDECAP_PLAN = FetchPlan(
    name="SUDECAP",
    url_builder=sudecap_url_builder,
    file_pattern="SUDECAP_{YYYY}_{MM}.xls",
    out_dir="data",
)
