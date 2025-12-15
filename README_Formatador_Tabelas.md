# Formatador de Tabelas Word

Este script Python formata automaticamente todas as tabelas de um arquivo Microsoft Word (.docx) com as seguintes características:

## Funcionalidades

- **Estilo "Sem Espaçamento"**: Remove espaçamentos extras entre linhas e parágrafos
- **Ajuste Automático**: Aplica ajuste automático às células das tabelas
- **Centralização de Texto**: Centraliza horizontalmente e verticalmente todo o texto das tabelas
- **Interface Gráfica**: Permite selecionar o arquivo através de uma janela de diálogo
- **Preservação**: Cria uma cópia formatada do arquivo original

## Requisitos

- Python 3.6 ou superior
- Biblioteca `python-docx`

## Instalação e Uso

### Método 1: Script Automático (Recomendado)

1. Execute o arquivo `instalar_e_usar_formatador.bat`
2. O script irá:
   - Verificar se o Python está instalado
   - Instalar as dependências necessárias
   - Executar o formatador

### Método 2: Instalação Manual

1. Abra o terminal/prompt de comando
2. Navegue até a pasta do projeto
3. Execute os comandos:

```bash
pip install -r requirements_formatador.txt
python formatar_tabelas_word.py
```

### Método 3: Linha de Comando

```bash
python formatar_tabelas_word.py "caminho/para/seu/arquivo.docx"
```

## Como Funciona

1. **Seleção do Arquivo**: 
   - Se nenhum arquivo for especificado, uma janela de diálogo será aberta
   - Se um caminho for fornecido como argumento, esse arquivo será usado

2. **Processamento**:
   - O script identifica todas as tabelas no documento
   - Aplica o estilo "Sem Espaçamento" a todos os parágrafos das tabelas
   - Configura ajuste automático para as células

3. **Saída**:
   - Cria um novo arquivo com sufixo "_formatado"
   - Exemplo: `documento.docx` → `documento_formatado.docx`

## Exemplo de Uso

```bash
# Executar com seleção de arquivo via interface gráfica
python formatar_tabelas_word.py

# Executar com arquivo específico
python formatar_tabelas_word.py "media/word/tabelas_relatorio_11_07_25.docx"
```

## Formatações Aplicadas

### Estilo "Sem Espaçamento"
- Espaçamento antes do parágrafo: 0
- Espaçamento depois do parágrafo: 0
- Espaçamento entre linhas: 1.0 (simples)

### Ajuste Automático
- `table.autofit = True`
- Alinhamento vertical centralizado nas células
- Remoção de espaçamentos extras nos textos

### Centralização de Texto
- Alinhamento horizontal centralizado em todos os parágrafos
- Alinhamento vertical centralizado em todas as células
- Aplicado tanto ao texto quanto aos números nas tabelas

## Tratamento de Erros

- Verifica se o arquivo existe
- Trata erros de formatação individualmente
- Exibe mensagens informativas sobre o progresso
- Mostra notificações de sucesso ou erro

## Arquivos Gerados

- `formatar_tabelas_word.py`: Script principal
- `requirements_formatador.txt`: Dependências Python
- `instalar_e_usar_formatador.bat`: Script de instalação automática
- `README_Formatador_Tabelas.md`: Este arquivo de instruções

## Suporte

Se encontrar problemas:
1. Verifique se o Python está instalado corretamente
2. Certifique-se de que o arquivo Word não está aberto em outro programa
3. Verifique se o arquivo é um .docx válido
4. Execute o script novamente 