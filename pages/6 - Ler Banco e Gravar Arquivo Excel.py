import os
import sqlite3
import pandas as pd
from datetime import datetime
import re
import zipfile
import tkinter as tk
from tkinter import messagebox
import time
import streamlit as st  # Importando Streamlit

# Diretórios e configuração de arquivos
media_path = 'media/planilhas_SLU'
db_path = 'banco_dados.db'
required_files = [
    "Placa de Recalque AC 01.xlsx", "Placa de Recalque AC 03.xlsx",
    "Placa de Recalque AC 04.xlsx", "Placa de Recalque AC 05.xlsx",
    "Placa de Recalque AMPLIAÇÃO.xlsx", "Placa de Recalque Emergencial.xlsx",
    "Recalques Celula Pesquisa.xlsx"
]

contador_processados = 0
contador_duplicados = 0
contador_erros = 0

def verificar_arquivos_abertos():
    """Tenta abrir cada arquivo para verificar se está acessível"""
    arquivos_bloqueados = []
    for arquivo in required_files:
        file_path = os.path.join(media_path, arquivo)
        try:
            # Tenta abrir o arquivo em modo de escrita
            with open(file_path, 'a+b') as f:
                pass
        except PermissionError:
            arquivos_bloqueados.append(arquivo)
    return arquivos_bloqueados

def solicitar_fechamento_arquivos(arquivos_bloqueados):
    """Exibe uma janela de diálogo solicitando que o usuário feche os arquivos"""
    root = tk.Tk()
    root.withdraw()  # Esconde a janela principal
    
    mensagem = "Os seguintes arquivos estão abertos:\n\n"
    mensagem += "\n".join(arquivos_bloqueados)
    mensagem += "\n\nPor favor, feche esses arquivos e clique em OK para continuar."
    
    while True:
        resposta = messagebox.showwarning("Arquivos Abertos", mensagem, icon='warning')
        
        # Verifica novamente se os arquivos ainda estão abertos
        arquivos_ainda_bloqueados = verificar_arquivos_abertos()
        if not arquivos_ainda_bloqueados:
            break
        
        mensagem = "Os seguintes arquivos ainda estão abertos:\n\n"
        mensagem += "\n".join(arquivos_ainda_bloqueados)
        mensagem += "\n\nPor favor, feche esses arquivos e clique em OK para continuar."
    
    root.destroy()

def extrair_data(nome_arquivo):
    match = re.search(r'(\d{6})M\.TXT$', nome_arquivo)
    if match:
        data_str = match.group(1)
        dia, mes, ano = data_str[:2], data_str[2:4], '20' + data_str[4:]
        return datetime.strptime(f"{dia}-{mes}-{ano}", "%d-%m-%Y")
    return None

def formatar_numero_br(valor):
    return f"{valor:,.3f}".replace(",", "X").replace(".", ",").replace("X", ".")

def verificar_duplicata(aba, data, elevacao, coord_este, coord_norte):
    for row in aba.iter_rows(min_row=3):  # Começando da linha 3
        if not row[0].value:  # Se chegou em uma linha vazia
            break
            
        # Converter valores da planilha para o mesmo formato dos novos dados
        row_data = row[0].value
        row_elevacao = row[1].value
        row_coord_este = row[2].value
        row_coord_norte = row[3].value
        
        # Verificar se todos os valores correspondem
        if (row_data == data and 
            row_elevacao == elevacao and 
            row_coord_este == coord_este and 
            row_coord_norte == coord_norte):
            return True
    
    return False

