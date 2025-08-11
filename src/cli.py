from __future__ import annotations

import sys
from pathlib import Path
import typer

# permite "python src/cli.py" rodar sem instalar o pacote
sys.path.append(str(Path(__file__).resolve().parent))

from cruzar_orcamento.adapters.orcamento import load_orcamento
from cruzar_orcamento.adapters.sudecap import load_sudecap
from cruzar_orcamento.processor import cruzar
from cruzar_orcamento.exporters.excel import export_cruzamento_excel

app = typer.Typer(no_args_is_help=True, add_completion=False, help="""
Cruzar Orçamento x Bancos de Referência.

Exemplo:
  python src/cli.py run --orc data/ORÇAMENTO.xlsx --ref data/sudecap.xlsx \\
                        --banco SUDECAP --out output/cruzamento.xlsx
""")

@app.command("run")
def run(
    orc: Path = typer.Option(..., exists=True, readable=True, help="Arquivo de orçamento (Excel)."),
    ref: Path = typer.Option(..., exists=True, readable=True, help="Arquivo de referência (ex.: SUDECAP Excel)."),
    ref_type: str = typer.Option("SUDECAP", help="Tipo da referência: SUDECAP (por enquanto)."),
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
    else:
        raise typer.BadParameter(f"ref_type '{ref_type}' não suportado ainda. Use: SUDECAP")

    # tolerâncias
    # tol_abs/tol_rel = 0.0 significa “qualquer diferença marca divergência”
    tol_rel_final = float(tol_rel or 0.0)
    tol_abs_final = float(tol_abs or 0.0)
    tol_abs_use = tol_abs_final if tol_abs_final > 0 else None

    typer.secho(">> Cruzando…", fg=typer.colors.CYAN)
    cruzado, diverg = cruzar(
        orcamento=orc_dict,
        referencia=ref_dict,
        banco=banco or None,
        tol_rel=tol_rel_final,
        comparar_descricao=True,
    )

    # Se quiser usar tol_abs no futuro, basta habilitar a lógica no processor e passar aqui:
    # cruzar(..., tol_abs=tol_abs_use)

    typer.echo(f">> Total cruzado: {len(cruzado)} | Divergências: {len(diverg)}")

    typer.secho(f">> Exportando Excel → {out}", fg=typer.colors.CYAN)
    out.parent.mkdir(parents=True, exist_ok=True)
    export_cruzamento_excel(cruzado, diverg, str(out))

    typer.secho(">> Pronto!", fg=typer.colors.GREEN)


if __name__ == "__main__":
    app(prog_name="cli.py")
