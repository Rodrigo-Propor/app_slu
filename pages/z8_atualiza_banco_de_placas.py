import sqlite3
import re
from datetime import datetime
import streamlit as st

def transform_tipo(tipo):
    """Transforma o tipo no formato correto"""
    tipo_map = {
        'emergencial': 'CELULA EMERGENCIAL',
        'pampulha': 'PAMPULHA',
        'pesquisa': 'CELULA DE PESQUISA',
        'inclinometro': 'INCLINOMETRO'
    }
    return tipo_map.get(tipo.lower(), tipo.upper())

def extract_date_from_filename(filename):
    """Extrai a data do nome do arquivo no formato DDMMAA e converte para YYYY-MM-DD"""
    try:
        pattern = r'(\d{6})M\.TXT'
        match = re.search(pattern, filename)
        if match:
            date_str = match.group(1)
            date_obj = datetime.strptime(date_str, '%d%m%y')
            return date_obj.strftime('%Y-%m-%d')
    except (ValueError, AttributeError) as e:
        st.warning(f"Erro ao extrair data do arquivo {filename}: {str(e)}")
        return None
    return None

def sync_tables():
    try:
        conn = sqlite3.connect('banco_dados.db')
        cursor = conn.cursor()

        # Verifica se todas as colunas necessárias existem
        cursor.execute("""
            SELECT * FROM dados_placa_geral LIMIT 1
        """)
        existing_columns = [description[0] for description in cursor.description]
        required_columns = ['dt_data', 'ct_cota', 'cd_este', 'cd_norte', 'lc_local', 
                          'pl_placa', 'obs1', 'obs2', 'obs3']
        
        missing_columns = [col for col in required_columns if col not in existing_columns]
        
        if missing_columns:
            st.error(f"Faltam as seguintes colunas na tabela dados_placa_geral: {', '.join(missing_columns)}")
            st.warning("Por favor, crie as colunas necessárias antes de continuar.")
            if st.button("Criar colunas faltantes"):
                for col in missing_columns:
                    try:
                        cursor.execute(f"ALTER TABLE dados_placa_geral ADD COLUMN {col} TEXT")
                    except sqlite3.OperationalError as e:
                        st.error(f"Erro ao criar coluna {col}: {str(e)}")
                conn.commit()
                st.success("Colunas criadas com sucesso!")
                st.rerun()
            return

        # Busca registros da tabela placas_completas_slu_bh
        cursor.execute("""
            SELECT id, tipo, descricao, coordenada_este, coordenada_norte, 
                   elevacao, info_gerada, nome_arquivo
            FROM placas_completas_slu_bh
        """)
        registros = cursor.fetchall()

        total_registros = len(registros)
        registros_inseridos = 0
        registros_ignorados = 0
        erros = 0
        
        st.info(f"Total de registros encontrados: {total_registros}")
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        error_text = st.empty()

        for i, registro in enumerate(registros):
            try:
                (id_original, tipo, descricao, coord_este, coord_norte, 
                 elevacao, info_gerada, nome_arquivo) = registro

                # Extrai a data do nome do arquivo
                data = extract_date_from_filename(nome_arquivo)
                if not data:
                    st.warning(f"Não foi possível extrair a data do arquivo: {nome_arquivo}")
                    erros += 1
                    continue

                # Verifica se já existe registro com mesma localização e data
                cursor.execute("""
                    SELECT COUNT(*) FROM dados_placa_geral 
                    WHERE cd_este = ? AND cd_norte = ? AND dt_data = ?
                """, (coord_este, coord_norte, data))
                
                if cursor.fetchone()[0] == 0:
                    cursor.execute("""
                        INSERT INTO dados_placa_geral 
                        (dt_data, ct_cota, cd_este, cd_norte, lc_local, 
                         pl_placa, obs1, obs2, obs3)
                        VALUES (?, ?, ?, ?, ?, ?, NULL, ?, ?)
                    """, (
                        data, 
                        elevacao, 
                        coord_este, 
                        coord_norte, 
                        transform_tipo(tipo),
                        info_gerada,
                        nome_arquivo,
                        descricao
                    ))
                    registros_inseridos += 1
                else:
                    registros_ignorados += 1

            except Exception as e:
                st.error(f"Erro ao processar registro {id_original}: {str(e)}")
                erros += 1
                continue

            finally:
                # Atualiza a barra de progresso
                progress = (i + 1) / total_registros
                progress_bar.progress(progress)
                status_text.text(f"Processando... {i+1}/{total_registros}")
                error_text.text(f"Erros encontrados: {erros}")

        conn.commit()
        
        st.success(f"""
        Sincronização concluída!
        - Total de registros processados: {total_registros}
        - Registros inseridos com sucesso: {registros_inseridos}
        - Registros ignorados (duplicados): {registros_ignorados}
        - Erros encontrados: {erros}
        """)

    except sqlite3.Error as e:
        st.error(f"Erro no banco de dados: {str(e)}")
    finally:
        conn.close()

def main():
    st.title("Sincronização de Dados das Placas")
    
    st.write("""
    ### Mapeamento de Colunas
    - coordenada_este -> cd_este
    - coordenada_norte -> cd_norte
    - elevacao -> ct_cota
    - info_gerada -> pl_placa
    - nome_arquivo -> obs2
    - tipo -> lc_local (com transformação)
    - descricao -> obs3
    
    ### Transformação dos Tipos
    - emergencial -> CELULA EMERGENCIAL
    - pampulha -> PAMPULHA
    - pesquisa -> CELULA DE PESQUISA
    - inclinometro -> INCLINOMETRO
    """)
    
    if st.button("Iniciar Sincronização"):
        sync_tables()

if __name__ == "__main__":
    main()