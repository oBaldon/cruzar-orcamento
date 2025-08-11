import os
from utils.carregador_orcamento import carregar_orcamento_filtrado
from utils.carregador_sudecap import carregar_tabela_sudecap
from repositorios.sudecap.processor import SudecapProcessor
import pandas as pd

# Caminhos
orcamento_path = "data/ORÇAMENTO - ACIONAMENTO 01 - REV 05 final.xlsx"
sinapi_path = "data/2025.04-tabela-de-construcao-desonerada.xlsx"
saida_path = "output/sudecap_cruzado.xlsx"
comparado_path = "output/sudecap_comparado.xlsx"

# Garante que a pasta de saída exista
os.makedirs("output", exist_ok=True)

# Carrega planilhas de dados
print("Carregando dados...")
df_orcamento = carregar_orcamento_filtrado(orcamento_path, banco="SUDECAP")
df_sinapi = carregar_tabela_sudecap(sinapi_path)

# Executa cruzamento e comparação
print("Executando cruzamento para SUDECAP...")
processor = SudecapProcessor()
df_cruzado = processor.cruzar(df_orcamento, df_sinapi)

# Salva os resultados
df_cruzado.to_excel(saida_path, index=False)
