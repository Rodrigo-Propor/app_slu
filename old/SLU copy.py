import streamlit as st
import os
import sqlite3

# Função para verificar e criar a tabela no banco de dados, caso ela ainda não exista
def create_table():
    conn = sqlite3.connect("banco_dados.db")
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS photo_tags (
        photo_name TEXT,
        tag TEXT,
        UNIQUE(photo_name, tag)
    )
    """)
    conn.commit()
    conn.close()

# Função para carregar as marcações salvas no banco de dados
def load_tags():
    conn = sqlite3.connect("banco_dados.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM photo_tags")
    data = cursor.fetchall()
    conn.close()
    return data

# Função para salvar as marcações no banco de dados
def save_tags(photo_tags, selected_tag):
    conn = sqlite3.connect("banco_dados.db")
    cursor = conn.cursor()
    for photo_name in photo_tags:
        cursor.execute("INSERT OR REPLACE INTO photo_tags (photo_name, tag) VALUES (?, ?)", (photo_name, selected_tag))
    conn.commit()
    conn.close()

# Inicialização da tabela no banco de dados, se necessário
create_table()

# Título da página
st.title("Controle Topográfico do Aterro de Belo Horizonte / MG")

# Seleção do período de medição
st.header("Selecione o Período de Medição")
mes = st.selectbox("Mês", list(range(1, 13)), format_func=lambda x: f"{x:02d}")
ano_contrato = st.selectbox("Ano do Contrato", [f"Ano {i}" for i in range(1, 11)])
ano_formatado = ano_contrato.replace("Ano ", "")

# Filtro para exibir arquivos correspondentes ao período selecionado
folder_path = "media"
photo_files = [
    f for f in os.listdir(folder_path)
    if f.lower().endswith(('.jpg', '.jpeg', '.png')) and f"Foto{mes}_Ano {ano_formatado}" in f
]

# Carregar as marcações salvas no banco de dados
saved_tags = {name: tag for name, tag in load_tags()}

# Tabela de fotos com opção de seleção
if photo_files:
    st.write("### Fotos Encontradas:")
    
    # Lista para armazenar os arquivos selecionados pelo usuário
    selected_files = []
    
    # Exibe uma tabela com checkboxes para seleção
    for photo_file in photo_files:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.write(photo_file)  # Nome do arquivo
        with col2:
            selected = st.checkbox("Selecionar", key=photo_file)
            if selected:
                selected_files.append(photo_file)
    
    # Caixa de seleção para escolher o tipo de marcação
    selected_tag = st.selectbox(
        "Marcar os arquivos selecionados como:",
        ["", "Célula Emergencial", "Célula de Pesquisa", "Célula da Pampulha", "Inclinômetro", "Levantamento Topográfico"]
    )
    
    # Botão para salvar as marcações
    if st.button("Salvar Marcações"):
        if selected_files and selected_tag:
            save_tags(selected_files, selected_tag)
            st.success("Marcações salvas com sucesso!")
        else:
            st.warning("Por favor, selecione ao menos um arquivo e um tipo de marcação.")

# Exibe a tabela atualizada com as marcações do banco de dados
st.write("### Marcações Salvas no Banco de Dados")
tag_data = load_tags()

if tag_data:
    for photo_name, tag in tag_data:
        st.write(f"**{photo_name}** - {tag}")
else:
    st.write("Nenhuma marcação encontrada.")
