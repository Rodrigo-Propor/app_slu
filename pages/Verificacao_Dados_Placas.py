import streamlit as st
import sqlite3
import pandas as pd

def verificar_estrutura_banco():
    """Verifica e cria a estrutura necessária do banco de dados"""
    try:
        conn = sqlite3.connect('banco_dados.db')
        cursor = conn.cursor()

        # Verifica se a tabela existe
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='placas_completas_slu_bh'
        """)
        
        if not cursor.fetchone():
            cursor.execute("""
                CREATE TABLE placas_completas_slu_bh (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    data TEXT,
                    tipo TEXT,
                    descricao TEXT,
                    coordenada_este REAL,
                    coordenada_norte REAL,
                    elevacao REAL,
                    placa TEXT
                )
            """)
            conn.commit()
            st.success("Tabela placas_completas_slu_bh criada com sucesso!")
        
        # Verifica se todas as colunas necessárias existem
        cursor.execute("PRAGMA table_info(placas_completas_slu_bh)")
        colunas_existentes = {row[1] for row in cursor.fetchall()}
        
        colunas_necessarias = {
            'id', 'data', 'tipo', 'descricao', 
            'coordenada_este', 'coordenada_norte', 
            'elevacao', 'placa'
        }
        
        colunas_faltantes = colunas_necessarias - colunas_existentes
        
        if colunas_faltantes:
            st.warning(f"Colunas faltantes: {', '.join(colunas_faltantes)}")
            for coluna in colunas_faltantes:
                tipo_coluna = "REAL" if coluna in ['coordenada_este', 'coordenada_norte', 'elevacao'] else "TEXT"
                cursor.execute(f"ALTER TABLE placas_completas_slu_bh ADD COLUMN {coluna} {tipo_coluna}")
            conn.commit()
            st.success("Colunas adicionadas com sucesso!")
        
        return True

    except sqlite3.Error as e:
        st.error(f"Erro no banco de dados: {str(e)}")
        return False
    finally:
        conn.close()

def verificar_duplicados():
    """Verifica registros duplicados na tabela dados_placa_geral"""
    conn = sqlite3.connect('banco_dados.db')
    query = """
    SELECT cd_este, cd_norte, dt_data, pl_placa, COUNT(*) as contagem
    FROM dados_placa_geral
    GROUP BY cd_este, cd_norte, dt_data, pl_placa
    HAVING COUNT(*) > 1
    """
    duplicados = pd.read_sql_query(query, conn)
    conn.close()
    return duplicados

def verificar_colunas_disponiveis():
    """Verifica todas as colunas disponíveis nas tabelas"""
    try:
        conn = sqlite3.connect('banco_dados.db')
        cursor = conn.cursor()

        # Verifica colunas da tabela dados_placa_geral
        cursor.execute("PRAGMA table_info(dados_placa_geral)")
        colunas_origem = {row[1]: row[2] for row in cursor.fetchall()}

        # Verifica colunas da tabela placas_completas_slu_bh
        cursor.execute("PRAGMA table_info(placas_completas_slu_bh)")
        colunas_destino = {row[1]: row[2] for row in cursor.fetchall()}

        # Amostra de dados para análise
        df_origem = pd.read_sql("SELECT * FROM dados_placa_geral LIMIT 5", conn)
        
        info_colunas = pd.DataFrame({
            'Coluna': list(colunas_origem.keys()),
            'Tipo': list(colunas_origem.values()),
            'Exemplo': [df_origem[col].iloc[0] if col in df_origem else None 
                       for col in colunas_origem],
            'Não Nulos (%)': [
                round((df_origem[col].count() / len(df_origem)) * 100, 2) 
                if col in df_origem else 0 
                for col in colunas_origem
            ]
        })

        conn.close()
        return info_colunas, colunas_destino
    except Exception as e:
        st.error(f"Erro ao verificar colunas: {str(e)}")
        return None, None

def obter_dados_validos():
    """Obtém dados válidos que podem ser transferidos"""
    conn = sqlite3.connect('banco_dados.db')
    colunas_base = """
        dt_data as data,
        lc_local as tipo,
        obs3 as descricao,
        cd_este as coordenada_este,
        cd_norte as coordenada_norte,
        ct_cota as elevacao,
        pl_placa as placa
    """
    
    colunas_adicionais = ""
    if 'colunas_adicionais' in st.session_state:
        colunas_adicionais = "," + ",".join(st.session_state.colunas_adicionais)
    
    query = f"""
    SELECT DISTINCT 
        {colunas_base}
        {colunas_adicionais}
    FROM dados_placa_geral
    WHERE cd_este IS NOT NULL 
        AND cd_norte IS NOT NULL 
        AND ct_cota IS NOT NULL
        AND lc_local IS NOT NULL
        AND pl_placa IS NOT NULL
        AND pl_placa NOT LIKE '%LEV%'
        AND pl_placa NOT LIKE '%TOP%'
    """
    dados_validos = pd.read_sql_query(query, conn)
    conn.close()
    return dados_validos

def transferir_dados(dados_df):
    """Transfere dados válidos para placas_completas_slu_bh"""
    conn = sqlite3.connect('banco_dados.db')
    cursor = conn.cursor()
    
    total_registros = len(dados_df)
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for idx, row in dados_df.iterrows():
        colunas = ['data', 'tipo', 'descricao', 'coordenada_este', 
                  'coordenada_norte', 'elevacao', 'placa']
        valores = [row[col] for col in colunas]
        
        if 'colunas_adicionais' in st.session_state:
            colunas.extend(st.session_state.colunas_adicionais)
            valores.extend([row[col] for col in st.session_state.colunas_adicionais])
        
        placeholders = ','.join(['?' for _ in valores])
        query = f"""
            INSERT INTO placas_completas_slu_bh 
            ({','.join(colunas)})
            VALUES ({placeholders})
        """
        cursor.execute(query, valores)
        
        # Atualiza progresso
        progress = (idx + 1) / total_registros
        progress_bar.progress(progress)
        status_text.text(f"Processando... {idx+1}/{total_registros} registros")
    
    conn.commit()
    conn.close()
    status_text.text("Transferência concluída!")
    return total_registros

def main():
    st.title("Verificação e Transferência de Dados das Placas")
    
    # Inicializa estados da sessão
    if 'processo_iniciado' not in st.session_state:
        st.session_state.processo_iniciado = False
    if 'processo_concluido' not in st.session_state:
        st.session_state.processo_concluido = False
    
    st.write("""
    ### O que este processo faz:
    1. Verifica e cria a estrutura necessária do banco de dados
    2. Verifica registros duplicados na tabela dados_placa_geral
    3. Identifica dados válidos que podem ser transferidos
    4. Transfere apenas dados que tenham as informações mínimas:
        - Data do registro
        - Tipo do local
        - Descrição
        - Coordenadas (Este e Norte)
        - Elevação
        - Identificação da placa
    5. Exclui informações de levantamentos topográficos
    """)

    # Verifica estrutura do banco
    if not verificar_estrutura_banco():
        st.error("Erro na estrutura do banco de dados. Corrija os problemas antes de continuar.")
        return

    # Verifica duplicados
    if st.button("Verificar Registros Duplicados"):
        duplicados = verificar_duplicados()
        if not duplicados.empty:
            st.warning("Encontrados registros duplicados:")
            st.dataframe(duplicados)
        else:
            st.success("Não foram encontrados registros duplicados!")

    # Adicione uma nova seção para análise de colunas
    st.subheader("Análise de Colunas Disponíveis")
    
    info_colunas, colunas_destino = verificar_colunas_disponiveis()
    if info_colunas is not None:
        st.write("### Colunas disponíveis na tabela de origem:")
        st.dataframe(info_colunas)
        
        st.write("### Colunas adicionais que podem ser relevantes:")
        colunas_complementares = info_colunas[
            (info_colunas['Não Nulos (%)'] > 50) & 
            (~info_colunas['Coluna'].isin(['id', 'data', 'tipo', 'descricao', 
                                         'coordenada_este', 'coordenada_norte', 
                                         'elevacao', 'placa']))
        ]
        
        if not colunas_complementares.empty:
            st.dataframe(colunas_complementares)
            
            # Permite ao usuário selecionar colunas adicionais
            colunas_selecionadas = st.multiselect(
                "Selecione colunas adicionais para transferir:",
                options=colunas_complementares['Coluna'].tolist()
            )
            
            if colunas_selecionadas:
                st.session_state.colunas_adicionais = colunas_selecionadas
        else:
            st.info("Não foram encontradas colunas complementares relevantes.")

    # Mostra dados válidos
    st.subheader("Dados Válidos para Transferência")
    dados_validos = obter_dados_validos()
    st.dataframe(dados_validos)
    
    st.write(f"Total de registros válidos encontrados: {len(dados_validos)}")

    # Botão de confirmação e processamento
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Iniciar Transferência", type="primary"):
            st.session_state.processo_iniciado = True
    
    with col2:
        if st.session_state.processo_iniciado and not st.session_state.processo_concluido:
            if st.checkbox("Confirmar transferência dos dados"):
                try:
                    with st.spinner('Transferindo dados...'):
                        total_transferidos = transferir_dados(dados_validos)
                        st.session_state.processo_concluido = True
                        st.success(f"""
                            Transferência concluída com sucesso!
                            - Total de registros transferidos: {total_transferidos}
                            - Data/Hora: {pd.Timestamp.now().strftime('%d/%m/%Y %H:%M:%S')}
                        """)
                except Exception as e:
                    st.error(f"Erro durante a transferência: {str(e)}")
                finally:
                    # Botão para reiniciar o processo
                    if st.button("Iniciar Nova Transferência"):
                        st.session_state.processo_iniciado = False
                        st.session_state.processo_concluido = False
                        st.rerun()

if __name__ == "__main__":
    main()