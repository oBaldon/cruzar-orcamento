import pandas as pd

class SudecapProcessor:
    """
    Processor responsável por cruzar e comparar dados do orçamento com a tabela de preços da SUDECAP.
    """

    def __init__(self):
        pass

    def cruzar(self, df_orcamento: pd.DataFrame, df_sudecap: pd.DataFrame) -> pd.DataFrame:
        """
        Cruza os dados do orçamento com os dados da tabela de preços SUDECAP com base no código
        e realiza comparações de descrição e valor unitário.

        :param df_orcamento: DataFrame contendo os dados do orçamento filtrado.
        :param df_sudecap: DataFrame contendo os dados da tabela de preços SUDECAP.
        :return: DataFrame com o cruzamento completo.
        """
        print("Executando cruzamento para SUDECAP...")

        print("Colunas SUDECAP carregadas:", df_sudecap.columns.tolist())

        # Filtra colunas relevantes dos dois DataFrames
        df_orcamento = df_orcamento[["CODIGO_ORC", "BANCO", "DESCRICAO_ORC", "VALOR_ORC"]]
        df_sudecap = df_sudecap[["CODIGO_SUDECAP", "DESCRICAO_SUDECAP", "VALOR_SUDECAP"]]

        # Renomeia a coluna de código da SUDECAP para permitir o merge
        df_sudecap = df_sudecap.rename(columns={"CODIGO_SUDECAP": "CODIGO_ORC"})

        # Merge com base no código
        df_cruzado = pd.merge(df_orcamento, df_sudecap, on="CODIGO_ORC", how="left")

        # Remove colunas duplicadas (evita erros em operações aritméticas)
        df_cruzado = df_cruzado.loc[:, ~df_cruzado.columns.duplicated()]
        df_cruzado = df_cruzado.reset_index(drop=True)

        return df_cruzado
