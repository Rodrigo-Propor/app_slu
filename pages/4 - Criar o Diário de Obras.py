import os
import re
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
        print(f"A pasta '{directory}' não foi encontrada.")
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

    print("Iniciando a combinação dos arquivos PDF...")
    for pdf in pdf_files:
        pdf_path = os.path.join(input_directory, pdf)
        print(f"Adicionando '{pdf}'...")
        merger.append(pdf_path)

    merger.write(output_path)
    merger.close()
    print(f"Arquivos PDF combinados com sucesso em '{output_path}'.")

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

    print("Iniciando a adição da assinatura em cada página...")
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
            mask='auto',  # Isso preserva a transparência
            preserveAspectRatio=True,
            anchor='sw'  # southwest = inferior esquerdo
        )

        can.save()
        packet.seek(0)

        # Cria uma nova página com a imagem
        overlay = PdfReader(packet)
        page.merge_page(overlay.pages[0])
        writer.add_page(page)

        print(f"Assinatura adicionada na página {page_num + 1}.")

    # Salva o PDF final
    with open(pdf_path, "wb") as output_pdf:
        writer.write(output_pdf)

    print(f"Assinatura adicionada com sucesso ao arquivo '{pdf_path}'.")

def main():
    month = int(input("Digite o mês de referência (número de 1 a 12): "))
    year = int(input("Digite o ano de referência (número inteiro, por exemplo, 1 para 'Ano 1'): "))

    output_directory = os.path.join("media", "relatorio")
    os.makedirs(output_directory, exist_ok=True)

    final_filename = f"Documentos_{month}_Ano_{year}_assinatura.pdf"
    final_pdf_path = os.path.join(output_directory, final_filename)

    if os.path.exists(final_pdf_path):
        print(f"O arquivo '{final_pdf_path}' já existe. Nenhuma ação foi realizada.")
        return

    pdf_files = get_pdf_files(month, year)

    if not pdf_files:
        print("Nenhum arquivo PDF encontrado para o mês e ano informados.")
        return

    # Caminho da imagem
    image_path = os.path.join("media", "template", "assinatura.png")

    # Verifica se a imagem existe
    if not os.path.exists(image_path):
        print(f"A imagem '{image_path}' não foi encontrada.")
        return

    # Junta os PDFs
    merge_pdfs(pdf_files, final_pdf_path)

    # Adiciona a imagem em cada página do PDF combinado
    add_image_to_pdf(final_pdf_path, image_path)

    print(f"Processo concluído! O arquivo final com a assinatura está em '{final_pdf_path}'.")

if __name__ == "__main__":
    main()