def processar_arquivo_excel(file_path, dados, aba_desejada):
    max_tentativas = 3
    tentativa = 0
    
    while tentativa < max_tentativas:
        try:
            with pd.ExcelWriter(file_path, engine="openpyxl", mode="a", 
                              if_sheet_exists="overlay") as writer:
                # Obter a aba ou criar uma nova
                if aba_desejada in writer.book.sheetnames:
                    aba = writer.book[aba_desejada]
                else:
                    aba = writer.book.create_sheet(aba_desejada)
                
                # Verificar duplicatas
                if verificar_duplicata(aba, dados["Data"], dados["Elevação"], 
                                    dados["Coordenada Este"], dados["Coordenada Norte"]):
                    return "duplicado"
                
                # Encontrar próxima linha vazia
                linha_inicio = 3
                while aba.cell(row=linha_inicio, column=1).value is not None:
                    linha_inicio += 1
                
                # Escrever dados
                aba[f"A{linha_inicio}"] = dados["Data"]
                aba[f"B{linha_inicio}"] = dados["Elevação"]
                aba[f"C{linha_inicio}"] = dados["Coordenada Este"]
                aba[f"D{linha_inicio}"] = dados["Coordenada Norte"]
                
                return "sucesso"
                
        except PermissionError:
            tentativa += 1
            if tentativa < max_tentativas:
                # Solicita ao usuário que feche o arquivo
                root = tk.Tk()
                root.withdraw()
                mensagem = f"O arquivo '{os.path.basename(file_path)}' está aberto.\n"
                mensagem += "Por favor, feche-o e clique em OK para continuar."
                messagebox.showwarning("Arquivo Aberto", mensagem)
                root.destroy()
                time.sleep(1)  # Pequena pausa antes de tentar novamente
            else:
                raise Exception(f"Não foi possível acessar o arquivo após {max_tentativas} tentativas")
        
        except zipfile.BadZipFile:
            raise Exception(f"O arquivo {os.path.basename(file_path)} está corrompido")

def processar_registros():
    global contador_processados, contador_duplicados, contador_erros

    # Resetar contadores
    contador_processados = 0
    contador_duplicados = 0
    contador_erros = 0

    # Conectar ao banco de dados
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Carregar registros da tabela `placas_completas_slu_bh`
    cursor.execute("SELECT * FROM placas_completas_slu_bh")
    registros = cursor.fetchall()

    # Processar cada registro
    for registro in registros:
        # Desempacotar os campos conforme a estrutura atual:
        # id, tipo, descricao, coordenada_este, coordenada_norte, elevacao, info_gerada,
        # nome_arquivo, placa, data
        id, tipo, descricao, coordenada_este, coordenada_norte, elevacao, info_gerada, nome_arquivo, placa, data = registro

        # Processar apenas os tipos válidos
        if tipo not in ("CELULA EMERGENCIAL", "CELULA PESQUISA", "PAMPULHA"):
            continue

        try:
            # Converter a data de leitura
            data_registro = datetime.strptime(data, "%Y-%m-%d")

            # Determinar o arquivo de destino de acordo com o campo TIPO
            if tipo == "CELULA EMERGENCIAL":
                arquivo_destino = "Placa de Recalque Emergencial.xlsx"
            elif tipo == "CELULA PESQUISA":
                arquivo_destino = "Recalques Celula Pesquisa.xlsx"
            elif tipo == "PAMPULHA":
                if placa and (placa.startswith("PR 1") or placa in ("D1", "D2")):
                    arquivo_destino = "Placa de Recalque AC 01.xlsx"
                elif placa and placa.startswith("PR 3"):
                    arquivo_destino = "Placa de Recalque AC 03.xlsx"
                elif placa and placa.startswith("PR 4"):
                    arquivo_destino = "Placa de Recalque AC 04.xlsx"
                elif placa and placa.startswith("PR 5"):
                    arquivo_destino = "Placa de Recalque AC 05.xlsx"
                elif placa and placa.startswith("PR A"):
                    arquivo_destino = "Placa de Recalque AMPLIAÇÃO.xlsx"
                else:
                    print(f"Aviso: Registro do tipo PAMPULHA com aba '{placa}' não corresponde a nenhum critério de destino.")
                    continue

            # Preparar dados para gravação
            dados = {
                "Data": data_registro.strftime("%d-%b-%y"),
                "Elevação": formatar_numero_br(elevacao),
                "Coordenada Este": formatar_numero_br(coordenada_este),
                "Coordenada Norte": formatar_numero_br(coordenada_norte)
            }

            # A aba onde será gravado é definida pelo campo placa (removendo espaços em excesso)
            aba_desejada = placa.strip() if placa else ""

            # Processar o arquivo Excel com verificação de duplicidade na aba
            file_path = os.path.join(media_path, arquivo_destino)
            resultado = processar_arquivo_excel(file_path, dados, aba_desejada)

            if resultado == "duplicado":
                print(f"Aviso: Registro duplicado encontrado - Arquivo: {arquivo_destino}, "
                      f"Aba: {aba_desejada}, Data: {dados['Data']}")
                contador_duplicados += 1
            elif resultado == "sucesso":
                print(f"Registro inserido - Arquivo: {arquivo_destino}, Aba: {aba_desejada}")
                contador_processados += 1

        except Exception as e:
            print(f"Erro ao processar registro: {str(e)}")
            contador_erros += 1
            continue

    conn.commit()
    conn.close()

    # Relatório final
    print(f"""
    Processamento concluído:
    - Total de registros processados com sucesso: {contador_processados}
    - Total de registros duplicados ignorados: {contador_duplicados}
    - Total de erros encontrados: {contador_erros}
    """)

    # Se houver erros, notificar o usuário
    if contador_erros > 0:
        root = tk.Tk()
        root.withdraw()
        messagebox.showwarning("Conclusão do Processamento",
                               f"Processamento concluído com {contador_erros} erro(s).\n"
                               "Verifique o console para mais detalhes.")
        root.destroy()

