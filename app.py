import streamlit as st
import os
import sqlite3
from datetime import datetime
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder
from st_aggrid import GridUpdateMode, DataReturnMode

# Configurações da página
st.set_page_config(
    page_title="Propor Engenharia Ltda.",
    page_icon="images/favicon.ico",
    layout="wide"
)

# Funções do banco de dados
def get_last_period():
    """Função para obter o último período registrado"""
    conn = sqlite3.connect("banco_dados.db")
    cursor = conn.cursor()
    cursor.execute("SELECT mes, ano_contrato FROM SLU_periodos ORDER BY id DESC LIMIT 1")
    result = cursor.fetchone()
    conn.close()
    return result if result else (1, 'Ano 1')

def get_file_records(mes_atual, ano_atual):
    """Função para obter registros filtrados do banco de dados"""
    conn = sqlite3.connect("banco_dados.db")
    cursor = conn.cursor()
    
    # Primeiro, verifica se a coluna referencia existe
    cursor.execute("PRAGMA table_info(SLU_files)")
    colunas = [coluna[1] for coluna in cursor.fetchall()]
    
    # Monta a query baseada na existência da coluna
    if 'referencia' in colunas:
        query = """
        SELECT id, tipo, mes, ano_contrato, caminho_arquivo, ativo, 
               data_carregamento, data_remocao, referencia 
        FROM SLU_files 
        WHERE mes = ? AND ano_contrato = ? AND ativo = 1
        ORDER BY data_carregamento DESC
        """
    else:
        query = """
        SELECT id, tipo, mes, ano_contrato, caminho_arquivo, ativo, 
               data_carregamento, data_remocao, NULL as referencia
        FROM SLU_files 
        WHERE mes = ? AND ano_contrato = ? AND ativo = 1
        ORDER BY data_carregamento DESC
        """
    
    cursor.execute(query, (mes_atual, ano_atual))
    records = cursor.fetchall()
    conn.close()
    return records

