import sqlite3
import pandas as pd

# Caminho do arquivo da planilha e do banco de dados
excel_path = 'media/template/dados_ate_outubro_24.xlsx'
db_path = 'banco_dados.db'

# Conectar ao banco de dados
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Verificar se a tabela existe, caso contrário, criar
table_name = 'dados_placa_geral'
cursor.execute(f'''
    CREATE TABLE IF NOT EXISTS {table_name} (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        dt_data TEXT,
        ct_cota REAL,
        cd_este REAL,
        cd_norte REAL,
        lc_local TEXT,
        pl_placa TEXT,
        lp_local_placa TEXT,
        obs1 TEXT,
        obs2 TEXT,
        obs3 TEXT
    )
''')
print("Tabela 'dados_placa_geral' verificada/criada com sucesso.")

try:
    # Carregar dados do Excel
    data_df = pd.read_excel(excel_path, usecols="A:J")
    data_df.columns = ["dt_data", "ct_cota", "cd_este", "cd_norte", "lc_local", "pl_placa", "lp_local_placa", "obs1", "obs2", "obs3"]

    # Converter colunas para os tipos adequados sem substituição de vírgulas
    data_df["ct_cota"] = pd.to_numeric(data_df["ct_cota"], errors='coerce')
    data_df["cd_este"] = pd.to_numeric(data_df["cd_este"], errors='coerce')
    data_df["cd_norte"] = pd.to_numeric(data_df["cd_norte"], errors='coerce')
    data_df["dt_data"] = data_df["dt_data"].dt.strftime('%Y-%m-%d')  # Converter dt_data para string no formato 'YYYY-MM-DD'

    # Remover linhas com valores inválidos nas colunas principais
    invalid_rows = data_df[data_df[['dt_data', 'ct_cota', 'cd_este', 'cd_norte']].isnull().any(axis=1)]
    if not invalid_rows.empty:
        print("Aviso: Linhas com valores inválidos encontrados e removidos:")
        print(invalid_rows)

    data_df.dropna(subset=["dt_data", "ct_cota", "cd_este", "cd_norte"], inplace=True)

    # Verificar se ainda há dados válidos para inserir
    registros_copiados = 0
    registros_duplicados = 0
    registros_duplicados_lista = []
    registros_invalidos = 0  # Contador para registros que não atendem aos critérios de faixa

    if data_df.empty:
        print("Nenhum dado válido encontrado após limpeza. Verifique os dados na planilha.")
    else:
        # Ordenar os dados
        data_df.sort_values(by=["dt_data", "lc_local", "pl_placa"], inplace=True)

        # Inserir dados no banco de dados
        for _, row in data_df.iterrows():
            dt_data = row["dt_data"]
            ct_cota = row["ct_cota"]
            cd_este = row["cd_este"]
            cd_norte = row["cd_norte"]

            # Verificação dos critérios de faixa
            if not (100 <= ct_cota <= 999.999 and 600000 <= cd_este <= 699999.999 and 7000000 <= cd_norte <= 7999999.999):
                registros_invalidos += 1
                print(f"Registro inválido removido - cota: {ct_cota}, este: {cd_este}, norte: {cd_norte}")
                continue

            # Verificar duplicata
            cursor.execute(f'''
                SELECT COUNT(*) FROM {table_name} 
                WHERE dt_data = ? AND cd_norte = ? AND cd_este = ? AND ct_cota = ?
            ''', (dt_data, cd_norte, cd_este, ct_cota))
            
            if cursor.fetchone()[0] == 0:  # Registro único
                try:
                    cursor.execute(f'''
                        INSERT INTO {table_name} 
                        (dt_data, ct_cota, cd_este, cd_norte, lc_local, pl_placa, lp_local_placa, obs1, obs2, obs3)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (dt_data, ct_cota, cd_este, cd_norte, row["lc_local"], row["pl_placa"], row["lp_local_placa"], row["obs1"], row["obs2"], row["obs3"]))
                    registros_copiados += 1
                except Exception as e:
                    print(f"Erro ao inserir registro {row}: {e}")
            else:
                registros_duplicados += 1
                registros_duplicados_lista.append((dt_data, cd_norte, cd_este, ct_cota))

except Exception as e:
    print(f"Erro ao processar o arquivo Excel: {e}")

# Salvar as alterações no banco de dados
conn.commit()
conn.close()

# Exibir o resumo
print(f"\nProcesso concluído. Registros copiados: {registros_copiados}")
print(f"Registros duplicados ignorados: {registros_duplicados}")
print(f"Registros inválidos removidos: {registros_invalidos}")
print("Detalhes dos registros duplicados:")
for registro in registros_duplicados_lista:
    print(registro)
