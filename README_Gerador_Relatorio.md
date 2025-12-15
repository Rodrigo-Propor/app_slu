# Gerador de Relatório Word com Template

Este script Python gera um relatório Word com tabelas formatadas usando dados do banco SQLite e um template personalizado.

## Funcionalidades

- **Conexão com Banco SQLite**: Lê dados da tabela `placas_completas_slu_bh`
- **Filtro por Período**: Considera apenas os últimos 5 meses de dados
- **Mapeamento de Placas**: Distribui automaticamente as placas nas 7 tabelas corretas
- **Ordenação por Data**: Ordena os dados de cada tabela por data (crescente)
- **Formatação com Template**: Usa um template Word para garantir formatação consistente
- **Formatação de Dados**: Aplica formatação brasileira (vírgula como separador decimal)

## Arquivos Necessários

### 1. Script Principal
- `gerador_word_com_template.py` - Script principal

### 2. Template Word
- `template_tabela.docx` - Arquivo Word com uma tabela modelo formatada

### 3. Banco de Dados
- `banco_dados_completo/banco_dados.db` - Banco SQLite com os dados

## Como Criar o Template

1. **Abra o Microsoft Word**
2. **Crie uma nova tabela** com 5 colunas:
   - PLACA
   - DATA  
   - COTA
   - COORDENADA ESTE
   - COORDENADA NORTE
3. **Formate a tabela** exatamente como deseja:
   - Cores de cabeçalho
   - Fontes e tamanhos
   - Bordas e alinhamento
   - Estilo de tabela (ex: "Tabela de Grade 4 - Ênfase 1")
4. **Deixe apenas o cabeçalho** - remova linhas de exemplo
5. **Salve como** `template_tabela.docx`

## Estrutura das Tabelas

O script gera 7 tabelas na seguinte ordem:

1. **Recalques Celula Pesquisa** - Placas PR01 a PR15
2. **Placa de Recalque Emergencial** - Placas PR 1.1 a PR 3.4
3. **Placa de Recalque AC 01** - Placas PR 1.1 a PR 1.45, D1, D2
4. **Placa de Recalque AC 03** - Placas PR 3.21 a PR 3.31
5. **Placa de Recalque AC 04** - Placas PR 4.1 a PR 4.51
6. **Placa de Recalque AC 05** - Placas PR 5.1 a PR 5.56
7. **Placa de Recalque AMPLIAÇÃO** - Placas PR A.1 a PR A.9

## Como Executar

1. **Certifique-se de que todos os arquivos estão na pasta correta**
2. **Execute o script**:
   ```bash
   python gerador_word_com_template.py
   ```
3. **Verifique o resultado**: `relatorio_final.docx`

## Formatação Aplicada

### Datas
- Formato: `dd-mmm-yy` (ex: 15-jan-25)
- Meses em português abreviado

### Cotas
- Formato: `xxx,xxx` (vírgula como separador decimal)
- 3 casas decimais

### Coordenadas
- Formato: `xxx.xxx,xxx` (ponto como separador de milhares, vírgula como decimal)
- 3 casas decimais

## Dependências

- `python-docx` - Manipulação de arquivos Word
- `pandas` - Processamento de dados
- `python-dateutil` - Manipulação de datas
- `sqlite3` - Conexão com banco de dados (incluído no Python)

## Instalação das Dependências

```bash
pip install python-docx pandas python-dateutil
```

## Estrutura do Banco de Dados

O script espera uma tabela `placas_completas_slu_bh` com as colunas:
- `placa` - Código da placa
- `data` - Data da medição (formato YYYY-MM-DD)
- `elevacao` - Cota/elevação
- `coordenada_este` - Coordenada Este
- `coordenada_norte` - Coordenada Norte

## Solução de Problemas

### Erro: "Arquivo template não encontrado"
- Verifique se o arquivo `template_tabela.docx` existe na pasta

### Erro: "Nenhuma tabela encontrada no template"
- Certifique-se de que o template tem pelo menos uma tabela

### Erro: "Nenhuma data válida encontrada"
- Verifique se a coluna `data` no banco tem formato YYYY-MM-DD

### Tabelas vazias
- Verifique se há dados no período dos últimos 5 meses
- Confirme se o mapeamento de placas está correto

## Arquivo de Saída

O script gera o arquivo `relatorio_final.docx` com:
- Título de cada tabela em maiúsculas
- Dados ordenados por data
- Formatação idêntica ao template
- Quebra de página entre tabelas 