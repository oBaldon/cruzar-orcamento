import pandas as pd

def carregar_tabela_sudecap(path_sudecap: str) -> pd.DataFrame:
    """
    Carrega e processa a tabela SUDECAP, detectando dinamicamente o cabeçalho
    e retornando apenas os campos essenciais: CODIGO_SUDECAP, DESCRICAO_SUDECAP, VALOR_SUDECAP.

    :param path_sudecap: Caminho para o arquivo da tabela SUDECAP (Excel).
    :return: DataFrame com as colunas padronizadas.
    """
    df_raw = pd.read_excel(path_sudecap, sheet_name=0, header=None)

    # Detecta a linha do cabeçalho com base em "Código"
    header_row_index = None
    for i in range(10):
        if df_raw.iloc[i].astype(str).str.contains("Código", case=False).any():
            header_row_index = i
            break

    if header_row_index is None:
        raise ValueError("Não foi possível localizar a linha de cabeçalho com a coluna 'Código' na planilha SUDECAP.")

    headers = df_raw.iloc[header_row_index]
    df = df_raw[header_row_index + 1:].copy()
    df.columns = headers

    print("Colunas SUDECAP carregadas:", df.columns.tolist())

    # Renomeia apenas as colunas essenciais
    def renomear_coluna(col):
        if not isinstance(col, str):
            return col
        col_lower = col.lower().strip()
        if "código" in col_lower or "codigo" in col_lower:
            return "CODIGO_SUDECAP"
        if "descrição" in col_lower or "descricao" in col_lower:
            return "DESCRICAO_SUDECAP"
        if "valor" in col_lower:
            return "VALOR_SUDECAP"
        return col

    df.columns = [renomear_coluna(c) for c in df.columns]

    print("Colunas após renomeação:", df.columns.tolist())

    df = df[df["CODIGO_SUDECAP"].notna()]
    df["CODIGO_SUDECAP"] = df["CODIGO_SUDECAP"].astype(str).str.strip()

    return df[["CODIGO_SUDECAP", "DESCRICAO_SUDECAP", "VALOR_SUDECAP"]]
