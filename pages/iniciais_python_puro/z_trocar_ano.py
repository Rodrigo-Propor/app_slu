import os

# Diretório onde os arquivos estão localizados
directory = "media"

# Definindo o texto antigo e o novo
old_year = "Ano 10"
new_year = "Ano 2"

# Iterando por todos os arquivos no diretório
for filename in os.listdir(directory):
    # Verifica se o ano antigo está no nome do arquivo
    if old_year in filename:
        # Define o novo nome, substituindo o ano antigo pelo novo
        new_filename = filename.replace(old_year, new_year)
        
        # Caminhos completos dos arquivos antigo e novo
        old_file_path = os.path.join(directory, filename)
        new_file_path = os.path.join(directory, new_filename)
        
        # Renomeia o arquivo
        os.rename(old_file_path, new_file_path)
        print(f"Renomeado: '{filename}' para '{new_filename}'")
    else:
        print(f"'{filename}' não contém '{old_year}', ignorado.")
