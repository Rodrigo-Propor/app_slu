import streamlit as st
import os
import sqlite3
from datetime import datetime
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder
from st_aggrid import GridUpdateMode, DataReturnMode
import locale
import re
from openpyxl import load_workbook
from PyPDF2 import PdfMerger, PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from io import BytesIO
from reportlab.lib import utils
import logging

# Configuração da página
st.set_page_config(
    page_title="Sistema de Controle SLU",
    page_icon="📊",
    layout="wide"
)

# Configuração do logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Funções comuns
def create_directories():
    """Cria os diretórios necessários se não existirem"""
    directories = ['media', 'media/planilhas_SLU', 'media/template']
    for directory in directories:
        os.makedirs(directory, exist_ok=True)

# Interface principal
def main():
    # Cabeçalho
    st.title("Sistema de Controle SLU")
    st.markdown("---")

    # Menu lateral para configurações globais
    with st.sidebar:
        st.header("Configurações")
        st.markdown("---")
        # Aqui você pode adicionar configurações globais

    # Criação das tabs principais
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📝 Gerenciar Dados",
        "📊 Planilhas SLU",
        "📈 Processamento Inclinômetro",
        "📑 Juntar PDFs",
        "⚙️ Configurações"
    ])

    with tab1:
        st.header("Gerenciamento de Dados")
        
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Importar Dados")
            uploaded_files = st.file_uploader(
                "Selecione os arquivos para upload",
                accept_multiple_files=True,
                type=['txt', 'csv', 'xlsx']
            )

        with col2:
            st.subheader("Sincronizar Dados")
            if st.button("Iniciar Sincronização"):
                from z8_atualiza_banco_de_placas import sync_tables
                sync_tables()

    with tab2:
        st.header("Processamento de Planilhas SLU")
        
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Gravar Planilhas")
            if st.button("Processar Planilhas"):
                try:
                    from z4_grava_planilha_SLU import processar_arquivo_excel
                    # Adicione aqui a lógica específica
                    st.success("Processamento concluído!")
                except Exception as e:
                    st.error(f"Erro no processamento: {str(e)}")

        with col2:
            st.subheader("Formatar Células")
            if st.button("Formatar Planilhas"):
                try:
                    from z5_formatar_cor_celula import process_excel_file
                    # Adicione aqui a lógica específica
                    st.success("Formatação concluída!")
                except Exception as e:
                    st.error(f"Erro na formatação: {str(e)}")

    with tab3:
        st.header("Processamento de Inclinômetro")
        
        if st.button("Iniciar Processamento do Inclinômetro"):
            try:
                from z6_processamento_inclinometro import processar_dados
                with st.spinner("Processando dados do inclinômetro..."):
                    processar_dados()
                st.success("Processamento do inclinômetro concluído!")
            except Exception as e:
                st.error(f"Erro no processamento: {str(e)}")

    with tab4:
        st.header("Juntar PDFs")
        
        col1, col2 = st.columns(2)
        with col1:
            mes = st.number_input("Mês de referência", min_value=1, max_value=12, value=1)
        with col2:
            ano = st.number_input("Ano do contrato", min_value=1, max_value=10, value=1)
            
        if st.button("Juntar PDFs"):
            try:
                from z7_jutar_pdf_diario_obra import get_pdf_files, merge_pdfs, add_image_to_pdf
                
                output_directory = os.path.join("media", "relatorio")
                os.makedirs(output_directory, exist_ok=True)
                
                final_filename = f"Documentos_{mes}_Ano_{ano}_assinatura.pdf"
                final_pdf_path = os.path.join(output_directory, final_filename)
                
                # Processo de junção dos PDFs
                with st.spinner("Juntando PDFs..."):
                    pdf_files = get_pdf_files(mes, ano)
                    if pdf_files:
                        merge_pdfs(pdf_files, final_pdf_path)
                        image_path = os.path.join("media", "template", "assinatura.png")
                        if os.path.exists(image_path):
                            add_image_to_pdf(final_pdf_path, image_path)
                            st.success(f"PDFs unidos com sucesso! Arquivo salvo em: {final_pdf_path}")
                        else:
                            st.warning("Imagem de assinatura não encontrada!")
                    else:
                        st.warning("Nenhum arquivo PDF encontrado para o período especificado!")
                        
            except Exception as e:
                st.error(f"Erro ao juntar PDFs: {str(e)}")

    with tab5:
        st.header("Configurações do Sistema")
        
        st.subheader("Diretórios")
        if st.button("Verificar/Criar Diretórios"):
            create_directories()
            st.success("Diretórios verificados/criados com sucesso!")
            
        st.subheader("Banco de Dados")
        if st.button("Verificar Banco de Dados"):
            try:
                conn = sqlite3.connect('banco_dados.db')
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = cursor.fetchall()
                st.write("Tabelas encontradas:")
                for table in tables:
                    st.write(f"- {table[0]}")
                conn.close()
            except Exception as e:
                st.error(f"Erro ao verificar banco de dados: {str(e)}")

if __name__ == "__main__":
    try:
        locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
    except:
        try:
            locale.setlocale(locale.LC_ALL, 'Portuguese_Brazil.1252')
        except:
            st.warning("Não foi possível configurar o locale para português do Brasil")
    
    main()