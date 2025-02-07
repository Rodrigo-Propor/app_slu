import os
import random
import streamlit as st

def extrair_comentario_inicial(caminho_arquivo):
    with open(caminho_arquivo, 'r', encoding='utf-8') as f:
        linhas = f.readlines()

    comentarios = []
    for linha in linhas:
        linha_strip = linha.strip()
        if linha_strip.startswith('#'):
            comentarios.append(linha_strip.lstrip('#').strip())
        else:
            break  # Para quando encontrar uma linha que não seja comentário

    return ' '.join(comentarios)

def main():
    # Definir o tema escuro como padrão
    st.set_page_config(layout="wide", page_title="Gerenciador de Aplicativos")

    # Aplicar estilo para o tema escuro
    dark_theme_css = '''
    <style>
    body {
        background-color: #0E1117;
        color: #FAFAFA;
    }
    .stButton>button {
        background-color: #262730;
        color: #FAFAFA;
    }
    .stTextInput>div>div>input {
        background-color: #262730;
        color: #FAFAFA;
    }
    </style>
    '''
    st.markdown(dark_theme_css, unsafe_allow_html=True)

    st.title('Gerenciador de Aplicativos')

    arquivo_atual = os.path.basename(__file__)

    arquivos = [f for f in os.listdir('.') if os.path.isfile(f) and f.endswith('.py') and f != arquivo_atual]

    # Lista de URLs de ícones que funcionam com temas escuros
    icones = [
        'https://img.icons8.com/fluency/48/000000/app.png',
        'https://img.icons8.com/fluency/48/000000/application-window.png',
        'https://img.icons8.com/fluency/48/000000/application.png',
        'https://img.icons8.com/fluency/48/000000/windows-10.png',
        'https://img.icons8.com/fluency/48/000000/ios-application-placeholder.png',
        'https://img.icons8.com/fluency/48/000000/task.png',
        'https://img.icons8.com/fluency/48/000000/services.png',
        'https://img.icons8.com/fluency/48/000000/source-code.png',
        'https://img.icons8.com/fluency/48/000000/computer.png',
        'https://img.icons8.com/fluency/48/000000/developer.png'
        # Adicione mais URLs de ícones conforme necessário
    ]

    # Definir o número de colunas para a grade
    num_colunas = 3
    colunas = st.columns(num_colunas)

    for idx, arquivo in enumerate(arquivos):
        nome_app = os.path.splitext(arquivo)[0]
        descricao = extrair_comentario_inicial(arquivo)

        # Selecionar um ícone aleatoriamente
        icone_url = random.choice(icones)

        with colunas[idx % num_colunas]:
            st.image(icone_url, width=50)
            st.subheader(nome_app)
            st.write(descricao)
            if st.button(f'Abrir {nome_app}', key=nome_app):
                pass  # Código para abrir o aplicativo

if __name__ == '__main__':
    main()
