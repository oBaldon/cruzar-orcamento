#!/usr/bin/env python3
from __future__ import annotations

import sys, os, argparse, json
sys.path.insert(0, os.path.abspath("src"))

from cruzar_orcamento.adapters.estrutura_orcamento import load_estrutura_orcamento
from cruzar_orcamento.adapters.estrutura_sinapi import load_estrutura_sinapi_analitico
from cruzar_orcamento.validators.estrutura_compare import comparar_estruturas
from cruzar_orcamento.exporters.estrutura_excel import export_estrutura_divergencias_excel


def _pp(divs):
    print(f"\nDivergências encontradas: {len(divs)}")
    for i, d in enumerate(divs[:10], 1):  # preview limitado
        print(f"\n[{i}] PAI {d['pai_codigo']}")
        if d.get("pai_desc_a"): print(f"   A(desc): {d['pai_desc_a']}")
        if d.get("pai_desc_b"): print(f"   B(desc): {d['pai_desc_b']}")
        if d["filhos_missing"]:
            print(f"   MISSING (A tem, B não): {', '.join(d['filhos_missing'][:10])}"
                  + (" …" if len(d['filhos_missing']) > 10 else ""))
        if d["filhos_extra"]:
            print(f"   EXTRA   (B tem, A não): {', '.join(d['filhos_extra'][:10])}"
                  + (" …" if len(d['filhos_extra']) > 10 else ""))
        if d["filhos_desc_mismatch"]:
            print(f"   DESC_DIF (primeiros 5):")
            for mm in d["filhos_desc_mismatch"][:5]:
                print(f"      - {mm['codigo']}:")
                print(f"          A: {mm['a_desc']}")
                print(f"          B: {mm['b_desc']}")


def main():
    p = argparse.ArgumentParser(description="Validação de estrutura (pais+filhos de 1º nível).")
    p.add_argument("--orc",  required=True, help="Arquivo do ORÇAMENTO (Composições).")
    p.add_argument("--base", required=True, help="Arquivo da BASE (ex.: SINAPI_YYYY_MM.xlsx).")
    p.add_argument("--base-type", choices=["ORCAMENTO", "SINAPI"], required=True,
                   help="Tipo da base para comparar com o orçamento.")
    p.add_argument("--json-out", help="Opcional: salvar divergências em JSON.")
    p.add_argument("--xlsx-out", help="Opcional: exportar divergências em Excel.")
    args = p.parse_args()

    print("== Validar estrutura (A=ORÇAMENTO vs B=BASE) ==")
    print(f"A(orc): {args.orc}")
    print(f"B(base): {args.base}  (tipo={args.base_type})")

    # carrega A
    A = load_estrutura_orcamento(args.orc)

    # carrega B
    if args.base_type == "ORCAMENTO":
        B = load_estrutura_orcamento(args.base)
    elif args.base_type == "SINAPI":
        B = load_estrutura_sinapi_analitico(args.base)
    else:
        raise SystemExit("[ERRO] base-type inválido")

    # comparar
    divs = comparar_estruturas(A, B)
    _pp(divs)

    # salvar JSON (opcional)
    if args.json_out:
        os.makedirs(os.path.dirname(args.json_out) or ".", exist_ok=True)
        with open(args.json_out, "w", encoding="utf-8") as f:
            json.dump(divs, f, ensure_ascii=False, indent=2)
        print(f"\n[OK] Divergências salvas em {args.json_out}")

    # exportar Excel (opcional)
    if args.xlsx_out:
        export_estrutura_divergencias_excel(divs, args.xlsx_out)
        print(f"[OK] Excel de divergências salvo em {args.xlsx_out}")

    print("\nOK ✅")


if __name__ == "__main__":
    main()
