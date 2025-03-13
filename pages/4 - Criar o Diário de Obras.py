import os
import streamlit as st
from PyPDF2 import PdfMerger, PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from io import BytesIO
from reportlab.lib import utils

def encontrar_pdfs(mes: int, ano: int) -> list:
    """Busca arquivos PDF na pasta correspondente."""
    st.write("Debug: Buscando PDFs...")
    pdf_files = []
    
    # Diretório base para os PDFs
    base_dir = os.path.join("media", "diario")
    
    if not os.path.isdir(base_dir):
        st.error(f"Pasta '{base_dir}' não encontrada.")
        return []
    
    # Forma o nome da pasta: MM_AA
    mes_str = f"{mes:02d}"
    ano_str = f"{ano % 100:02d}"
    pasta_alvo = f"{mes_str}_{ano_str}"
    
    caminho_pasta = os.path.join(base_dir, pasta_alvo)
    st.write(f"Debug: Procurando em: {caminho_pasta}")
    
    if not os.path.isdir(caminho_pasta):
        st.error(f"Pasta '{caminho_pasta}' não encontrada.")
        return []
    
    # Coleta todos os PDFs na pasta
    for arquivo in os.listdir(caminho_pasta):
        if arquivo.endswith(".pdf"):
            pdf_files.append(os.path.join(caminho_pasta, arquivo))
    
    st.write(f"Debug: Encontrados {len(pdf_files)} arquivos PDF")
    return sorted(pdf_files)

def mesclar_pdfs(lista_pdf: list, destino: str):
    """Mescla vários PDFs em um único arquivo."""
    st.write("Debug: Iniciando mesclagem...")
    
    merger = PdfMerger()
    
    try:
        for pdf in lista_pdf:
            st.write(f"Debug: Adicionando {os.path.basename(pdf)}")
            merger.append(pdf)
        
        # Garante que o diretório de destino existe
        os.makedirs(os.path.dirname(destino), exist_ok=True)
        
        merger.write(destino)
        merger.close()
        st.success(f"PDFs mesclados com sucesso em '{destino}'")
        return True
    except Exception as e:
        st.error(f"Erro ao mesclar PDFs: {e}")
        return False

def inserir_imagem(pdf_alvo: str, caminho_imagem: str):
    """Insere uma imagem em todas as páginas de um PDF."""
    st.write("Debug: Inserindo assinatura...")
    
    # Calcula dimensões da imagem
    altura_img = 2 * cm
    try:
        img = utils.ImageReader(caminho_imagem)
        largura_orig, altura_orig = img.getSize()
        proporcao = largura_orig / altura_orig
        largura_img = altura_img * proporcao
    except Exception as e:
        st.error(f"Erro ao processar a imagem: {e}")
        return False
    
    try:
        # Abre o PDF para leitura
        reader = PdfReader(pdf_alvo)
        writer = PdfWriter()
        
        # Processa cada página
        for num_pag, pagina in enumerate(reader.pages):
            st.write(f"Debug: Processando página {num_pag+1} de {len(reader.pages)}")
            
            largura_pag = float(pagina.mediabox.width)
            altura_pag = float(pagina.mediabox.height)
            
            # Cria um PDF temporário com a imagem
            packet = BytesIO()
            can = canvas.Canvas(packet, pagesize=(largura_pag, altura_pag))
            
            # Posiciona no canto inferior esquerdo
            x_pos = 3 * cm
            y_pos = 1 * cm
            
            can.drawImage(
                caminho_imagem,
                x_pos, y_pos,
                width=largura_img,
                height=altura_img,
                mask='auto'
            )
            can.save()
            
            # Combina com a página original
            packet.seek(0)
            overlay = PdfReader(packet)
            pagina.merge_page(overlay.pages[0])
            writer.add_page(pagina)
        
        # Salva o PDF final
        with open(pdf_alvo, "wb") as output_pdf:
            writer.write(output_pdf)
        
        st.success(f"Assinatura adicionada com sucesso em '{pdf_alvo}'")
        return True
    except Exception as e:
        st.error(f"Erro ao inserir imagem no PDF: {e}")
        return False


def main():
    st.title("Diário de Obras - Processamento de PDFs")
    
    mes = st.number_input("Mês:", min_value=1, max_value=12, value=1, step=1)
    ano = st.number_input("Ano:", min_value=1, value=2024, step=1)
    
    # Usando session_state para manter os PDFs encontrados entre interações
    if 'pdfs_encontrados' not in st.session_state:
        st.session_state.pdfs_encontrados = []
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Buscar PDFs"):
            st.session_state.pdfs_encontrados = encontrar_pdfs(mes, ano)
    
    # Exibe informações se houver PDFs encontrados
    if st.session_state.pdfs_encontrados:
        st.success(f"Encontrados {len(st.session_state.pdfs_encontrados)} arquivos PDF")
        with st.expander("Ver arquivos"):
            for pdf in st.session_state.pdfs_encontrados:
                st.write(f"- {os.path.basename(pdf)}")
        
        with col2:
            if st.button("Processar PDFs"):
                st.write("Debug: Iniciando processamento...")
                
                # Define nome do arquivo final
                nome_arquivo = f"Documentos_{mes:02d}_Ano_{ano % 100:02d}_assinatura.pdf"
                arquivo_final = os.path.join("media", "diario", nome_arquivo)
                
                # Verifica se arquivo já existe
                if os.path.exists(arquivo_final):
                    st.warning(f"O arquivo '{nome_arquivo}' já existe. Processamento cancelado.")
                    return
                
                # Verifica imagem de assinatura
                imagem_assinatura = os.path.join("media", "template", "assinatura.png")
                if not os.path.exists(imagem_assinatura):
                    st.error(f"Imagem de assinatura não encontrada em '{imagem_assinatura}'")
                    return
                
                # Processamento: mescla PDFs e adiciona assinatura
                with st.spinner("Mesclando PDFs..."):
                    if mesclar_pdfs(st.session_state.pdfs_encontrados, arquivo_final):
                        st.write("Debug: Mesclagem concluída")
                
                with st.spinner("Adicionando assinatura..."):
                    if inserir_imagem(arquivo_final, imagem_assinatura):
                        st.write("Debug: Assinatura adicionada")
                        
                st.success(f"Processamento concluído! Arquivo final: {nome_arquivo}")

if __name__ == "__main__":
    main()