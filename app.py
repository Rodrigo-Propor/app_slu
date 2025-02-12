import streamlit as st
import os
import pandas as pd
from datetime import datetime

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

# Criar um formulário para entrada de dados
with st.form("dados_arquivos"):
    data = []
    
    for filename in filenames:
        st.write(f"#### Arquivo: {filename}")
        
        # Extrai o tipo do arquivo
        tipo = filename.split("_")[0] if "_" in filename else "Desconhecido"
        tipo_formatado = transform_tipo(tipo)
        
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
            "tipo": tipo_formatado,
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
    processed_data = []
    
    for item in data:
        try:
            # Valida a data
            if item["dia"] and item["mes"] and item["ano"]:
                date_str = f"{item['dia']}/{item['mes']}/{item['ano']}"
                datetime.strptime(date_str, '%d/%m/%Y')  # Valida a data
                
                processed_data.append([
                    item["filename"],
                    item["tipo"],
                    int(item["dia"]),
                    int(item["mes"]),
                    int(item["ano"]),
                    item["registros"]
                ])
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


