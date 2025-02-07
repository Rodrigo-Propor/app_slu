import sqlite3

# Conectando ao banco de dados
conn = sqlite3.connect('banco_dados.db')
cursor = conn.cursor()

# Criação das tabelas, se não existirem
cursor.execute('''
    CREATE TABLE IF NOT EXISTS SLU_periodos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        mes INTEGER,
        ano_contrato TEXT,
        periodo TEXT UNIQUE
    )
''')

# Criação da tabela para armazenar informações dos arquivos
cursor.execute('''
    CREATE TABLE IF NOT EXISTS SLU_files (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tipo TEXT,
        mes INTEGER,
        ano_contrato TEXT,
        caminho_arquivo TEXT,
        ativo INTEGER,
        data_carregamento TEXT,
        data_remocao TEXT,
        FOREIGN KEY (mes, ano_contrato) REFERENCES SLU_periodos(mes, ano_contrato)
    )
''')

# Salva as alterações
conn.commit()
