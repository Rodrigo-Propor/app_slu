import os
import re
import streamlit as st
from PyPDF2 import PdfMerger, PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from io import BytesIO
from PIL import Image
from reportlab.lib import utils

def get_pdf_files(month: int, year: int) -> list:
    """
    Retorna uma lista de arquivos PDF na pasta 'media' que correspondem ao mês e ano de referência.
    """
    pdf_files = []
    directory = os.path.join("media")  # Diretório fixo onde estão os arquivos PDF
    pattern = fr"_{month}_(Ano {year})_"

    if not os.path.isdir(directory):
        st.error(f"A pasta '{directory}' não foi encontrada.")
        return []

    for filename in os.listdir(directory):
        if filename.endswith(".pdf") and re.search(pattern, filename):
            pdf_files.append(filename)

    return sorted(pdf_files)

def merge_pdfs(pdf_files: list, output_path: str):
    """
    Junta os arquivos PDF na lista `pdf_files` em um único PDF.
    """
    merger = PdfMerger()
    input_directory = os.path.join("media")

    st.info("Iniciando a combinação dos arquivos PDF...")
    for pdf in pdf_files:
        pdf_path = os.path.join(input_directory, pdf)
        st.write(f"Adicionando '{pdf}'...")
        merger.append(pdf_path)

    merger.write(output_path)
    merger.close()
    st.success(f"Arquivos PDF combinados com sucesso em '{output_path}'.")

def get_image_dimensions(image_path: str, target_height: float):
    """
    Calcula as dimensões da imagem mantendo a proporção e transparência.
    """
    img = utils.ImageReader(image_path)
    orig_width, orig_height = img.getSize()
    aspect_ratio = orig_width / orig_height
    target_width = target_height * aspect_ratio
    return target_width, target_height

def add_image_to_pdf(pdf_path: str, image_path: str):
    """
    Adiciona uma imagem PNG transparente a cada página de um PDF existente.
    A imagem será posicionada a 3cm da borda esquerda e 1cm da borda inferior,
    com altura de 2cm e largura proporcional.
    """
    target_height = 2 * cm
    target_width, _ = get_image_dimensions(image_path, target_height)

    reader = PdfReader(pdf_path)
    writer = PdfWriter()

    st.info("Iniciando a adição da assinatura em cada página...")
    for page_num, page in enumerate(reader.pages):
        # Obtém as dimensões da página
        page_width = float(page.mediabox.width)
        page_height = float(page.mediabox.height)

        # Cria um novo canvas com as dimensões da página
        packet = BytesIO()
        can = canvas.Canvas(packet, pagesize=(page_width, page_height))

        # Define as posições (3cm da esquerda, 1cm da base)
        x_position = 3 * cm
        y_position = 1 * cm

        # Adiciona a imagem mantendo a transparência
        can.drawImage(
            image_path,
            x_position,
            y_position,
            width=target_width,
            height=target_height,
            mask='auto',  # Preserva a transparência
            preserveAspectRatio=True,
            anchor='sw'   # inferior esquerdo
        )

        can.save()
        packet.seek(0)

        # Cria uma nova página com a imagem
        overlay = PdfReader(packet)
        page.merge_page(overlay.pages[0])
        writer.add_page(page)

        st.write(f"Assinatura adicionada na página {page_num + 1}.")

    with open(pdf_path, "wb") as output_pdf:
        writer.write(output_pdf)

    st.success(f"Assinatura adicionada com sucesso ao arquivo '{pdf_path}'.")

def main():
    st.title("Diário de Obras - Processamento de PDFs")
    st.write("Informe as informações necessárias para o processamento:")

    month = st.number_input("Mês de referência (1 a 12):", min_value=1, max_value=12, value=1, step=1)
    year = st.number_input("Ano de referência:", min_value=1, value=1, step=1)

    if st.button("Buscar PDFs"):
        pdf_files = get_pdf_files(month, year)
        if not pdf_files:
            st.error("Nenhum arquivo PDF encontrado para o mês e ano informados.")
            return
        
        st.write("Arquivos PDF encontrados:")
        for file in pdf_files:
            st.write(f"- {file}")
        
        if st.button("Confirmar Processamento"):
            output_directory = os.path.join("media", "relatorio")
            os.makedirs(output_directory, exist_ok=True)
            
            final_filename = f"Documentos_{month}_Ano_{year}_assinatura.pdf"
            final_pdf_path = os.path.join(output_directory, final_filename)
            
            if os.path.exists(final_pdf_path):
                st.warning(f"O arquivo '{final_pdf_path}' já existe. Nenhuma ação foi realizada.")
                return
            
            image_path = os.path.join("media", "template", "assinatura.png")
            if not os.path.exists(image_path):
                st.error(f"A imagem '{image_path}' não foi encontrada.")
                return
            
            merge_pdfs(pdf_files, final_pdf_path)
            add_image_to_pdf(final_pdf_path, image_path)
            st.success(f"Processo concluído! O arquivo final com a assinatura está em '{final_pdf_path}'.")

if __name__ == "__main__":
    main()