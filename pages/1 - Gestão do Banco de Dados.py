import streamlit as st
import sqlite3
import pandas as pd
import os
from sqlite3 import Error

# Configuração inicial do Streamlit
st.set_page_config(
    page_title="Gerenciador de Banco de Dados",
    page_icon="🗃️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Função para conectar ao banco de dados
def create_connection(db_file: str):
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except Error as e:
        st.error(f"Erro ao conectar ao banco de dados: {e}")
        return None

# Função para obter todas as tabelas do banco
def get_tables(conn):
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        return [table[0] for table in tables]
    except Error as e:
        st.error(f"Erro ao obter tabelas: {e}")
        return []

# Função para obter estrutura da tabela
def get_table_structure(conn, table_name):
    try:
        cursor = conn.cursor()
        cursor.execute(f"PRAGMA table_info({table_name});")
        return cursor.fetchall()
    except Error as e:
        st.error(f"Erro ao obter estrutura da tabela: {e}")
        return []

# Função para obter dados da tabela
def get_table_data(conn, table_name):
    try:
        return pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
    except Error as e:
        st.error(f"Erro ao obter dados da tabela: {e}")
        return pd.DataFrame()

# Função para executar query SQL
def execute_query(conn, query):
    try:
        cursor = conn.cursor()
        cursor.execute(query)
        conn.commit()
        return True
    except Error as e:
        st.error(f"Erro ao executar query: {e}")
        return False

# Sidebar - seleção de banco de dados
st.sidebar.title("🗃️ Gerenciador de BD")

# Lista os arquivos .db disponíveis na pasta atual
db_files = [f for f in os.listdir('.') if f.endswith('.db')]
if not db_files:
    st.sidebar.error("Nenhum banco de dados encontrado na pasta atual.")
    conn = None
else:
    selected_db = st.sidebar.selectbox("Selecione o banco de dados", db_files)
    conn = create_connection(selected_db)

if conn is not None:
    tables = get_tables(conn)
    
    # Menu principal
    operation = st.sidebar.selectbox(
        "Selecione a operação",
        ["📊 Visualizar Tabelas", "➕ Criar Tabela", "✏️ Editar Dados", "❌ Excluir Tabela", "📝 SQL Query"]
    )

    if operation == "📊 Visualizar Tabelas":
        st.title("📊 Visualizar Tabelas")
        if tables:
            selected_table = st.selectbox("Selecione uma tabela", tables)
            
            # Estrutura da tabela em um expander
            with st.expander("Estrutura da Tabela", expanded=False):
                structure = get_table_structure(conn, selected_table)
                structure_df = pd.DataFrame(structure, columns=['ID', 'Nome', 'Tipo', 'NotNull', 'Default', 'PK'])
                st.dataframe(structure_df)

            # Dados da tabela em um expander
            with st.expander("Dados da Tabela", expanded=True):
                data = get_table_data(conn, selected_table)
                st.dataframe(data, use_container_width=True)

    elif operation == "➕ Criar Tabela":
        st.title("➕ Criar Nova Tabela")
        
        with st.expander("Criar Nova Tabela", expanded=True):
            table_name = st.text_input("Nome da tabela")
            num_columns = st.number_input("Número de colunas", min_value=1, max_value=20, value=1)
            
            if table_name:
                columns = []
                st.subheader("Definir Colunas")
                cols = st.columns(3)
                
                for i in range(num_columns):
                    with cols[0]:
                        col_name = st.text_input(f"Nome da coluna {i+1}", key=f"nome_{i}")
                    with cols[1]:
                        col_type = st.selectbox(f"Tipo da coluna {i+1}", 
                                                ["INTEGER", "TEXT", "REAL", "BLOB", "DATE"], key=f"tipo_{i}")
                    with cols[2]:
                        col_pk = st.checkbox(f"Chave Primária {i+1}", key=f"pk_{i}")
                        col_notnull = st.checkbox(f"Not Null {i+1}", key=f"notnull_{i}")
                    
                    if col_name:
                        column_def = f"{col_name} {col_type}"
                        if col_pk:
                            column_def += " PRIMARY KEY"
                        if col_notnull:
                            column_def += " NOT NULL"
                        columns.append(column_def)
                
                if st.button("Criar Tabela"):
                    query = f"CREATE TABLE {table_name} ({', '.join(columns)})"
                    if execute_query(conn, query):
                        st.success("Tabela criada com sucesso!")
                        st.experimental_rerun()

    elif operation == "✏️ Editar Dados":
        st.title("✏️ Editar Dados")
        
        if tables:
            selected_table = st.selectbox("Selecione uma tabela para editar", tables)
            data = get_table_data(conn, selected_table)
            
            # Adicionar novo registro em um expander
            with st.expander("Adicionar Novo Registro", expanded=False):
                columns = data.columns
                new_data = {}
                cols = st.columns(len(columns))
                
                for i, col in enumerate(columns):
                    with cols[i]:
                        new_data[col] = st.text_input(f"Novo {col}", key=f"novo_{col}")
                
                if st.button("Adicionar Registro"):
                    cols_str = ", ".join(columns)
                    vals_str = ", ".join([f"'{v}'" if v else "NULL" for v in new_data.values()])
                    query = f"INSERT INTO {selected_table} ({cols_str}) VALUES ({vals_str})"
                    if execute_query(conn, query):
                        st.success("Registro adicionado com sucesso!")
                        st.experimental_rerun()
            
            # Editar registros existentes em um expander
            with st.expander("Registros Existentes", expanded=True):
                edited_df = st.data_editor(
                    data,
                    num_rows="dynamic",
                    use_container_width=True
                )
                
                if st.button("Salvar Alterações"):
                    execute_query(conn, f"DELETE FROM {selected_table}")
                    for _, row in edited_df.iterrows():
                        cols_str = ", ".join(columns)
                        vals_str = ", ".join([f"'{v}'" if pd.notna(v) else "NULL" for v in row])
                        query = f"INSERT INTO {selected_table} ({cols_str}) VALUES ({vals_str})"
                        execute_query(conn, query)
                    st.success("Alterações salvas com sucesso!")

    elif operation == "❌ Excluir Tabela":
        st.title("❌ Excluir Tabela")
        
        with st.expander("Excluir Tabela", expanded=True):
            if tables:
                selected_table = st.selectbox("Selecione uma tabela para excluir", tables)
                
                if st.button("Excluir Tabela", type="primary"):
                    confirm = st.checkbox("Confirmar exclusão")
                    
                    if confirm:
                        query = f"DROP TABLE {selected_table}"
                        if execute_query(conn, query):
                            st.success("Tabela excluída com sucesso!")
                            st.experimental_rerun()

    elif operation == "📝 SQL Query":
        st.title("📝 Editor SQL")
        
        with st.expander("Editor SQL", expanded=True):
            query = st.text_area("Digite sua query SQL", height=200)
            
            if st.button("Executar Query"):
                try:
                    if query.lower().strip().startswith("select"):
                        result = pd.read_sql_query(query, conn)
                        st.dataframe(result)
                    else:
                        if execute_query(conn, query):
                            st.success("Query executada com sucesso!")
                            if not query.lower().startswith("select"):
                                st.experimental_rerun()
                except Exception as e:
                    st.error(f"Erro ao executar query: {e}")

    # Mostrar informações do banco de dados
    st.sidebar.markdown("---")
    st.sidebar.subheader("Informações do Banco")
    st.sidebar.info(f"Número de tabelas: {len(tables)}")
    st.sidebar.info(f"Tabelas: {', '.join(tables)}")

else:
    st.error("Não foi possível conectar ao banco de dados!")

# Fechar conexão
if conn:
    conn.close()
