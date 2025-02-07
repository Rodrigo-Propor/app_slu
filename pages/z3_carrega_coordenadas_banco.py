import os
import pandas as pd

# Diretório onde os arquivos Excel estão localizados
media_path = 'media/planilhas_SLU'

# Função para carregar todos os arquivos Excel na pasta
def carregar_arquivos_excel():
    arquivos = []
    for arquivo in os.listdir(media_path):
        if arquivo.endswith('.xlsx'):
            file_path = os.path.join(media_path, arquivo)
            try:
                # Lê o arquivo Excel e adiciona à lista
                df = pd.read_excel(file_path)
                arquivos.append((arquivo, df))  # Armazena o nome do arquivo e o DataFrame
            except Exception as e:
                print(f"Erro ao ler o arquivo {arquivo}: {str(e)}")
    return arquivos

# Chamar a função para carregar os arquivos
arquivos_carregados = carregar_arquivos_excel()

# Exibir os dados carregados
for nome_arquivo, df in arquivos_carregados:
    print(f"Dados do arquivo {nome_arquivo}:")
    print(df.head())  # Exibe as primeiras linhas do DataFrame
