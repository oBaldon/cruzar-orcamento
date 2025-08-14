# cruzar-orcamento

Pipeline para **cruzar composições do seu ORÇAMENTO** com **bancos de referência** (SUDECAP, SINAPI CCD/PR), sinalizando divergências de preço e descrição, e exportando um Excel com abas de **cruzado** e **divergências**.

---

## Sumário

- [Arquitetura](#arquitetura)
- [Instalação](#instalação)
- [Arquivos de entrada](#arquivos-de-entrada)
- [Como usar (CLI)](#como-usar-cli)
  - [`run` – cruzar um orçamento com 1 referência](#run--cruzar-um-orçamento-com-1-referência)
  - [`run-both-auto` – rodar SINAPI e SUDECAP de uma vez](#run-both-auto--rodar-sinapi-e-sudecap-de-uma-vez)
  - [`fetch-all` – (opcional) baixar automaticamente referências](#fetch-all--opcional-baixar-automaticamente-referências)
- [Lógica de cruzamento](#lógica-de-cruzamento)
- [Exportação para Excel](#exportação-para-excel)
- [Adapters (parsers)](#adapters-parsers)
  - [Orçamento (Composições)](#orçamento-composições)
  - [SUDECAP](#sudecap)
  - [SINAPI CCD (Paraná)](#sinapi-ccd-paraná)
- [Fetchers (opcional)](#fetchers-opcional)
- [Convenções de nomes (data/)](#convenções-de-nomes-data)
- [Roadmap / Próximos passos](#roadmap--próximos-passos)

---

## Arquitetura

```
src/
  cruzar_orcamento/
    adapters/
      orcamento.py      # lê a aba "Composições" do orçamento
      sudecap.py        # lê a planilha SUDECAP
      sinapi.py         # lê SINAPI CCD (PR)
    processor.py        # cruza A (orc) vs B (banco) e aponta divergências
    exporters/
      excel.py          # gera Excel com abas 'cruzado' e 'divergencias'
    fetchers/           # opcional: baixar arquivos (SINAPI ZIP, SUDECAP)
      base.py
      http.py
      providers/
        sinapi.py
        sudecap.py
  cli.py                # interface de linha de comando (Typer)
scripts/
  test_cruzamento.py    # smoke tests locais
  test_fetch_*.py       # testes de fetchers (opcional)
```

---

## Instalação

Recomendado Python 3.11+.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install pandas openpyxl typer requests # etc.
```

Para ler **.xls** (SUDECAP), é necessário `xlrd` (se disponível no seu ambiente). Se não, converta o arquivo para **.xlsx** ou use o suporte atual que lê `.xls` com `xlrd` quando presente.

---

## Arquivos de entrada

- **Orçamento (Excel)**:
  - Contém a aba **Composições** (ou similar).
  - Deve ter colunas equivalentes a: **Código**, **Descrição**, **Valor Unitário**; opcional **Banco/Base/Fonte** e **Tipo**.
  - A coluna **Tipo** (ou outra coluna que contenha “Composição/Composição Auxiliar”) é detectada automaticamente; apenas esses tipos são importados.

- **Referências**:
  - **SUDECAP**: planilha **.xls** no formato oficial.
  - **SINAPI CCD/PR**: arquivo **`SINAPI_YYYY_MM.xlsx`** (internamente extraído do ZIP mensal). Usamos a coluna **PR → CURITIBA → “Custo (R$)”**.

Coloque os arquivos em `data/` com os nomes padronizados (ver [Convenções](#convenções-de-nomes-data)).

---

## Como usar (CLI)

### `run` – cruzar um orçamento com 1 referência

```bash
python -m src.cli run   --orc "data/ORÇAMENTO - ACIONAMENTO 01 - REV 05 final.xlsx"   --ref "data/2025.04-tabela-de-construcao-desonerada.xls"   --ref-type SUDECAP   --banco SUDECAP   --tol-rel 0.0   --out output/cruzamento_sudecap.xlsx
```

Para SINAPI (CCD/PR):

```bash
python -m src.cli run   --orc "data/ORÇAMENTO - ACIONAMENTO 01 - REV 05 final.xlsx"   --ref "data/SINAPI_2025_06.xlsx"   --ref-type SINAPI   --banco SINAPI   --tol-rel 0.0   --out output/cruzamento_sinapi.xlsx
```

Parâmetros relevantes:
- `--banco`: filtra o orçamento por banco antes do cruzamento (e.g., `SUDECAP`, `SINAPI`).
- `--tol-rel`: tolerância relativa (fração). `0.02 = 2%`. Com `0.0`, qualquer diferença marca divergência.
- `--valor_scale`: fator multiplicador nos valores do orçamento (ex.: `0.01` se o arquivo vier 100×).

### `run-both-auto` – rodar SINAPI e SUDECAP de uma vez

Carrega o orçamento uma única vez e cruza com **os arquivos mais recentes encontrados em `data/`**:

```bash
python -m src.cli run-both-auto   --orc "data/ORÇAMENTO - ACIONAMENTO 01 - REV 05 final.xlsx"   --tol-rel 0.0   --out-dir output
```

Gera:
- `output/cruzamento_sinapi_YYYY_MM.xlsx`
- `output/cruzamento_sudecap_YYYY_MM.xlsx`

> Por padrão **não baixa** automaticamente. Se desejar ligar os fetchers no futuro, o comando já tem `--fetch` (padrão desativado por ora).

### `fetch-all` – (opcional) baixar automaticamente referências

**Desativado por padrão** no fluxo principal, mas pronto para uso quando quiser:

```bash
python -m src.cli fetch-all --back 18
```

- Baixa o **SINAPI** (ZIP do mês mais recente → extrai apenas `SINAPI_Referência_YYYY_MM.xlsx` e salva como `SINAPI_YYYY_MM.xlsx`).
- Tenta baixar o **SUDECAP** no padrão oficial de URL.

---

## Lógica de cruzamento

No `processor.py`:

- O orçamento **A** pode ser filtrado por `--banco` antes do match.
- Para cada `codigo`:
  - **Match por código** com a referência **B**.
  - **Divergência de valor**:  
    - Se `B.valor > 0`: `dif_abs = |A-B|`, `dif_rel = dif_abs / B`; marca **VALOR_DIVERGENTE** se `dif_rel > tol_rel`.
    - Se `B.valor` nulo/zero e `A != 0`: marca **VALOR_BASE_ZERO_OU_NULO**.
    - Calcula ainda a **direção** da diferença: `dir = "MAIOR" | "MENOR" | "IGUAL"` comparando `A` vs `B`.
  - **Divergência de descrição** (opcional): compara versões normalizadas (casefold + sem acento). Se diferente, marca **DESCRICAO_DIVERGENTE**.

### Sobre códigos duplicados no orçamento
- O adapter de **orçamento** atualmente **log**a duplicados e **mantém o último** (o dicionário é por código). Isso preserva a compatibilidade do pipeline atual.

---

## Exportação para Excel

Exporta duas abas:

- **`cruzado`**  
  Colunas: `codigo, a_banco, a_desc, a_valor, b_desc, b_valor, match`

- **`divergencias`**  
  Colunas: `codigo, motivos[], dif_abs, dif_rel, dir`  
  - `dir` indica **se o orçamento está MAIOR/MENOR/IGUAL** à referência (quando aplicável).

---

## Adapters (parsers)

### Orçamento (Composições)

- Detecta automaticamente a linha de cabeçalho e a coluna de **Tipo** (mesmo que não se chame “Tipo”).
- Filtra **apenas** linhas cujo tipo seja **“Composição”** ou **“Composição Auxiliar”**.
- Lê `Código`, `Descrição`, `Valor Unitário` e, se existir, **Banco/Base/Fonte**.
- Converte valores com segurança; aceita vírgula decimal e normaliza para `float`.
- `valor_scale` permite corrigir arquivos que venham com escala incorreta (e.g. 100×).

### SUDECAP

- Lê o Excel oficial (`.xls`).
- A resolução de códigos, descrições e valores segue o layout publicado.
- Requer `xlrd` para `.xls` no seu ambiente (ou converter para `.xlsx`).

### SINAPI CCD (Paraná)

- Lê `SINAPI_YYYY_MM.xlsx` (extraído do ZIP oficial).
- Cabeçalho multinível: procura `("PR", "CURITIBA")` → coluna **“Custo (R$)”**.
- **Códigos** podem vir encapsulados em fórmulas `HYPERLINK(...)`; o parser extrai o número final (ex.: `=HIPERLINK(...;105002)` → `105002`).
- Normaliza decimais com vírgula (e.g. `1.234,77` → `1234.77`).

---

## Fetchers (opcional)

- **SINAPI (ZIP)**  
  Busca retroativa mês a mês e baixa o ZIP, extraindo **apenas** `SINAPI_Referência_YYYY_MM.xlsx`, salvando como `data/SINAPI_YYYY_MM.xlsx`.  
  Se algo falhar, há suporte a logs simples (pode ser habilitado se necessário).

- **SUDECAP**  
  Monte de URL fixa: `AAAA.MM-tabela-de-construcao-desonerada.xls`.  
  Implementamos uma rotina “robusta” de verificação via **GET stream** (sem `HEAD/Range`) e **logs de diagnóstico** em `data/_debug_sudecap_YYYY_MM.log` quando a resposta parece HTML/portal ao invés de arquivo.  
  **No fluxo atual do CLI, os fetchers ficam desativados** por padrão.

---

## Convenções de nomes (`data/`)

Os nomes padrão permitem o `run-both-auto` encontrar “o mais recente” sem parâmetros:

- `data/SINAPI_YYYY_MM.xlsx` – referência CCD/PR (arquivo extraído do ZIP).
- `data/SUDECAP_YYYY_MM.xls` – referência SUDECAP.
- `data/ORÇAMENTO*.xlsx` – seu orçamento (nome livre).

---

## Roadmap / Próximos passos

- **Novos adapters**:
  - **CPOS/CDHU** (acesso em andamento).
  - **SBC** (acesso pago – aguardar).
- **CLI**:
  - Reabilitar `--fetch` como padrão quando os portais estabilizarem (código já preparado).
  - Suporte a **tolerância absoluta** (`tol_abs`) no `processor`.
- **Exportação**:
  - Exportar um **CSV adicional** ou **aba com estatísticas** (totais por motivo, % de divergências).
- **Front-end**:
  - Camada web para subir orçamento, escolher banco e baixar o relatório.
- **Dados duplicados no orçamento**:
  - Opcional: evolução do schema para lidar com múltiplas ocorrências do mesmo código (hoje mantemos o último para manter a compatibilidade de dicionário → cruzamento).

---

## Exemplos rápidos

Cruzamento SUDECAP:

```bash
python -m src.cli run   --orc "data/ORÇAMENTO - ACIONAMENTO 01 - REV 05 final.xlsx"   --ref "data/SUDECAP_2025_04.xls"   --ref-type SUDECAP   --banco SUDECAP   --tol-rel 0.0   --out output/cruzamento_sudecap_2025_04.xlsx
```

Cruzamento SINAPI (CCD/PR):

```bash
python -m src.cli run   --orc "data/ORÇAMENTO - ACIONAMENTO 01 - REV 05 final.xlsx"   --ref "data/SINAPI_2025_06.xlsx"   --ref-type SINAPI   --banco SINAPI   --tol-rel 0.0   --out output/cruzamento_sinapi_2025_06.xlsx
```

Rodar ambos automaticamente com os últimos arquivos em `data/`:

```bash
python -m src.cli run-both-auto   --orc "data/ORÇAMENTO - ACIONAMENTO 01 - REV 05 final.xlsx"   --tol-rel 0.0   --out-dir output
```

---