def save_file_record(tipo, mes, ano, caminho_arquivo):
    """Função para salvar registro do arquivo no banco de dados"""
    conn = sqlite3.connect("banco_dados.db")
    cursor = conn.cursor()
    current_date = datetime.now().strftime('%Y-%m-%d')
    cursor.execute("""
    INSERT INTO SLU_files (tipo, mes, ano_contrato, caminho_arquivo, ativo, data_carregamento)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (tipo, mes, ano, caminho_arquivo, 1, current_date))
    conn.commit()
    conn.close()

def configure_grid(df):
    """Configura as opções do AgGrid"""
    gb = GridOptionsBuilder.from_dataframe(df)
    
    # Configurações das colunas
    gb.configure_column("ID", width=70)
    gb.configure_column("Tipo", width=150, filter=True)
    gb.configure_column("Mês", width=90, filter=True)
    gb.configure_column("Ano do Contrato", width=130, filter=True)
    gb.configure_column("Caminho do Arquivo", width=300, filter=True)
    gb.configure_column("Ativo", width=90, hide=True)
    gb.configure_column("Data de Carregamento", width=150, filter=True)
    gb.configure_column("Data de Remoção", width=150, filter=True)
    gb.configure_column("Referência", width=150, filter=True)
    
    # Configurações gerais da grid
    gb.configure_selection('multiple', use_checkbox=True, rowMultiSelectWithClick=True)
    gb.configure_side_bar()
    gb.configure_default_column(
        groupable=True,
        value=True,
        enableRowGroup=True,
        aggFunc='sum',
        editable=False
    )
    
    return gb.build()

# Criando um container para o cabeçalho
header = st.container()
col1, col2, col3 = header.columns([4, 4, 2])

with col1:
    st.title("Relatório SLU")

with col3:
    st.image(
        "images/logo_propor.jpg",
        width=200,
        output_format="PNG"
    )

st.markdown("---")

# Criando as tabs
tab1, tab2, tab3 = st.tabs(["📊 Carregar dados", "📈 Processa Coordenadas", "💰 Gera o Relatório"])


################################XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX#########################################

with tab1:
    # Obtém o último período registrado
    last_mes, last_ano = get_last_period()
    
    # Container para seleção de período e tipo de arquivo
    col1, col2, col3 = st.columns(3)
    
    with col1:
        mes = st.selectbox("Mês", 
                          options=list(range(1, 13)), 
                          format_func=lambda x: f"{x:02d}",
                          index=last_mes-1)
    
    with col2:
        ano_contrato = st.selectbox("Ano do Contrato",
                                   options=[f"Ano {i}" for i in range(1, 11)],
                                   index=int(last_ano.replace('Ano ', ''))-1)
    
    with col3:
        tipo_arquivo = st.selectbox(
            "Tipo de Arquivo",
            ["Foto", "Medição de Placa", "Topografia de Terreno", "Diário de Obra", "Levantamento Topográfico"]
        )

    # Upload de arquivos
    uploaded_files = st.file_uploader("Escolha os arquivos para upload", accept_multiple_files=True)
    if uploaded_files:
        for uploaded_file in uploaded_files:
            nome_arquivo = f"{tipo_arquivo}_{mes}_{ano_contrato}_{uploaded_file.name}"
            file_path = os.path.join("media", nome_arquivo)
            
            # Garante que o diretório media existe
            os.makedirs("media", exist_ok=True)
            
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            save_file_record(
                tipo=tipo_arquivo,
                mes=mes,
                ano=ano_contrato,
                caminho_arquivo=file_path
            )
            st.success(f"Arquivo {nome_arquivo} carregado com sucesso!")

    # Exibe tabela com todos os arquivos
    st.subheader("Arquivos Carregados")
    records = get_file_records(mes, ano_contrato)

    if records:
        df = pd.DataFrame(
            records,
            columns=['ID', 'Tipo', 'Mês', 'Ano do Contrato', 'Caminho do Arquivo', 'Ativo', 
                    'Data de Carregamento', 'Data de Remoção', 'Referência']
        )
        
        # Formatação das datas
        date_columns = ['Data de Carregamento', 'Data de Remoção']
        for col in date_columns:
            df[col] = pd.to_datetime(df[col], errors='coerce').dt.strftime('%Y-%m-%d')
        
        # Configurar e exibir AgGrid
        gridOptions = configure_grid(df)
        grid_response = AgGrid(
            df,
            gridOptions=gridOptions,
            height=400,
            enable_enterprise_modules=False,
            update_mode=GridUpdateMode.MODEL_CHANGED | GridUpdateMode.SELECTION_CHANGED,
            data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
            fit_columns_on_grid_load=True,
            allow_unsafe_jscode=True
        )
        
        # Obter dados selecionados da grid e converter para lista se necessário
        selected_rows = grid_response['selected_rows']

        try:
            if selected_rows is None:  # Verifica se selected_rows é None
                selected_rows = []  # Define como uma lista vazia se for None
            elif not isinstance(selected_rows, list):  # Se não for None nem list, converte
                selected_rows = selected_rows.to_dict('records')
        except Exception as e:
            st.error(f"Erro ao processar seleção: {str(e)}")
            selected_rows = []
        
        # Seção de classificação
        if selected_rows:
            st.markdown("---")  # Adiciona uma linha divisória
            st.subheader("Classificação dos Arquivos Selecionados")
            
            # Exibe quantos arquivos foram selecionados
            st.info(f"{len(selected_rows)} arquivo(s) selecionado(s) para classificação")
            
            grupo = st.selectbox(
                "Classificar arquivos selecionados como:",
                [
                    "Célula Emergencial",
                    "Célula de Pesquisa",
                    "Célula da Pampulha",
                    "Inclinômetro",
                    "Levantamento Topográfico"
                ]
            )

            if st.button("Salvar Classificação"):
                conn = sqlite3.connect("banco_dados.db")
                cursor = conn.cursor()
                
                # Verifica se a coluna existe
                cursor.execute("PRAGMA table_info(SLU_files)")
                colunas = cursor.fetchall()
                coluna_existe = any(coluna[1] == 'referencia' for coluna in colunas)
                
                # Se a coluna não existe, cria ela
                if not coluna_existe:
                    try:
                        cursor.execute("ALTER TABLE SLU_files ADD COLUMN referencia TEXT")
                        conn.commit()
                    except sqlite3.OperationalError as e:
                        st.error(f"Erro ao criar coluna: {e}")
                        conn.close()
                        st.stop()
                
                # Atualiza os registros
                try:
                    for row in selected_rows:
                        cursor.execute("""
                        UPDATE SLU_files 
                        SET referencia = ? 
                        WHERE caminho_arquivo = ?
                        """, (grupo, row['Caminho do Arquivo']))
                    conn.commit()
                    st.success("Classificação salva com sucesso!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao salvar classificação: {e}")
                finally:
                    conn.close()
    else:
        st.info("Nenhum arquivo encontrado para o período selecionado.")

########################xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx######################################

with tab2:
    st.write("### Processamento das coordenadas - incorporar os códigos já elaborados")
    


##############################xXxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx###########################################


with tab3:
    st.write("### Gerar o Relatório da Medição")

