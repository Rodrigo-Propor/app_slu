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

# Verificar a existência dos arquivos necessários
missing_files = [f for f in required_files if not os.path.exists(os.path.join(media_path, f))]
if missing_files:
    print(f"Erro: Os seguintes arquivos estão ausentes na pasta '{media_path}': {', '.join(missing_files)}")
    exit()

# Verificar se há arquivos abertos
arquivos_bloqueados = verificar_arquivos_abertos()
if arquivos_bloqueados:
    print("Detectados arquivos abertos. Solicitando ao usuário para fechá-los...")
    solicitar_fechamento_arquivos(arquivos_bloqueados)
    print("Todos os arquivos foram fechados. Continuando o processamento...")

# Conectar ao banco de dados
print("Conectando ao banco de dados...")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
print("Conexão com o banco de dados estabelecida com sucesso.")

# Função para extrair data do nome do arquivo
def extrair_data(nome_arquivo):
    match = re.search(r'(\d{6})M\.TXT$', nome_arquivo)
    if match:
        data_str = match.group(1)
        dia, mes, ano = data_str[:2], data_str[2:4], '20' + data_str[4:]
        return datetime.strptime(f"{dia}-{mes}-{ano}", "%d-%m-%Y")
    return None

# Função para formatar valores no padrão brasileiro
def formatar_numero_br(valor):
    return f"{valor:,.3f}".replace(",", "X").replace(".", ",").replace("X", ".")

# Função para verificar se um registro já existe na aba
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

# Função para processar um único arquivo Excel
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

# Carregar registros da tabela `placas_completas_slu_bh`
cursor.execute("SELECT * FROM placas_completas_slu_bh")
registros = cursor.fetchall()

# Contadores
contador_processados = 0
contador_duplicados = 0
contador_erros = 0

# Processar cada registro
for registro in registros:
    _, mes, ano, tipo, numero_ponto, descricao, coordenada_este, coordenada_norte, elevacao, info_gerada, nome_arquivo = registro

    # Ignorar registros do tipo `inclinômetro`
    if tipo == "inclinômetro":
        continue

    try:
        # Extrair data do nome do arquivo
        data_registro = extrair_data(nome_arquivo)
        if not data_registro:
            print(f"Aviso: Data não extraída do arquivo {nome_arquivo}. Registro ignorado.")
            continue

        # Determinar o arquivo de destino
        if tipo == "emergencial":
            arquivo_destino = "Placa de Recalque Emergencial.xlsx"
        elif tipo == "pesquisa":
            arquivo_destino = "Recalques Celula Pesquisa.xlsx"
        elif tipo == "Pampulha":
            if info_gerada.startswith("PR 1") or descricao in ["D1", "D2"]:
                arquivo_destino = "Placa de Recalque AC 01.xlsx"
            elif info_gerada.startswith("PR 3"):
                arquivo_destino = "Placa de Recalque AC 03.xlsx"
            elif info_gerada.startswith("PR 4"):
                arquivo_destino = "Placa de Recalque AC 04.xlsx"
            elif info_gerada.startswith("PR 5"):
                arquivo_destino = "Placa de Recalque AC 05.xlsx"
            elif info_gerada.startswith("PR A"):
                arquivo_destino = "Placa de Recalque AMPLIAÇÃO.xlsx"
            else:
                print(f"Aviso: Registro com tipo Pampulha não corresponde a nenhum critério de destino: {info_gerada}")
                continue
        else:
            print(f"Aviso: Tipo desconhecido para registro: {tipo}. Registro ignorado.")
            continue

        # Preparar dados para gravação
        dados = {
            "Data": data_registro.strftime("%d-%b-%y"),
            "Elevação": formatar_numero_br(elevacao),
            "Coordenada Este": formatar_numero_br(coordenada_este),
            "Coordenada Norte": formatar_numero_br(coordenada_norte)
        }

        # Processar o arquivo
        file_path = os.path.join(media_path, arquivo_destino)
        resultado = processar_arquivo_excel(file_path, dados, info_gerada.strip())
        
        if resultado == "duplicado":
            print(f"Aviso: Registro duplicado encontrado - Arquivo: {arquivo_destino}, "
                  f"Aba: {info_gerada.strip()}, Data: {dados['Data']}")
            contador_duplicados += 1
        elif resultado == "sucesso":
            print(f"Registro inserido - Arquivo: {arquivo_destino}, "
                  f"Aba: {info_gerada.strip()}")
            contador_processados += 1

    except Exception as e:
        print(f"Erro ao processar registro: {str(e)}")
        contador_erros += 1
        continue

