import sqlite3
import os

def atualizar_banco_de_dados(caminho_origem, caminho_destino):
    """
    Atualiza o banco de dados de destino com novos dados do banco de dados de origem.

    Args:
        caminho_origem (str): Caminho para o banco de dados de origem.
        caminho_destino (str): Caminho para o banco de dados de destino.
    """

    try:
        # Conectar ao banco de dados de origem (apenas para leitura)
        conn_origem = sqlite3.connect(caminho_origem)
        cursor_origem = conn_origem.cursor()

        # Conectar ao banco de dados de destino
        conn_destino = sqlite3.connect(caminho_destino)
        cursor_destino = conn_destino.cursor()

        # Obter todos os dados da tabela dados_placa_geral do banco de origem
        cursor_origem.execute("SELECT dt_data, ct_cota, cd_este, cd_norte, lc_local, pl_placa FROM dados_placa_geral")
        dados_origem = cursor_origem.fetchall()

        # Obter todas as placas existentes na tabela dados_placa_geral do banco de destino
        cursor_destino.execute("SELECT pl_placa FROM dados_placa_geral")
        placas_destino = {row[0] for row in cursor_destino.fetchall()}

        # Inserir os novos dados no banco de destino
        novos_registros = 0
        for linha in dados_origem:
            dt_data, ct_cota, cd_este, cd_norte, lc_local, pl_placa = linha
            if pl_placa not in placas_destino:
                cursor_destino.execute("""
                    INSERT INTO dados_placa_geral (dt_data, ct_cota, cd_este, cd_norte, lc_local, pl_placa)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (dt_data, ct_cota, cd_este, cd_norte, lc_local, pl_placa))
                novos_registros += 1

        # Obter todos os dados da tabela placas_completas_slu_bh do banco de origem
        cursor_origem.execute("SELECT data, tipo, descricao, coordenada_este, coordenada_norte, elevacao, placa FROM placas_completas_slu_bh")
        dados_origem_placas = cursor_origem.fetchall()

        # Obter todas as placas existentes na tabela placas_completas_slu_bh do banco de destino
        cursor_destino.execute("SELECT placa FROM placas_completas_slu_bh")
        placas_destino_placas = {row[0] for row in cursor_destino.fetchall()}

        # Inserir os novos dados na tabela placas_completas_slu_bh do banco de destino
        novos_registros_placas = 0
        for linha_placas in dados_origem_placas:
            data, tipo, descricao, coordenada_este, coordenada_norte, elevacao, placa = linha_placas
            if placa not in placas_destino_placas:
                cursor_destino.execute("""
                    INSERT INTO placas_completas_slu_bh (data, tipo, descricao, coordenada_este, coordenada_norte, elevacao, placa)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (data, tipo, descricao, coordenada_este, coordenada_norte, elevacao, placa))
                novos_registros_placas += 1

        # Commit das alterações no banco de destino
        conn_destino.commit()

        print(f"Atualização concluída.")
        print(f"{novos_registros} novos registros inseridos na tabela dados_placa_geral.")
        print(f"{novos_registros_placas} novos registros inseridos na tabela placas_completas_slu_bh.")

    except sqlite3.Error as e:
        print(f"Erro ao acessar ou atualizar o banco de dados: {e}")
        if conn_destino:
            conn_destino.rollback()
    finally:
        if conn_origem:
            conn_origem.close()
        if conn_destino:
            conn_destino.close()

if __name__ == "__main__":
    caminho_origem = "banco_dados.db"
    caminho_destino = os.path.join("banco_dados_completo", "banco_dados.db")

    # Verificar se o banco de dados de origem existe
    if not os.path.exists(caminho_origem):
        print(f"Erro: Banco de dados de origem não encontrado em: {caminho_origem}")
    # Verificar se o diretório do banco de dados de destino existe, se não, cria
    diretorio_destino = os.path.dirname(caminho_destino)
    if not os.path.exists(diretorio_destino):
        os.makedirs(diretorio_destino)
        # Criar o arquivo de banco de dados de destino se não existir
        if not os.path.exists(caminho_destino):
            conn = sqlite3.connect(caminho_destino)
            cursor = conn.cursor()
            # Recriar a estrutura da tabela placas_completas_slu_bh no destino
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS placas_completas_slu_bh (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tipo TEXT,
                    descricao TEXT,
                    coordenada_este REAL,
                    coordenada_norte REAL,
                    elevacao REAL,
                    info_gerada TEXT,
                    nome_arquivo TEXT,
                    placa TEXT,
                    data TEXT
                )
            """)
            # Recriar a estrutura da tabela dados_placa_geral no destino
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS dados_placa_geral (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    dt_data TEXT,
                    ct_cota REAL,
                    cd_este REAL,
                    cd_norte REAL,
                    lc_local TEXT,
                    pl_placa TEXT,
                    lp_local_placa TEXT,
                    obs1 TEXT,
                    obs2 TEXT,
                    obs3 TEXT
                )
            """)
            conn.commit()
            conn.close()

    # Verificar se o banco de dados de destino existe
    if not os.path.exists(caminho_destino):
        print(f"Erro: Banco de dados de destino não encontrado em: {caminho_destino}")
    else:
        atualizar_banco_de_dados(caminho_origem, caminho_destino)