import streamlit as st

# Configuração da página
st.set_page_config(page_title="SLU - Belo Horizonte", layout="wide")

# Título da página
st.title("Modulo SLU - Belo Horizonte")

# Barra de navegação de ícones na parte superior
st.write("### Selecione uma Seção:")

# Criando colunas para distribuir os ícones horizontalmente
col1, col2, col3 = st.columns(3)

# Variável para armazenar a seção selecionada
selecao = None

# Botões de navegação com ícones em cada coluna
with col1:
    if st.button("🏠 Início"):  # Ícone de "Início"
        selecao = "Início"

with col2:
    if st.button("📄 Documentos"):  # Ícone de "Documentos"
        selecao = "Documentos"

with col3:
    if st.button("📊 Análise"):  # Ícone de "Análise"
        selecao = "Análise"

# Exibe a seção correspondente com base no ícone selecionado
if selecao == "Início":
    st.header("🏠 Seção de Início")
    st.write("Bem-vindo à seção de início. Aqui você encontra informações gerais sobre o aplicativo e como navegar.")

elif selecao == "Documentos":
    st.header("📄 Seção de Documentos")
    st.write("Esta é a seção de documentos, onde você pode acessar relatórios, arquivos importantes e outros documentos.")

elif selecao == "Análise":
    st.header("📊 Seção de Análise")
    st.write("Bem-vindo à seção de análise. Aqui estão disponíveis gráficos e insights sobre os dados mais recentes.")

else:
    st.write("Selecione uma seção acima para visualizar o conteúdo correspondente.")