# Confirmar mudanças e fechar o banco de dados
conn.commit()
conn.close()

# Relatório final
print(f"""
Processamento concluído:
- Total de registros processados com sucesso: {contador_processados}
- Total de registros duplicados ignorados: {contador_duplicados}
- Total de erros encontrados: {contador_erros}
""")

# Se houve erros, aguarda confirmação do usuário antes de fechar
if contador_erros > 0:
    root = tk.Tk()
    root.withdraw()
    messagebox.showwarning("Conclusão do Processamento", 
                          f"Processamento concluído com {contador_erros} erro(s).\n"
                          "Verifique o console para mais detalhes.")
    root.destroy()

def interface_streamlit():
    st.title("Processamento de Planilhas SLU")
    
    # Exibir arquivos necessários
    st.subheader("Arquivos Necessários")
    for arquivo in required_files:
        st.write(arquivo)

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
            st.write(arquivo)
        return

    # Conectar ao banco de dados
    st.success("Conectando ao banco de dados...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    st.success("Conexão com o banco de dados estabelecida com sucesso.")

    # Processar registros
    contador_processados = 0
    contador_duplicados = 0
    contador_erros = 0

    # Carregar registros da tabela `placas_completas_slu_bh`
    cursor.execute("SELECT * FROM placas_completas_slu_bh")
    registros = cursor.fetchall()

    for registro in registros:
        # Processar cada registro e exibir informações
        # ...

        try:
            # Extrair data do nome do arquivo
            data_registro = extrair_data(nome_arquivo)
            if not data_registro:
                st.warning(f"Aviso: Data não extraída do arquivo {nome_arquivo}. Registro ignorado.")
                continue

            # Preparar dados para gravação
            dados = {
                "Data": data_registro.strftime("%d-%b-%y"),
                "Elevação": formatar_numero_br(elevacao),
                "Coordenada Este": formatar_numero_br(coordenada_este),
                "Coordenada Norte": formatar_numero_br(coordenada_norte)
            }

            # Processar o arquivo
            file_path = os.path.join(media_path, arquivo_destino)
            resultado = processar_arquivo_excel(file_path, dados, info_gerada.strip())
            
            if resultado == "duplicado":
                st.warning(f"Aviso: Registro duplicado encontrado - Arquivo: {arquivo_destino}, "
                            f"Aba: {info_gerada.strip()}, Data: {dados['Data']}")
                contador_duplicados += 1
            elif resultado == "sucesso":
                st.success(f"Registro inserido - Arquivo: {arquivo_destino}, "
                            f"Aba: {info_gerada.strip()}")
                contador_processados += 1

        except Exception as e:
            st.error(f"Erro ao processar registro: {str(e)}")
            contador_erros += 1
            continue

    # Confirmar mudanças e fechar o banco de dados
    conn.commit()
    conn.close()

    # Relatório final
    st.subheader("Relatório Final")
    st.write(f"Total de registros processados com sucesso: {contador_processados}")
    st.write(f"Total de registros duplicados ignorados: {contador_duplicados}")
    st.write(f"Total de erros encontrados: {contador_erros}")

# Chamar a função de interface Streamlit
if __name__ == "__main__":
    interface_streamlit()