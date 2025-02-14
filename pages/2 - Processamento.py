import streamlit as st
import sqlite3
import pandas as pd
import os
from datetime import datetime
import re

def verificar_coluna_processamento():
    conn = sqlite3.connect('arquivos.db')
    cursor = conn.cursor()
    
    # Verifica se a coluna existe
    cursor.execute("PRAGMA table_info(arquivos)")
    colunas = cursor.fetchall()
    coluna_existe = any(coluna[1] == 'processamento' for coluna in colunas)
    
    if not coluna_existe:
        try:
            cursor.execute("ALTER TABLE arquivos ADD COLUMN processamento TEXT DEFAULT 'nao_processado'")
            conn.commit()
            st.success("Coluna 'processamento' adicionada com sucesso!")
        except Exception as e:
            st.error(f"Erro ao adicionar coluna: {str(e)}")
    
    conn.close()

def formatar_placa(descricao, tipo_arquivo):
    descricao = descricao.strip()
    
    if tipo_arquivo == "CELULA EMERGENCIAL":
        if descricao.startswith('L'):
            return f"PR {descricao[1:]}"
    
    elif tipo_arquivo == "INCLINOMETRO":
        return descricao
    
    elif tipo_arquivo == "CELULA DE PESQUISA":
        match = re.search(r'PR(\d+)', descricao)
        if match:
            numero = int(match.group(1))
            return f"PR{numero:02d}"
    
    elif tipo_arquivo == "PAMPULHA":
        if descricao.startswith('D'):
            return descricao
        elif descricao.startswith('A'):
            numero = descricao[1:]
            return f"PR A.{numero}"
        else:
            return f"PR {descricao}"
    
    return descricao

def validar_registro(registro):
    try:
        # Divide o registro por vírgulas
        campos = registro.strip().split(',')
        
        if len(campos) < 5:
            return None
        
        # Validações
        numero = int(campos[0])
        descricao = campos[1].strip()
        este = float(campos[2])
        norte = float(campos[3])
        cota = float(campos[4])
        
        # Validação dos ranges
        if not (599000 <= este <= 700000):
            return None
        if not (6999999 <= norte <= 8000000):
            return None
        if not (850 <= cota <= 999):
            return None
            
        return {
            'numero': numero,
            'descricao': descricao,
            'este': este,
            'norte': norte,
            'cota': cota
        }
    except:
        return None

def processar_arquivo(arquivo, tipo, data):
    registros_validos = []
    
    try:
        with open(arquivo, 'r', encoding='latin-1') as f:
            linhas = f.readlines()
            
        # Pula a primeira linha se começar com M
        inicio = 1 if linhas[0].startswith('M') else 0
        
        for linha in linhas[inicio:]:
            registro = validar_registro(linha)
            if registro:
                registro['tipo'] = tipo
                registro['data'] = data
                registro['descricao'] = formatar_placa(registro['descricao'], tipo)
                registros_validos.append(registro)
                
        return registros_validos
    except Exception as e:
        st.error(f"Erro ao processar arquivo {arquivo}: {str(e)}")
        return []

def salvar_dados_processados(registros):
    conn = sqlite3.connect('banco_dados.db')
    cursor = conn.cursor()
    
    # Cria tabela se não existir
    cursor.execute('''CREATE TABLE IF NOT EXISTS dados_placa_geral
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      dt_data DATE,
                      ct_cota REAL,
                      cd_este REAL,
                      cd_norte REAL,
                      lc_local TEXT,
                      pl_placa TEXT)''')
    
    try:
        for registro in registros:
            cursor.execute('''INSERT INTO dados_placa_geral 
                            (dt_data, ct_cota, cd_este, cd_norte, lc_local, pl_placa)
                            VALUES (?, ?, ?, ?, ?, ?)''',
                         (registro['data'], 
                          registro['cota'],
                          registro['este'],
                          registro['norte'],
                          registro['tipo'],
                          registro['descricao']))
        
        conn.commit()
        return True
    except Exception as e:
        st.error(f"Erro ao salvar dados: {str(e)}")
        return False
    finally:
        conn.close()

def marcar_como_processado(arquivo):
    conn = sqlite3.connect('arquivos.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute("UPDATE arquivos SET processamento = 'processado' WHERE nome_arquivo = ?",
                      (arquivo,))
        conn.commit()
    finally:
        conn.close()

def main():
    st.title("Processamento de Dados Topográficos")
    
    # Verifica/cria coluna de processamento
    verificar_coluna_processamento()
    
    # Busca arquivos não processados
    conn = sqlite3.connect('arquivos.db')
    df = pd.read_sql_query("""
        SELECT nome_arquivo, tipo, dia, mes, ano 
        FROM arquivos 
        WHERE processamento IS NULL 
           OR processamento = 'nao_processado'""", conn)
    conn.close()
    
    if df.empty:
        st.success("Todos os arquivos já foram processados!")
        st.stop()
    
    st.write(f"### {len(df)} arquivo(s) para processar")
    
    if st.button("Iniciar Processamento"):
        for _, row in df.iterrows():
            arquivo = os.path.join('media/originais_txt', row['nome_arquivo'])
            
            if not os.path.exists(arquivo):
                st.warning(f"Arquivo não encontrado: {arquivo}")
                continue
                
            data = datetime(row['ano'], row['mes'], row['dia']).date()
            
            st.write(f"Processando {row['nome_arquivo']}...")
            
            registros = processar_arquivo(arquivo, row['tipo'], data)
            
            if registros:
                if salvar_dados_processados(registros):
                    marcar_como_processado(row['nome_arquivo'])
                    st.success(f"✅ {row['nome_arquivo']}: {len(registros)} registros processados")
                else:
                    st.error(f"❌ Erro ao salvar dados de {row['nome_arquivo']}")
            else:
                st.warning(f"⚠️ Nenhum registro válido encontrado em {row['nome_arquivo']}")

if __name__ == "__main__":
    main()