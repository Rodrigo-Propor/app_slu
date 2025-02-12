import sqlite3
import pandas as pd
import streamlit as st

# Caminho do arquivo da planilha e do banco de dados
excel_path = 'media/template/dados_ate_outubro_24.xlsx'
db_path = 'banco_dados.db'

# Título do aplicativo Streamlit
st.title("Importação de Dados para Banco de Dados")

# Caixa de diálogo para confirmação
if st.checkbox("Deseja atualizar o banco de dados com os dados do arquivo Excel?"):
    # Conectar ao banco de dados (corrigido usando st.cache_resource)
    @st.cache_resource
    def init_connection():
        return sqlite3.connect(db_path, check_same_thread=False)

    try:
        conn = init_connection()
        cursor = conn.cursor()

        # Verificar se a tabela existe, caso contrário, criar
        table_name = 'dados_placa_geral'
        cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS {table_name} (
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
        ''')
        st.write("Tabela 'dados_placa_geral' verificada/criada com sucesso.")

        # Barra de progresso
        progress_bar = st.progress(0)
        status_text = st.empty()

        try:
            data_df = pd.read_excel(excel_path, usecols="A:J")
            data_df.columns = ["dt_data", "ct_cota", "cd_este", "cd_norte", "lc_local", "pl_placa", "lp_local_placa", "obs1", "obs2", "obs3"]
        except FileNotFoundError:
            st.error(f"Arquivo não encontrado: {excel_path}")
            st.stop()
        except Exception as e:
            st.error(f"Erro ao ler arquivo Excel: {e}")
            st.stop()

        # Converter colunas para os tipos adequados
        for col in ["ct_cota", "cd_este", "cd_norte"]:
            data_df[col] = pd.to_numeric(data_df[col], errors='coerce')

        data_df["dt_data"] = pd.to_datetime(data_df["dt_data"], errors='coerce').dt.strftime('%Y-%m-%d')

        # Remover linhas com valores inválidos nas colunas principais
        data_df.dropna(subset=["dt_data", "ct_cota", "cd_este", "cd_norte"], inplace=True)

        if data_df.empty:
            st.warning("Nenhum dado válido encontrado após limpeza. Verifique os dados na planilha.")
            st.stop()

        # Ordenar os dados
        data_df.sort_values(by=["dt_data", "lc_local", "pl_placa"], inplace=True)

        # Contadores e listas para exibir no Streamlit
        registros_copiados = 0
        registros_duplicados = 0
        registros_duplicados_lista = []
        registros_invalidos = 0
        erros_insercao = 0
        erros_insercao_lista = []

        total_registros = len(data_df)

        # Inserir dados no banco de dados
        for i, row in data_df.iterrows():
            dt_data = row["dt_data"]
            ct_cota = row["ct_cota"]
            cd_este = row["cd_este"]
            cd_norte = row["cd_norte"]

            # Verificação dos critérios de faixa
            if not (100 <= ct_cota <= 999.999 and 600000 <= cd_este <= 699999.999 and 7000000 <= cd_norte <= 7999999.999):
                registros_invalidos += 1
                continue  # Pula para a próxima iteração

            # Verificar duplicata
            cursor.execute(f'''
                SELECT COUNT(*) FROM {table_name} 
                WHERE dt_data = ? AND cd_norte = ? AND cd_este = ? AND ct_cota = ?
            ''', (dt_data, cd_norte, cd_este, ct_cota))

            if cursor.fetchone()[0] == 0:  # Registro único
                try:
                    cursor.execute(f'''
                        INSERT INTO {table_name} 
                        (dt_data, ct_cota, cd_este, cd_norte, lc_local, pl_placa, lp_local_placa, obs1, obs2, obs3)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (dt_data, ct_cota, cd_este, cd_norte, row["lc_local"], row["pl_placa"], row["lp_local_placa"], row["obs1"], row["obs2"], row["obs3"]))
                    registros_copiados += 1
                except Exception as e:
                    erros_insercao += 1
                    erros_insercao_lista.append(f"Erro ao inserir registro {row}: {e}")

            else:
                registros_duplicados += 1
                registros_duplicados_lista.append((dt_data, cd_norte, cd_este, ct_cota))

            # Atualizar barra de progresso e informações no Streamlit
            progress_percent = (i + 1) / total_registros
            progress_percent = round(progress_percent, 3)  # arredonda para 3 casas decimais
            if progress_percent > 1:  # impede que passe de 1
                progress_percent = 1
            progress_bar.progress(progress_percent)
            status_text.write(f"Progresso: {progress_percent:.2%}, Registros processados: {i + 1}/{total_registros}, Copiados: {registros_copiados}, Duplicados: {registros_duplicados}, Inválidos: {registros_invalidos}, Erros Inserção:{erros_insercao}")

        # Salvar as alterações no banco de dados
        conn.commit()

        # Exibir resumo no Streamlit
        st.write(f"\n**Processo concluído!**")
        st.write(f"Registros copiados: {registros_copiados}")
        st.write(f"Registros duplicados ignorados: {registros_duplicados}")
        st.write(f"Registros inválidos removidos: {registros_invalidos}")
        if erros_insercao > 0:
            st.error(f"Erros na inserção: {erros_insercao}")
            for erro in erros_insercao_lista:
                st.write(erro)
        if registros_duplicados > 0:
            st.write("**Detalhes dos registros duplicados:**")
            for registro in registros_duplicados_lista:
                st.write(registro)

    except Exception as e:
        st.error(f"Erro geral: {e}")

    finally:
        try:
            conn.close()
        except Exception as e:
            st.error(f"Erro ao fechar conexão: {e}")
else:
    st.write("A atualização do banco de dados não foi confirmada.")