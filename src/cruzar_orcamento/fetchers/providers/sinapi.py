from __future__ import annotations
import shutil
import os
import unicodedata
import tempfile
from datetime import date
from zipfile import ZipFile

from ..base import FetchPlan, find_latest_available, _fmt_file
from ..http import download_file

_BASE = "https://www.caixa.gov.br/Downloads/sinapi-relatorios-mensais"

def _strip_accents(s: str) -> str:
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()

def sinapi_zip_url_builder(d: date) -> str:
    # Ex.: SINAPI-2025-06-formato-xlsx.zip
    return f"{_BASE}/SINAPI-{d.year:04d}-{d.month:02d}-formato-xlsx.zip"

SINAPI_ZIP_PLAN = FetchPlan(
    name="SINAPI-ZIP",
    url_builder=sinapi_zip_url_builder,
    file_pattern="SINAPI_{YYYY}_{MM}.zip",  # só para dar nome ao zip local se necessário
    out_dir="data",
)

def _wanted_inner_name(d: date) -> str:
    # Nome que normalmente vem dentro do ZIP
    # Atenção: tem acento no 'Referência'
    return f"SINAPI_Referência_{d.year:04d}_{d.month:02d}.xlsx"

def _matches_target(member_name: str, target: str) -> bool:
    # Casa tanto com acento quanto sem acento; compara só o nome (sem diretórios)
    m_base = os.path.basename(member_name)
    if m_base == target:
        return True
    # fallback sem acentos
    return _strip_accents(m_base) == _strip_accents(target)

def fetch_latest_sinapi_referencia_xlsx(start: date, max_months_back: int = 36) -> str:
    """
    Busca retroativamente o ZIP do SINAPI e extrai apenas o
    'SINAPI_Referência_{YYYY}_{MM}.xlsx' para a pasta 'data/'.
    Retorna o caminho do .xlsx extraído.
    """
    # 1) descobrir mês/URL disponíveis
    d, url = find_latest_available(SINAPI_ZIP_PLAN, start, max_months_back=max_months_back)

    os.makedirs(SINAPI_ZIP_PLAN.out_dir, exist_ok=True)

    # 2) baixar o ZIP e 3) abrir/extrair ainda dentro do tempdir
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_zip = os.path.join(tmpdir, _fmt_file(SINAPI_ZIP_PLAN.file_pattern, d))
        download_file(url, tmp_zip)

        # 3) abrir zip e encontrar o arquivo alvo
        target_name = _wanted_inner_name(d)
        with ZipFile(tmp_zip, "r") as zf:
            candidate = next((name for name in zf.namelist() if _matches_target(name, target_name)), None)

            if candidate is None:
                listing = "\n".join(zf.namelist()[:30])
                raise RuntimeError(
                    f"Arquivo alvo '{target_name}' não encontrado no ZIP.\n"
                    f"Alguns arquivos no ZIP:\n{listing}"
                )

            # 4) extrair só o alvo para data/ com nome sem 'Referência'
            dest_name = f"SINAPI_{d.year:04d}_{d.month:02d}.xlsx"
            dest_path = os.path.join(SINAPI_ZIP_PLAN.out_dir, dest_name)

            with zf.open(candidate) as src, open(dest_path, "wb") as dst:
                shutil.copyfileobj(src, dst)

    return dest_path
