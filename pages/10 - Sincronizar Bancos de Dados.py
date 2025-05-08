import streamlit as st
import sqlite3
import os
import time # Para a barra de progresso e feedback visual

# --- Configuração dos Caminhos dos Bancos de Dados ---
# Presume que o script está rodando dentro da pasta 'pages' ou similar
# Ajuste os caminhos conforme a estrutura do seu projeto
APP_DIR = os.path.dirname(os.path.dirname(__file__)) # Diretório pai da pasta 'pages'
SOURCE_DB_PATH = os.path.join(APP_DIR, "banco_dados.db")
DEST_DB_DIR = os.path.join(APP_DIR, "banco_dados_completo")
DEST_DB_NAME = "banco_dados.db"
DEST_DB_PATH = os.path.join(DEST_DB_DIR, DEST_DB_NAME)

# --- Funções Auxiliares ---

def connect_db(db_path):
    """Tenta conectar ao banco de dados SQLite."""
    # Verifica se o diretório do banco de destino existe, se não, cria (opcional)
    if db_path == DEST_DB_PATH:
        if not os.path.exists(DEST_DB_DIR):
            try:
                os.makedirs(DEST_DB_DIR)
                st.info(f"Diretório '{DEST_DB_DIR}' criado.")
            except OSError as e:
                st.error(f"Erro ao criar diretório '{DEST_DB_DIR}': {e}")
                return None

    if not os.path.exists(db_path):
        # Se for o banco de destino e ele não existe, a conexão sqlite3 o criará.
        # Se for o banco de origem, precisamos que ele exista.
        if db_path == SOURCE_DB_PATH:
             st.error(f"Erro: Banco de dados de origem não encontrado em '{db_path}'")
             return None
        else:
             st.warning(f"Aviso: Banco de dados de destino não encontrado em '{db_path}'. Ele será criado.")

    try:
        conn = sqlite3.connect(db_path)
        # conn.row_factory = sqlite3.Row # Descomente se quiser acesso por nome de coluna
        return conn
    except sqlite3.Error as e:
        st.error(f"Erro ao conectar/criar o banco de dados '{os.path.basename(db_path)}': {e}")
        return None

