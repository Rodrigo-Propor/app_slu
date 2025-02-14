import streamlit as st
import os
import pandas as pd
from datetime import datetime
import sqlite3

def transform_tipo(tipo):
    tipo = tipo.upper()
    mapeamento = {
        "EM": "CELULA EMERGENCIAL",
        "IC": "INCLINOMETRO",
        "LV": "LEVANTAMENTO TOPOGRÁFICO",
        "PA": "PAMPULHA",
        "PE": "CELULA DE PESQUISA"
    }
    
    for prefixo, valor in mapeamento.items():
        if tipo.startswith(prefixo):
            return valor
    return tipo

def init_db():
    conn = sqlite3.connect('arquivos.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS arquivos
                 (nome_arquivo TEXT PRIMARY KEY, 
                  tipo TEXT, 
                  dia INTEGER, 
                  mes INTEGER, 
                  ano INTEGER,
                  registros INTEGER)''')
    conn.commit()
    conn.close()

def verificar_arquivo_existente(nome_arquivo):
    conn = sqlite3.connect('arquivos.db')
    c = conn.cursor()
    c.execute("SELECT * FROM arquivos WHERE nome_arquivo = ?", (nome_arquivo,))
    resultado = c.fetchone()
    conn.close()
    return resultado is not None

def salvar_arquivo_db(dados):
    conn = sqlite3.connect('arquivos.db')
    c = conn.cursor()
    try:
        c.execute("""INSERT INTO arquivos (nome_arquivo, tipo, dia, mes, ano, registros) 
                     VALUES (?, ?, ?, ?, ?, ?)""", dados)
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def buscar_arquivos_db():
    conn = sqlite3.connect('arquivos.db')
    try:
        df = pd.read_sql_query("""
            SELECT nome_arquivo, tipo, dia, mes, ano, registros 
            FROM arquivos""", conn)
        return df
    except Exception as e:
        st.error(f"Erro ao buscar dados do banco: {str(e)}")
        return pd.DataFrame()
    finally:
        conn.close()

st.title("Processamento de Arquivos TXT")
st.write("### Configure as datas dos arquivos")

# Define o caminho da pasta
folder_path = "media/originais_txt"

# Tenta ler os arquivos da pasta
try:
    filenames = [f for f in os.listdir(folder_path) if f.endswith('.txt')]
    if not filenames:
        st.warning("Nenhum arquivo .txt encontrado na pasta.")
        st.stop()
except FileNotFoundError:
    st.error(f"Pasta '{folder_path}' não encontrada.")
    st.stop()
except Exception as e:
    st.error(f"Erro ao ler arquivos: {str(e)}")
    st.stop()

# Inicializa o banco de dados
init_db()

# Busca arquivos já processados
df_existentes = buscar_arquivos_db()
arquivos_processados = df_existentes['nome_arquivo'].tolist() if not df_existentes.empty else []

# Filtra apenas arquivos não processados
arquivos_para_processar = [f for f in filenames if f not in arquivos_processados]

# Se todos os arquivos já estiverem processados, mostra apenas o DataFrame
if not arquivos_para_processar:
    st.success("Todos os arquivos já foram processados!")
    st.write("### Arquivos Processados")
    
    # Renomeia as colunas para exibição
    df_exibicao = df_existentes.rename(columns={
        'nome_arquivo': 'Nome do Arquivo',
        'tipo': 'Tipo de Informação',
        'dia': 'Dia',
        'mes': 'Mês',
        'ano': 'Ano',
        'registros': 'Número de Registros'
    })
    
    st.dataframe(df_exibicao)
    
    # Opção para download
    csv = df_exibicao.to_csv(index=False).encode('utf-8')
    st.download_button(
        "Download CSV",
        csv,
        "dados_processados.csv",
        "text/csv",
        key='download-csv'
    )
    st.stop()

# Se houver arquivos para processar, mostra o formulário apenas para eles
st.write(f"### {len(arquivos_para_processar)} arquivo(s) para processar")

# Criar um formulário para entrada de dados
with st.form("dados_arquivos"):
    data = []
    
    for filename in arquivos_para_processar:
        st.write(f"#### Arquivo: {filename}")
        
        # Extrai o tipo do arquivo
        tipo = filename.split("_")[0] if "_" in filename else "Desconhecido"
        tipo_formatado = transform_tipo(tipo)
        
        # Adicionar select box para confirmar tipo
        tipos_disponiveis = [
            "CELULA EMERGENCIAL",
            "INCLINOMETRO",
            "LEVANTAMENTO TOPOGRÁFICO",
            "PAMPULHA",
            "CELULA DE PESQUISA"
        ]
        tipo_confirmado = st.selectbox(
            "Confirmar tipo de arquivo",
            tipos_disponiveis,
            index=tipos_disponiveis.index(tipo_formatado) if tipo_formatado in tipos_disponiveis else 0,
            key=f"tipo_{filename}"
        )
        
        # Cria colunas para input de data
        col1, col2, col3 = st.columns(3)
        
        with col1:
            dia = st.text_input(
                "Dia",
                key=f"dia_{filename}",
                placeholder="DD",
                help="Digite o dia (01-31)"
            )
        
        with col2:
            mes = st.text_input(
                "Mês",
                key=f"mes_{filename}",
                placeholder="MM",
                help="Digite o mês (01-12)"
            )
        
        with col3:
            ano = st.text_input(
                "Ano",
                key=f"ano_{filename}",
                placeholder="AAAA",
                help="Digite o ano (ex: 2024)"
            )
        
        # Lê o número de registros do arquivo
        filepath = os.path.join(folder_path, filename)
        try:
            with open(filepath, 'r', encoding="latin-1") as f:
                num_registros = len(f.readlines())
        except Exception as e:
            st.error(f"Erro ao ler o arquivo {filename}: {str(e)}")
            num_registros = 0
        
        # Armazena os dados temporariamente
        data.append({
            "filename": filename,
            "tipo": tipo_confirmado,
            "dia": dia,
            "mes": mes,
            "ano": ano,
            "registros": num_registros
        })
        
        st.divider()
    
    # Botão para processar todos os arquivos
    submitted = st.form_submit_button("Processar Arquivos")

# Processa os dados quando o formulário for submetido
if submitted:
    # Inicializa o banco de dados
    init_db()
    
    processed_data = []
    saving_status = []
    
    for item in data:
        try:
            # Valida a data
            if item["dia"] and item["mes"] and item["ano"]:
                date_str = f"{item['dia']}/{item['mes']}/{item['ano']}"
                datetime.strptime(date_str, '%d/%m/%Y')  # Valida a data
                
                dados_arquivo = [
                    item["filename"],
                    item["tipo"],
                    int(item["dia"]),
                    int(item["mes"]),
                    int(item["ano"]),
                    item["registros"]
                ]
                
                # Verifica se o arquivo já existe no banco
                if not verificar_arquivo_existente(item["filename"]):
                    if salvar_arquivo_db(dados_arquivo):
                        saving_status.append(f"✅ Arquivo {item['filename']} salvo com sucesso!")
                    else:
                        saving_status.append(f"❌ Erro ao salvar {item['filename']}")
                else:
                    saving_status.append(f"⚠️ Arquivo {item['filename']} já existe no banco")
                
                processed_data.append(dados_arquivo)
            else:
                st.warning(f"Data incompleta para o arquivo {item['filename']}")
        except ValueError:
            st.error(f"Data inválida para o arquivo {item['filename']}")
    
    if processed_data:
        # Cria e exibe o DataFrame
        df = pd.DataFrame(
            processed_data,
            columns=["Nome do Arquivo", "Tipo de Informação", "Dia", "Mês", "Ano", "Número de Registros"]
        )
        st.write("### Resultado do Processamento")
        st.dataframe(df)
        
        # Opção para download
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            "Download CSV",
            csv,
            "dados_processados.csv",
            "text/csv",
            key='download-csv'
        )
        
        # Exibe status do salvamento
        st.write("### Status do Salvamento no Banco de Dados")
        for status in saving_status:
            st.write(status)


