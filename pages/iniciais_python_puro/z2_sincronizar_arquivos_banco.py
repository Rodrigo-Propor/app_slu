import os
import sqlite3
from datetime import datetime

# Configuração dos caminhos e da data atual
pasta_media = 'media'
data_atual = datetime.now().strftime('%Y-%m-%d')

# Conectar ao banco de dados
print("Conectando ao banco de dados...")
conexao = sqlite3.connect('banco_dados.db')
cursor = conexao.cursor()
print("Conexão com o banco de dados estabelecida.")

# Função para extrair informações do nome do arquivo
def extrair_info_arquivo(nome_arquivo):
    try:
        partes = nome_arquivo.split('_')
        tipo = partes[0]
        mes = partes[1]
        ano_contrato = partes[2].replace("Ano ", "")
        return tipo, mes, ano_contrato
    except IndexError:
        print(f"Erro ao extrair informações do arquivo {nome_arquivo}. Formato inválido.")
        return None, None, None

# Obter a lista de todos os arquivos na pasta, independentemente da extensão
arquivos_pasta = [
    f for f in os.listdir(pasta_media)
    if os.path.isfile(os.path.join(pasta_media, f))
]
print(f"{len(arquivos_pasta)} arquivos encontrados na pasta '{pasta_media}'.")

# Obter todos os registros no banco de dados
cursor.execute("SELECT id, tipo, mes, ano_contrato, caminho_arquivo, ativo FROM SLU_files")
registros_banco = cursor.fetchall()
print(f"{len(registros_banco)} registros encontrados no banco de dados.")

# Converter registros em um dicionário para fácil comparação
registros_dict = {}
for registro in registros_banco:
    id, tipo, mes, ano_contrato, caminho_arquivo, ativo = registro
    registros_dict[caminho_arquivo] = {
        'id': id,
        'tipo': tipo,
        'mes': mes,
        'ano_contrato': ano_contrato,
        'ativo': ativo,
        'caminho_arquivo': caminho_arquivo
    }

# Contadores para log
arquivos_novos = 0
arquivos_atualizados = 0
arquivos_ignorados = 0
arquivos_nao_encontrados = 0

# Processar arquivos na pasta
for arquivo in arquivos_pasta:
    caminho_arquivo = os.path.join(pasta_media, arquivo)

    # Extrair informações do arquivo
    tipo, mes, ano_contrato = extrair_info_arquivo(arquivo)
    if tipo is None or mes is None or ano_contrato is None:
        arquivos_ignorados += 1
        print(f"Arquivo ignorado devido a formato inválido: {arquivo}")
        continue

    # Verificar se o arquivo já está no banco de dados
    if caminho_arquivo in registros_dict:
        # Se já está no banco, marcar como ativo
        registro_id = registros_dict[caminho_arquivo]['id']
        cursor.execute(
            "UPDATE SLU_files SET ativo = 1, data_remocao = NULL WHERE id = ?",
            (registro_id,)
        )
        arquivos_atualizados += 1
        print(f"Arquivo encontrado e atualizado como ativo: {arquivo}")
    else:
        # Inserir novo arquivo no banco de dados
        cursor.execute(
            """
            INSERT INTO SLU_files (tipo, mes, ano_contrato, caminho_arquivo, ativo, data_carregamento)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (tipo, mes, ano_contrato, caminho_arquivo, 1, data_atual)
        )
        arquivos_novos += 1
        print(f"Novo arquivo registrado no banco de dados: {arquivo}")

# Verificar arquivos que estão no banco mas não na pasta
for caminho_arquivo, dados in registros_dict.items():
    if dados['ativo'] == 1 and not os.path.exists(caminho_arquivo):
        # Atualizar para inativo e definir a data de remoção
        cursor.execute(
            "UPDATE SLU_files SET ativo = 0, data_remocao = ? WHERE id = ?",
            (data_atual, dados['id'])
        )
        arquivos_nao_encontrados += 1
        print(f"Arquivo não encontrado na pasta, marcado como inativo: {dados['caminho_arquivo']}")

# Exibir resumo das operações
print("\nResumo da execução:")
print(f"Total de arquivos na pasta: {len(arquivos_pasta)}")
print(f"Total de arquivos novos registrados: {arquivos_novos}")
print(f"Total de arquivos atualizados como ativos: {arquivos_atualizados}")
print(f"Total de arquivos ignorados (formato inválido): {arquivos_ignorados}")
print(f"Total de arquivos no banco não encontrados na pasta e marcados como inativos: {arquivos_nao_encontrados}")

# Salvar e fechar a conexão
conexao.commit()
conexao.close()
print("Conexão com o banco de dados encerrada.")
print("Script executado com sucesso.")