def sync_dados_placa_geral(source_conn, dest_conn, status_placeholder, progress_placeholder, results_placeholder):
    """Sincroniza a tabela dados_placa_geral."""
    st.write("--- Sincronizando Tabela: dados_placa_geral ---")
    status_placeholder.info("Lendo dados da tabela 'dados_placa_geral' de origem...")
    source_cursor = source_conn.cursor()
    dest_cursor = dest_conn.cursor()
    inserted_count = 0
    processed_count = 0

    try:
        # 1. Contar total de registros na origem para a barra de progresso
        source_cursor.execute("SELECT COUNT(*) FROM dados_placa_geral")
        total_rows = source_cursor.fetchone()[0]
        if total_rows == 0:
            status_placeholder.info("Tabela 'dados_placa_geral' de origem está vazia. Nada a sincronizar.")
            results_placeholder.success("Tabela 'dados_placa_geral': 0 novos registros inseridos.")
            return 0

        status_placeholder.info(f"Encontrados {total_rows} registros na origem. Verificando e inserindo novos no destino...")
        progress_bar = progress_placeholder.progress(0)

        # 2. Buscar todos os registros da origem
        source_cursor.execute("SELECT dt_data, ct_cota, cd_este, cd_norte, lc_local, pl_placa FROM dados_placa_geral")
        source_data = source_cursor.fetchall()

        # 3. Iterar e inserir no destino se não existir
        for row in source_data:
            dt_data, ct_cota, cd_este, cd_norte, lc_local, pl_placa = row
            processed_count += 1

            # Verificar se um registro "correspondente" já existe no destino.
            # Usamos pl_placa E dt_data como chave de verificação (ajuste se necessário)
            dest_cursor.execute(
                "SELECT 1 FROM dados_placa_geral WHERE pl_placa = ? AND dt_data = ?",
                (pl_placa, dt_data)
            )
            exists = dest_cursor.fetchone()

            if not exists:
                try:
                    # Inserir no destino, especificando as colunas que existem na origem.
                    # As colunas extras no destino (lp_local_placa, obs1, etc.) receberão NULL.
                    dest_cursor.execute(
                        """
                        INSERT INTO dados_placa_geral (dt_data, ct_cota, cd_este, cd_norte, lc_local, pl_placa)
                        VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        (dt_data, ct_cota, cd_este, cd_norte, lc_local, pl_placa)
                    )
                    inserted_count += 1
                except sqlite3.Error as e:
                    st.warning(f"Erro ao inserir linha (placa={pl_placa}, data={dt_data}) em 'dados_placa_geral': {e}. Pulando...")

            # Atualizar barra de progresso
            progress_bar.progress(processed_count / total_rows)

        # 4. Commit das alterações no banco de destino
        dest_conn.commit()
        results_placeholder.success(f"Tabela 'dados_placa_geral': {inserted_count} de {total_rows} registros eram novos e foram inseridos.")
        return inserted_count

    except sqlite3.Error as e:
        status_placeholder.error(f"Erro de Banco de Dados ao processar 'dados_placa_geral': {e}")
        results_placeholder.error("Falha na sincronização de 'dados_placa_geral'.")
        return -1 # Indica erro

def sync_placas_completas_slu_bh(source_conn, dest_conn, status_placeholder, progress_placeholder, results_placeholder):
    """Sincroniza a tabela placas_completas_slu_bh."""
    st.write("--- Sincronizando Tabela: placas_completas_slu_bh ---")
    status_placeholder.info("Lendo dados da tabela 'placas_completas_slu_bh' de origem...")
    source_cursor = source_conn.cursor()
    dest_cursor = dest_conn.cursor()
    inserted_count = 0
    processed_count = 0

    try:
        # 1. Contar total de registros na origem
        source_cursor.execute("SELECT COUNT(*) FROM placas_completas_slu_bh")
        total_rows = source_cursor.fetchone()[0]
        if total_rows == 0:
            status_placeholder.info("Tabela 'placas_completas_slu_bh' de origem está vazia. Nada a sincronizar.")
            results_placeholder.success("Tabela 'placas_completas_slu_bh': 0 novos registros inseridos.")
            return 0

        status_placeholder.info(f"Encontrados {total_rows} registros na origem. Verificando e inserindo novos no destino...")
        progress_bar = progress_placeholder.progress(0)

        # 2. Buscar todos os registros da origem
        source_cursor.execute("SELECT data, tipo, descricao, coordenada_este, coordenada_norte, elevacao, placa FROM placas_completas_slu_bh")
        source_data = source_cursor.fetchall()

        # 3. Iterar e inserir no destino se não existir
        for row in source_data:
            data, tipo, descricao, coord_este, coord_norte, elevacao, placa = row
            processed_count += 1

            # Verificar se um registro "correspondente" já existe no destino.
            # Usamos placa E data como chave de verificação (ajuste se necessário)
            dest_cursor.execute(
                "SELECT 1 FROM placas_completas_slu_bh WHERE placa = ? AND data = ?",
                (placa, data)
            )
            exists = dest_cursor.fetchone()

            if not exists:
                try:
                    # Inserir no destino, especificando as colunas que existem na origem.
                    # As colunas extras no destino (info_gerada, nome_arquivo) receberão NULL.
                    dest_cursor.execute(
                        """
                        INSERT INTO placas_completas_slu_bh (data, tipo, descricao, coordenada_este, coordenada_norte, elevacao, placa)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                        """,
                        (data, tipo, descricao, coord_este, coord_norte, elevacao, placa)
                    )
                    inserted_count += 1
                except sqlite3.Error as e:
                    st.warning(f"Erro ao inserir linha (placa={placa}, data={data}) em 'placas_completas_slu_bh': {e}. Pulando...")

            # Atualizar barra de progresso
            progress_bar.progress(processed_count / total_rows)

        # 4. Commit das alterações no banco de destino
        dest_conn.commit()
        results_placeholder.success(f"Tabela 'placas_completas_slu_bh': {inserted_count} de {total_rows} registros eram novos e foram inseridos.")
        return inserted_count

    except sqlite3.Error as e:
        status_placeholder.error(f"Erro de Banco de Dados ao processar 'placas_completas_slu_bh': {e}")
        results_placeholder.error("Falha na sincronização de 'placas_completas_slu_bh'.")
        return -1 # Indica erro

# --- Interface Streamlit ---

st.set_page_config(page_title="Sincronizar BD", layout="wide")

st.title(" ferramenta de Sincronização de Banco de Dados")
st.markdown(f"""
Esta ferramenta compara o banco de dados de origem (`{os.path.basename(SOURCE_DB_PATH)}`)
com o banco de dados de destino (`{os.path.join(os.path.basename(DEST_DB_DIR), DEST_DB_NAME)}`)
e adiciona **apenas** os registros novos do origem ao destino.

**Importante:** Nenhum dado existente no banco de destino será modificado ou excluído.
As tabelas sincronizadas são: `dados_placa_geral` e `placas_completas_slu_bh`.
""")

st.sidebar.header("Ações")
sync_button = st.sidebar.button("Iniciar Sincronização Agora", key="sync_db")

# Placeholders para mensagens e barras de progresso
status_placeholder = st.empty()
progress_placeholder_1 = st.empty()
results_placeholder_1 = st.empty()
progress_placeholder_2 = st.empty()
results_placeholder_2 = st.empty()
summary_placeholder = st.empty()

if sync_button:
    start_time = time.time()
    status_placeholder.info("Iniciando processo...")
    time.sleep(0.5) # Pequena pausa visual

    source_conn = None
    dest_conn = None
    total_inserted = 0
    error_occurred = False

    try:
        # Conectar aos bancos de dados
        status_placeholder.info(f"Conectando ao banco de dados de origem: {SOURCE_DB_PATH}")
        source_conn = connect_db(SOURCE_DB_PATH)
        time.sleep(0.5)

        status_placeholder.info(f"Conectando ao banco de dados de destino: {DEST_DB_PATH}")
        dest_conn = connect_db(DEST_DB_PATH)
        time.sleep(0.5)

        if source_conn and dest_conn:
            status_placeholder.info("Conexões estabelecidas. Iniciando sincronização...")

            # Sincronizar Tabela 1
            inserted_1 = sync_dados_placa_geral(source_conn, dest_conn, status_placeholder, progress_placeholder_1, results_placeholder_1)
            if inserted_1 == -1: error_occurred = True
            else: total_inserted += inserted_1
            time.sleep(1) # Pausa entre tabelas

            # Sincronizar Tabela 2 (só continua se a primeira não deu erro fatal)
            if not error_occurred:
                 inserted_2 = sync_placas_completas_slu_bh(source_conn, dest_conn, status_placeholder, progress_placeholder_2, results_placeholder_2)
                 if inserted_2 == -1: error_occurred = True
                 else: total_inserted += inserted_2
                 time.sleep(1)

            # Mensagem final
            elapsed_time = time.time() - start_time
            if not error_occurred:
                summary_placeholder.success(f"Sincronização concluída em {elapsed_time:.2f} segundos. Total de {total_inserted} novos registros inseridos nas duas tabelas.")
            else:
                summary_placeholder.error(f"Sincronização concluída com erros em {elapsed_time:.2f} segundos. Verifique as mensagens acima.")

        else:
            summary_placeholder.error("Falha ao conectar a um ou ambos os bancos de dados. Verifique os caminhos e permissões.")
            error_occurred = True

    except Exception as e:
        st.error(f"Ocorreu um erro inesperado durante o processo: {e}")
        summary_placeholder.error("Sincronização falhou devido a um erro inesperado.")
        error_occurred = True

    finally:
        # Garantir que as conexões sejam fechadas
        status_placeholder.info("Fechando conexões com os bancos de dados...")
        if source_conn:
            source_conn.close()
        if dest_conn:
            dest_conn.close()
        status_placeholder.info("Conexões fechadas.")
        # Limpar placeholders de progresso se não houve erro fatal para não ficarem na tela
        if not error_occurred:
            time.sleep(2) # Espera para o usuário ler o resultado final
            progress_placeholder_1.empty()
            progress_placeholder_2.empty()


else:
    st.info("Clique no botão 'Iniciar Sincronização Agora' na barra lateral para começar.")

# Opcional: Mostrar informações sobre os bancos (ex: últimas N entradas no destino)
# ... (código para consultar e mostrar dados do BD destino, se desejado) ...