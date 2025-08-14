# src/cli.py
from __future__ import annotations

import sys
from pathlib import Path
import typer

# permite "python src/cli.py" rodar sem instalar o pacote
sys.path.append(str(Path(__file__).resolve().parent))

from cruzar_orcamento.adapters.orcamento import load_orcamento
from cruzar_orcamento.adapters.sudecap import load_sudecap
from cruzar_orcamento.adapters.sinapi import load_sinapi_ccd_pr
from cruzar_orcamento.validators.processor import cruzar
from cruzar_orcamento.exporters.excel import export_cruzamento_excel

# ---------------------------------------------------------------------
# ⚠️ FETCHERS DESLIGADOS POR PADRÃO
# Para reativar no futuro, descomente estas linhas e as chamadas
# correspondentes nos comandos indicados.
# ---------------------------------------------------------------------
# from datetime import date
# from cruzar_orcamento.fetchers.base import fetch_latest, find_latest_available
# from cruzar_orcamento.fetchers.providers.sudecap import SUDECAP_PLAN
# from cruzar_orcamento.fetchers.providers.sinapi import fetch_latest_sinapi_referencia_xlsx
# from cruzar_orcamento.fetchers.http import download_file

app = typer.Typer(no_args_is_help=True, add_completion=False, help="""
Cruzar Orçamento x Bancos de Referência.

Exemplo:
  python src/cli.py run --orc data/ORÇAMENTO.xlsx --ref data/sudecap.xlsx \\
                        --banco SUDECAP --out output/cruzamento.xlsx
""")

# -----------------------------------------
# Helpers: pegar o arquivo mais recente por padrão em data/
# -----------------------------------------
def _latest_file(prefix: str, ext: str) -> Path:
    """
    Procura em data/ pelo padrão {prefix}_YYYY_MM.{ext} e retorna o mais recente
    lexicograficamente (assumindo YYYY_MM no nome).
    """
    candidates = sorted(Path("data").glob(f"{prefix}_????_??.{ext}"))
    if not candidates:
        raise FileNotFoundError(f"Nenhum arquivo encontrado: data/{prefix}_YYYY_MM.{ext}")
    return candidates[-1]

def _latest_sudecap_any() -> Path:
    """
    Tenta achar SUDECAP_YYYY_MM.xls; se não houver, tenta .xlsx.
    """
    try:
        return _latest_file("SUDECAP", "xls")
    except FileNotFoundError:
        return _latest_file("SUDECAP", "xlsx")

# -----------------------------------------
# Comando “unitário”: orçamento x referência informada
# -----------------------------------------
@app.command("run")
def run(
    orc: Path = typer.Option(..., exists=True, readable=True, help="Arquivo de orçamento (Excel)."),
    ref: Path = typer.Option(..., exists=True, readable=True, help="Arquivo de referência (SUDECAP/SINAPI)."),
    ref_type: str = typer.Option("SUDECAP", help="Tipo da referência: SUDECAP ou SINAPI."),
    banco: str = typer.Option("", help="Filtra o orçamento por este banco (ex.: SUDECAP, SINAPI)."),
    tol_rel: float = typer.Option(0.0, help="Tolerância relativa (fração). Ex.: 0.02 = 2%%. Default 0.0."),
    tol_abs: float = typer.Option(0.0, help="Tolerância absoluta. Ex.: 0.01 = 1 centavo. Default 0.0."),
    valor_scale: float = typer.Option(1.0, help="Fator multiplicador para valores do orçamento (ex.: 0.01)."),
    out: Path = typer.Option(Path("output/cruzamento.xlsx"), help="Caminho do Excel de saída."),
):
    """
    Carrega o orçamento, carrega a referência, cruza e exporta um Excel com
    abas 'cruzado' e 'divergencias'.
    """
    typer.secho(">> Lendo ORÇAMENTO…", fg=typer.colors.CYAN)
    orc_dict = load_orcamento(str(orc), valor_scale=valor_scale)

    if banco:
        typer.echo(f">> Filtrando orçamento por banco: {banco}")

    typer.secho(f">> Lendo referência: {ref_type}…", fg=typer.colors.CYAN)
    ref_type_norm = ref_type.strip().upper()

    if ref_type_norm == "SUDECAP":
        ref_dict = load_sudecap(str(ref))
    elif ref_type_norm == "SINAPI":
        ref_dict = load_sinapi_ccd_pr(str(ref), cidade="CURITIBA")
    else:
        raise typer.BadParameter("ref_type não suportado. Use: SUDECAP, SINAPI")

    # tolerâncias
    tol_rel_final = float(tol_rel or 0.0)
    tol_abs_final = float(tol_abs or 0.0)
    _ = tol_abs_final  # reservado para uso futuro (se ligar tol_abs no processor)

    typer.secho(">> Cruzando…", fg=typer.colors.CYAN)
    cruzado, diverg = cruzar(
        orcamento=orc_dict,
        referencia=ref_dict,
        banco=banco or None,
        tol_rel=tol_rel_final,
        comparar_descricao=True,
    )

    typer.echo(f">> Total cruzado: {len(cruzado)} | Divergências: {len(diverg)}")

    typer.secho(f">> Exportando Excel → {out}", fg=typer.colors.CYAN)
    out.parent.mkdir(parents=True, exist_ok=True)
    export_cruzamento_excel(cruzado, diverg, str(out))

    typer.secho(">> Pronto!", fg=typer.colors.GREEN)

