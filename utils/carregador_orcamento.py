import pandas as pd

def carregar_orcamento_filtrado(path_orcamento: str, banco: str = None) -> pd.DataFrame:
    """
    Carrega e filtra a aba "Orçamento" de um arquivo Excel, retornando apenas os campos essenciais.

    Campos retornados: CODIGO_ORC, BANCO, DESCRICAO_ORC, VALOR_ORC

    :param path_orcamento: Caminho para o arquivo de orçamento.
    :param banco: Nome do banco a filtrar (ex: "SUDECAP"). Se None, retorna todos os bancos.
    :return: DataFrame filtrado.
    """
    df_raw = pd.read_excel(path_orcamento, sheet_name="Orçamento", header=None)

    # Detecta dinamicamente a linha do cabeçalho
    header_row_index = None
    for i in range(10):
        if df_raw.iloc[i].astype(str).str.contains("Código", case=False).any():
            header_row_index = i
            break

    if header_row_index is None:
        raise ValueError("Não foi possível localizar a linha de cabeçalho com a coluna 'Código'.")

    headers = df_raw.iloc[header_row_index]
    df = df_raw[header_row_index + 1:].copy()
    df.columns = headers

    print("Colunas disponíveis:", df.columns.tolist())  # Debug

    # Renomeia colunas principais
    def renomear_coluna(col):
        if not isinstance(col, str):
            return col
        col_lower = col.lower().strip()
        if "código" in col_lower:
            return "CODIGO_ORC"
        if "banco" in col_lower:
            return "BANCO"
        if "descrição" in col_lower:
            return "DESCRICAO_ORC"
        if "valor unit" in col_lower:
            return "VALOR_ORC"
        return col

    df.columns = [renomear_coluna(c) for c in df.columns]

    if banco:
        df = df[df["BANCO"] == banco]

    df = df[df["CODIGO_ORC"].notna()]
    df["CODIGO_ORC"] = df["CODIGO_ORC"].astype(str).str.strip()

    # Retorna apenas os campos essenciais
    return df[["CODIGO_ORC", "BANCO", "DESCRICAO_ORC", "VALOR_ORC"]]
