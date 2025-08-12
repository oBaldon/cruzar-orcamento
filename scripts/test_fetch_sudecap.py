#!/usr/bin/env python3
from __future__ import annotations

import sys, os
sys.path.insert(0, os.path.abspath("src"))
import argparse
from datetime import date

from cruzar_orcamento.fetchers.base import (
    fetch_latest,
    find_latest_available,
    _fmt_file,      # só pra montar o nome local
)
from cruzar_orcamento.fetchers.providers.sudecap import SUDECAP_PLAN
from cruzar_orcamento.fetchers.http import download_file


def main():
    parser = argparse.ArgumentParser(
        description="Teste de fetch para SUDECAP (busca retroativa e por ano)."
    )
    parser.add_argument(
        "--mode",
        choices=["retro", "year"],
        default="retro",
        help="retro: busca voltando meses até achar; year: encontra o último daquele ano.",
    )
    parser.add_argument("--year", type=int, help="Ano base/alvo. retro: base; year: ano alvo.")
    parser.add_argument("--month", type=int, help="Mês base (1-12), apenas no modo retro.")
    parser.add_argument("--back", type=int, default=24, help="retro: voltar até N meses (padrão: 24).")
    args = parser.parse_args()

    today = date.today()

    if args.mode == "retro":
        base = date(args.year or today.year, args.month or today.month, 1)
        print(f">> [RETRO] Buscando {SUDECAP_PLAN.name} a partir de {base:%Y-%m} (back={args.back})…")
        try:
            dest = fetch_latest(SUDECAP_PLAN, base, max_months_back=args.back)
        except Exception as e:
            print(f"[ERRO] {e}", file=sys.stderr)
            sys.exit(2)
        print(f">> OK: baixado em {dest}")

    elif args.mode == "year":
        if not args.year:
            print("[ERRO] --year é obrigatório no modo 'year'", file=sys.stderr)
            sys.exit(2)
        print(f">> [YEAR] Buscando a última versão de {SUDECAP_PLAN.name} em {args.year}…")
        try:
            d, url = find_latest_available(SUDECAP_PLAN, args.year)
        except Exception as e:
            print(f"[ERRO] {e}", file=sys.stderr)
            sys.exit(2)

        # baixa para data/SUDECAP_YYYY_MM.xls
        fname = _fmt_file(SUDECAP_PLAN.file_pattern, d)
        import os
        os.makedirs(SUDECAP_PLAN.out_dir, exist_ok=True)
        dest = os.path.join(SUDECAP_PLAN.out_dir, fname)

        print(f">> Encontrado: {d:%Y-%m} | URL: {url}")
        try:
            download_file(url, dest)
        except Exception as e:
            print(f"[ERRO] Falha ao baixar {url}: {e}", file=sys.stderr)
            sys.exit(3)
        print(f">> OK: baixado em {dest}")


if __name__ == "__main__":
    main()