# -----------------------------------------
# (Comentado) fetch-all — deixar pronto para reativar no futuro
# -----------------------------------------
# @app.command("fetch-all")
# def fetch_all(
#     back: int = typer.Option(18, "--back", help="Buscar até N meses para trás"),
# ):
#     """
#     Baixa os arquivos mais recentes de SINAPI (ZIP → extrai Referência) e SUDECAP.
#     Salva com nomes padronizados em data/ (SINAPI_YYYY_MM.xlsx, SUDECAP_YYYY_MM.xls).
#     """
#     from datetime import date
#     from cruzar_orcamento.fetchers.base import find_latest_available
#     from cruzar_orcamento.fetchers.providers.sudecap import SUDECAP_PLAN
#     from cruzar_orcamento.fetchers.providers.sinapi import fetch_latest_sinapi_referencia_xlsx
#     from cruzar_orcamento.fetchers.http import download_file
#
#     base = date.today()
#
#     # SINAPI
#     typer.secho(">> [FETCH] SINAPI (ZIP) …", fg=typer.colors.CYAN)
#     sinapi_path = fetch_latest_sinapi_referencia_xlsx(base, max_months_back=back)
#     typer.secho(f">> [OK] {sinapi_path}", fg=typer.colors.GREEN)
#
#     # SUDECAP
#     typer.secho(">> [FETCH] SUDECAP …", fg=typer.colors.CYAN)
#     d_sud, url_sud = find_latest_available(SUDECAP_PLAN, base, max_months_back=back)
#     dest_sud = Path("data") / f"SUDECAP_{d_sud.year:04d}_{d_sud.month:02d}.xls"
#     download_file(url_sud, str(dest_sud))
#     typer.secho(f">> [OK] {dest_sud}", fg=typer.colors.GREEN)

# -----------------------------------------
# run-both-auto (usa últimos arquivos da pasta data/)
# -----------------------------------------
@app.command("run-both-auto")
def run_both_auto(
    orc: Path = typer.Option(..., exists=True, readable=True, help="Arquivo de orçamento (Composições)."),
    cidade: str = typer.Option("CURITIBA", "--cidade", help="Cidade para SINAPI CCD"),
    tol_rel: float = typer.Option(0.0, help="Tolerância relativa (fração)."),
    out_dir: Path = typer.Option(Path("output"), "--out-dir", help="Pasta de saída"),
    # fetch: bool = typer.Option(False, help="(Futuro) Baixar últimas versões antes de cruzar."),
    # back: int = typer.Option(18, help="(Futuro) Se fetch=True, buscar até N meses para trás"),
):
    """
    Carrega os **últimos arquivos** encontrados em data/ e cruza:
        - Orçamento (banco=SINAPI) x último SINAPI_YYYY_MM.xlsx
        - Orçamento (banco=SUDECAP) x último SUDECAP_YYYY_MM.xls (ou .xlsx)
    Exporta 2 planilhas em output/.
    """
    out_dir.mkdir(parents=True, exist_ok=True)

    # # (Futuro) fetch opcional
    # if fetch:
    #     typer.secho(">> Preparando referências (fetch-all)…", fg=typer.colors.CYAN)
    #     fetch_all(back=back)

    # (1) Carrega ORÇAMENTO uma vez
    typer.secho(">> Lendo ORÇAMENTO…", fg=typer.colors.CYAN)
    orc_dict = load_orcamento(str(orc))

    # ===== SINAPI =====
    try:
        sinapi_file = _latest_file("SINAPI", "xlsx")
    except FileNotFoundError:
        typer.secho("[SINAPI] Nenhum arquivo encontrado em data/SINAPI_YYYY_MM.xlsx.",
                    err=True, fg=typer.colors.YELLOW)
        sinapi_file = None

    if sinapi_file:
        try:
            typer.echo(f">> Lendo referência SINAPI: {sinapi_file.name}")
            ref_sinapi = load_sinapi_ccd_pr(str(sinapi_file), cidade=cidade)

            typer.echo(">> Cruzando (SINAPI)…")
            cruz_s, div_s = cruzar(
                orc_dict, ref_sinapi, banco="SINAPI",
                tol_rel=float(tol_rel), comparar_descricao=True
            )

            y, m = sinapi_file.stem.split("_")[-2:]
            out_sinapi = out_dir / f"cruzamento_sinapi_{y}_{m}.xlsx"
            typer.echo(f">> Exportando Excel (SINAPI) → {out_sinapi}")
            export_cruzamento_excel(cruz_s, div_s, str(out_sinapi))
            typer.secho(">> SINAPI OK", fg=typer.colors.GREEN)
        except Exception as e:
            typer.secho(f"[SINAPI] Falhou: {e}", err=True, fg=typer.colors.RED)

    # ===== SUDECAP =====
    try:
        sud_file = _latest_sudecap_any()
    except FileNotFoundError:
        typer.secho("[SUDECAP] Nenhum arquivo encontrado em data/SUDECAP_YYYY_MM.xls(.xlsx).",
                    err=True, fg=typer.colors.YELLOW)
        sud_file = None

    if sud_file:
        try:
            typer.echo(f">> Lendo referência SUDECAP: {sud_file.name}")
            ref_sud = load_sudecap(str(sud_file))

            typer.echo(">> Cruzando (SUDECAP)…")
            cruz_u, div_u = cruzar(
                orc_dict, ref_sud, banco="SUDECAP",
                tol_rel=float(tol_rel), comparar_descricao=True
            )

            y, m = sud_file.stem.split("_")[-2:]
            out_sud = out_dir / f"cruzamento_sudecap_{y}_{m}.xlsx"
            typer.echo(f">> Exportando Excel (SUDECAP) → {out_sud}")
            export_cruzamento_excel(cruz_u, div_u, str(out_sud))
            typer.secho(">> SUDECAP OK", fg=typer.colors.GREEN)
        except Exception as e:
            typer.secho(f"[SUDECAP] Falhou: {e}", err=True, fg=typer.colors.RED)

if __name__ == "__main__":
    app(prog_name="cli.py")