def interface_streamlit():
    st.title("Processamento de Planilhas SLU")
    
    # Criando tabs para melhor organização
    tab1, tab2 = st.tabs(["Informações", "Processamento"])
    
    with tab1:
        st.markdown("""
        ### Sobre o Processamento
        Este programa realiza as seguintes operações:
        1. Lê dados do banco de dados SQLite
        2. Processa os registros conforme regras específicas
        3. Atualiza as planilhas Excel correspondentes
        4. Verifica duplicatas e mantém consistência dos dados
        """)
        
        st.subheader("Arquivos Necessários")
        for arquivo in required_files:
            st.write(f"- {arquivo}")
    
    with tab2:
        # Verificar a existência dos arquivos necessários
        missing_files = [f for f in required_files if not os.path.exists(os.path.join(media_path, f))]
        if missing_files:
            st.error(f"Erro: Os seguintes arquivos estão ausentes na pasta '{media_path}': {', '.join(missing_files)}")
            return

        # Verificar se há arquivos abertos
        arquivos_bloqueados = verificar_arquivos_abertos()
        if arquivos_bloqueados:
            st.warning("Detectados arquivos abertos. Por favor, feche os arquivos listados abaixo:")
            for arquivo in arquivos_bloqueados:
                st.write(f"- {arquivo}")
            return

        # Container para status e progresso
        status_container = st.empty()
        progress_container = st.empty()
        
        col1, col2 = st.columns(2)
        
        with col1:
            iniciar = st.button("Iniciar Processamento", type="primary")
        
        with col2:
            confirmar = st.checkbox("Confirmar início do processamento")
        
        if iniciar:
            if not confirmar:
                st.warning("Por favor, confirme para iniciar o processamento")
                return
                
            status_container.info("Iniciando processamento...")
            progress_bar = progress_container.progress(0)
            
            try:
                processar_registros()
                
                # Atualizar status final
                status_container.success("Processamento concluído!")
                
                # Exibir relatório em uma área expandível
                with st.expander("Ver Relatório Detalhado", expanded=True):
                    st.markdown("### Relatório de Processamento")
                    st.write(f"✅ Registros processados com sucesso: {contador_processados}")
                    st.write(f"⚠️ Registros duplicados ignorados: {contador_duplicados}")
                    st.write(f"❌ Erros encontrados: {contador_erros}")
                    
                    if contador_erros > 0:
                        st.error("Foram encontrados erros durante o processamento. Verifique o log para mais detalhes.")
                
            except Exception as e:
                status_container.error(f"Erro durante o processamento: {str(e)}")
                st.error("O processamento foi interrompido devido a um erro.")

if __name__ == "__main__":
    interface_streamlit()