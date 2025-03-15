import os
import dash
from dash import dcc, html, Input, Output, State
from dash.exceptions import PreventUpdate
from PyPDF2 import PdfMerger, PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from io import BytesIO
from reportlab.lib import utils

# Initialize the Dash app
app = dash.Dash(__name__)

# App layout
app.layout = html.Div([
    html.H1("Diário de Obras - Processamento de PDFs"),

    html.Div([
        html.Label("Mês:"),
        dcc.Input(id='mes', type='number', min=1, max=12, value=1, step=1),

        html.Label("Ano:"),
        dcc.Input(id='ano', type='number', value=2024, step=1),

        html.Button("Buscar PDFs", id='buscar-pdfs', n_clicks=0),
    ], style={'display': 'flex', 'gap': '10px'}),

    html.Div(id='pdf-info'),
    dcc.Loading(
        id="loading-pdfs",
        type="default",
        children=[
             dcc.Checklist(id='pdf-list', options=[], value=[]) # Checklist for selection
        ]
    ),
   

    html.Button("Processar PDFs", id='processar-pdfs', n_clicks=0, disabled=True), # Disable initially
    html.Div(id='processing-output'),
    dcc.Loading(id='loading-processing', type='circle')

])


def encontrar_pdfs(mes: int, ano: int) -> list:
    """Busca arquivos PDF na pasta correspondente."""
    pdf_files = []

    base_dir = os.path.join("media", "diario")

    if not os.path.isdir(base_dir):
        return []  # Return empty list if base directory not found

    mes_str = f"{mes:02d}"
    ano_str = f"{ano % 100:02d}"
    pasta_alvo = f"{mes_str}_{ano_str}"

    caminho_pasta = os.path.join(base_dir, pasta_alvo)

    if not os.path.isdir(caminho_pasta):
        return []  # Return empty list if month/year directory not found


    for arquivo in os.listdir(caminho_pasta):
        if arquivo.endswith(".pdf"):
            pdf_files.append(os.path.join(caminho_pasta, arquivo))

    return sorted(pdf_files)


def mesclar_pdfs(lista_pdf: list, destino: str):
    """Mescla vários PDFs em um único arquivo."""
    merger = PdfMerger()

    try:
        for pdf in lista_pdf:
            merger.append(pdf)

        os.makedirs(os.path.dirname(destino), exist_ok=True)
        merger.write(destino)
        merger.close()
        return True
    except Exception as e:
        print(f"Error merging PDFs: {e}")  # Log error for debugging
        return False


def inserir_imagem(pdf_alvo: str, caminho_imagem: str):
    """Insere uma imagem em todas as páginas de um PDF."""
    try:
        img = utils.ImageReader(caminho_imagem)
        largura_orig, altura_orig = img.getSize()
        altura_img = 2 * cm
        proporcao = largura_orig / altura_orig
        largura_img = altura_img * proporcao
    except Exception as e:
        print(f"Error processing image: {e}")
        return False

    try:
        reader = PdfReader(pdf_alvo)
        writer = PdfWriter()

        for num_pag, pagina in enumerate(reader.pages):
            largura_pag = float(pagina.mediabox.width)
            altura_pag = float(pagina.mediabox.height)

            packet = BytesIO()
            can = canvas.Canvas(packet, pagesize=(largura_pag, altura_pag))
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

            packet.seek(0)
            overlay = PdfReader(packet)
            pagina.merge_page(overlay.pages[0])
            writer.add_page(pagina)

        with open(pdf_alvo, "wb") as output_pdf:
            writer.write(output_pdf)

        return True
    except Exception as e:
        print(f"Error inserting image into PDF: {e}")
        return False


@app.callback(
    [Output('pdf-list', 'options'),
     Output('pdf-info', 'children'),
     Output('processar-pdfs', 'disabled')],
    [Input('buscar-pdfs', 'n_clicks')],
    [State('mes', 'value'),
     State('ano', 'value')]
)
def update_pdf_list(n_clicks, mes, ano):
    """Updates the checklist with found PDFs."""
    if n_clicks is None or n_clicks == 0:
         raise PreventUpdate

    pdfs_encontrados = encontrar_pdfs(mes, ano)

    if pdfs_encontrados:
        options = [{'label': os.path.basename(pdf), 'value': pdf} for pdf in pdfs_encontrados]
        info_message = html.Div([html.P(f"Encontrados {len(pdfs_encontrados)} arquivos PDF"),
                                 html.Details([  # Use html.Details for expander
                                      html.Summary("Ver arquivos"),
                                      html.Ul([html.Li(os.path.basename(pdf)) for pdf in pdfs_encontrados])
                                 ])
                                ])
        return options, info_message, False # Enable the process button
    else:
        return [], html.P("Nenhum PDF encontrado."), True  # Disable process button


@app.callback(
    Output('processing-output', 'children'),
    [Input('processar-pdfs', 'n_clicks')],
    [State('pdf-list', 'value'),  # Get selected PDFs
     State('mes', 'value'),
     State('ano', 'value')]
)
def process_pdfs(n_clicks, selected_pdfs, mes, ano):
    """Processes selected PDFs: merges and adds signature."""

    if n_clicks is None or n_clicks ==0:
        raise PreventUpdate

    if not selected_pdfs:
        return html.P("Nenhum PDF selecionado para processamento.")

    nome_arquivo = f"Documentos_{mes:02d}_Ano_{ano % 100:02d}_assinatura.pdf"
    arquivo_final = os.path.join("media", "diario", nome_arquivo)

    if os.path.exists(arquivo_final):
        return html.P(f"O arquivo '{nome_arquivo}' já existe. Processamento cancelado.")

    imagem_assinatura = os.path.join("media", "template", "assinatura.png")
    if not os.path.exists(imagem_assinatura):
        return html.P(f"Imagem de assinatura não encontrada em '{imagem_assinatura}'")


    if mesclar_pdfs(selected_pdfs, arquivo_final):
        if inserir_imagem(arquivo_final, imagem_assinatura):
            return html.P(f"Processamento concluído! Arquivo final: {nome_arquivo}")
        else:
            return html.P("Erro ao adicionar assinatura.")
    else:
        return html.P("Erro ao mesclar PDFs.")



if __name__ == '__main__':
    app.run_server(debug=True)