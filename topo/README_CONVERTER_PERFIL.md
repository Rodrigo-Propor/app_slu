# Conversor GDI para TXT - Documentação

## ?? Visão Geral

O **Conversor GDI para TXT** é uma ferramenta Python que processa arquivos de dados brutos da **Estação Total GDI** e converte as coordenadas em arquivos `.txt` padronizados com o formato:

```
Ponto,Descricao,Este,Norte,Cota
```

Este documento descreve como usar, entender e manter a funcionalidade.

---

## ?? Objetivo

Converter dados topográficos coletados em campo com equipamento de estação total em coordenadas georeferenciadas (SAD69) calculadas com precisão.

### Funcionalidades principais:
- ? Parse de arquivos GDI brutos da estação total
- ? Cálculo de coordenadas (Este, Norte, Cota)
- ? Calibração automática de azimutes
- ? Suporte a múltiplos pontos de estação
- ? Exportação em formato TXT padrão
- ? Processamento em lote de múltiplos arquivos

---

## ??? Estrutura do Projeto

```
topo/
??? converter_perfil.py          # Script principal de conversão
??? app.py                       # Script alternativo com mais funcionalidades
??? perfil/                      # Pasta com arquivos GDI para processar
?   ??? PERFILM.unknown
?   ??? PERFIL1
?   ??? PERFIL2
?   ??? ...
??? conversoes_final/            # Saída dos arquivos convertidos
?   ??? PERFILM.txt
?   ??? PERFIL1.txt
?   ??? PERFIL2.txt
?   ??? ...
??? txt/                         # Arquivos de referência de marcas
    ??? EM*.TXT
    ??? ICL*.TXT
```

---

## ?? Dependências

```
pandas
numpy
python-dateutil (opcional)
pathlib (built-in)
re (built-in)
math (built-in)
```

### Instalação de dependências:

```bash
pip install pandas numpy
```

---

## ?? Como Usar

### Método 1: Script Simplificado (Recomendado)

```bash
python converter_perfil.py
```

**O que faz:**
1. Procura arquivos na pasta `topo/perfil/`
2. Converte cada arquivo em coordenadas
3. Salva os resultados em `topo/conversoes_final/` como `.txt`
4. Exibe relatório de processamento

### Método 2: Script Completo

```bash
python app.py
```

**O que faz:**
1. Processa arquivos da raiz
2. Processa arquivos da pasta `perfil/`
3. Consolida todos os pontos em arquivo único
4. Gera relatórios consolidados

---

## ?? Banco de Dados de Pontos de Controle

O script utiliza um banco de dados com coordenadas conhecidas (SAD69) para calibração:

```python
KNOWN_POINTS = {
    'B1':  {'N': 7797920.066, 'E': 603204.240, 'Z': 872.612},
    'B3':  {'N': 7797702.453, 'E': 603701.764, 'Z': 917.476},
    'P9':  {'N': 7798230.8492, 'E': 603410.5553, 'Z': 879.479},
    # ... mais pontos
}
```

### Estrutura:
- **N**: Coordenada NORTE (latitude local)
- **E**: Coordenada ESTE (longitude local)
- **Z**: Cota / Elevação (altitude)

**Fonte:** "COORDENADAS - MARCOS SLU (1).txt"

---

## ?? Fluxo de Processamento

```
Arquivo GDI Bruto
    ?
[1] Parsing do arquivo com Regex
    ?? Extrai estação atual
    ?? Extrai ré (backsight)
    ?? Extrai pontos irradiados
    ?
[2] Calibração de Azimutes
    ?? Calcula azimute verdadeiro (Estação ? Ré)
    ?? Compara com leitura do instrumento
    ?? Calcula correção angular
    ?
[3] Cálculo de Coordenadas
    ?? Converte ângulos DMS ? Decimal
    ?? Calcula distância horizontal
    ?? Calcula diferença de nível
    ?? Transforma para coordenadas globais
    ?
[4] Exportação
    ?? Salva em arquivo .txt
```

---

## ?? Algoritmos Principais

### 1. Conversão DMS para Decimal

Converte ângulos no formato "GGGMMSS" (Graus, Minutos, Segundos) para graus decimais.

```python
def dms_to_decimal(dms_str):
    # Exemplo: "0885515" ? 88 graus 55 minutos 15 segundos
    # Resultado: 88.9208333... graus
```

### 2. Cálculo de Azimute

Calcula o ângulo verdadeiro entre dois pontos usando coordenadas conhecidas.

```python
def get_azimuth(n1, e1, n2, e2):
    # Fórmula: azimute = atan2(?E, ?N) em radianos
    # Converte para graus (0-360°)
```

### 3. Transformação de Coordenadas

Calcula coordenadas finais usando:
- Ponto inicial (estação)
- Distância inclinada (slope distance)
- Ângulo horizontal (azimute)
- Ângulo vertical (ângulo zenital)
- Altura do instrumento (HI)
- Altura do prisma (ht)

**Fórmulas:**
```
distância_horizontal = distância_inclinada × cos(ângulo_vertical)
diferença_nível = distância_inclinada × sin(ângulo_vertical)

norte_final = norte_inicial + distância_horizontal × cos(azimute)
este_final = este_inicial + distância_horizontal × sin(azimute)
cota_final = cota_inicial + altura_instrumento + diferença_nível - altura_prisma
```

---

## ?? Formato de Arquivo GDI

O arquivo GDI é um formato proprietário da estação total que contém dados estruturados assim:

```
_'[ESTACAO]_(E_)[ALTURA_INSTRUMENTO]_+[RÉ]_ ?+[DIST]m[AZIMUTE]+[VERT]d...
_*[CODIGO],1.600_+[PONTO]_ ?+[DIST]m[AZIMUTE]+[VERT]d...
```

### Exemplo real:
```
_'B1_(E_)0.450_+M2_ ?+00355391m0885515+0310233d...
_*R_,1.600_+P9_ ?+00373107m0884714+0333449d...
_*A_,1.600_+P6_ ?+00237449m0895739+0320522d...
```

### Campos:
- **ESTACAO**: Ponto onde o instrumento está instalado
- **ALTURA_INSTRUMENTO**: Altura do aparelho (HI) em metros
- **RÉ**: Ponto de referência para calibração
- **CODIGO**: Código/descrição do ponto (R, A, PS, PE, CR, etc)
- **PONTO**: Nome/ID do ponto medido
- **DIST**: Distância inclinada (em milímetros)
- **AZIMUTE**: Ângulo horizontal (formato GGGMMSS)
- **VERT**: Ângulo vertical/zenital (formato GGGMMSS)

---

## ?? Formato de Saída .TXT

Os arquivos gerados seguem este padrão:

```csv
Ponto,Descricao,Este,Norte,Cota
P9,R,603410.5553,7798230.8492,879.4790
P6,A,603330.3861,7798121.2425,871.6820
P5,A,603237.2298,7797970.8793,870.1630
```

### Colunas:
- **Ponto**: ID/Nome do ponto medido
- **Descricao**: Código/descrição (tipo de medição)
- **Este**: Coordenada E (longitude local) - 4 casas decimais
- **Norte**: Coordenada N (latitude local) - 4 casas decimais
- **Cota**: Elevação/altitude em metros - 4 casas decimais

---

## ?? Exemplo de Uso Prático

### Cenário:
Você tem 5 arquivos GDI coletados em campo e quer convertê-los em coordenadas.

### Passo 1: Organizar arquivos
```
topo/perfil/
??? PERFILM        (arquivo 1)
??? PERFIL1        (arquivo 2)
??? PERFIL2        (arquivo 3)
??? ...
```

### Passo 2: Executar conversão
```bash
cd D:\APP\app_slu\topo
python converter_perfil.py
```

### Passo 3: Saída
```
============================================================
GDI to TXT Converter
Total Station GDI File to Text File
============================================================

Processing files from folder: D:\APP\app_slu\topo\perfil
------------------------------------------------------------

File: PERFILM
  SUCCESS: PERFILM.txt
  Extracted: 8 points

File: PERFIL1
  SUCCESS: PERFIL1.txt
  Extracted: 55 points

...

Processing completed: 5 file(s) converted
Output folder: D:\APP\app_slu\topo\conversoes_final
```

### Passo 4: Visualizar resultados
```bash
cat conversoes_final/PERFIL1.txt
```

---

## ?? Troubleshooting

### Problema: "ModuleNotFoundError: No module named 'pandas'"

**Solução:**
```bash
pip install pandas numpy
```

Ou use o Python do ambiente virtual:
```bash
.venv311\Scripts\python.exe converter_perfil.py
```

---

### Problema: "No points extracted" para um arquivo

**Possíveis causas:**
1. Arquivo não tem formato GDI válido
2. Estação não está no banco de dados de pontos conhecidos
3. Arquivo está vazio ou corrompido

**Solução:**
- Verificar se o arquivo tem o padrão correto
- Adicionar a estação ao dicionário `KNOWN_POINTS`
- Reconverter o arquivo da estação total

---

### Problema: Coordenadas incorretas

**Possíveis causas:**
1. Pontos de controle (KNOWN_POINTS) com valores errados
2. Altura do instrumento (HI) incorreta
3. Sistema de coordenadas diferente

**Solução:**
- Validar coordenadas dos marcos de referência
- Verificar medição da altura do instrumento
- Confirmar que os dados estão em SAD69

---

## ?? Referência de Pontos Disponíveis

Confira quais marcos estão cadastrados no sistema:

| ID | Nome | Norte | Este | Cota |
|----|----|-------|------|------|
| B1 | Marco B1 | 7797920.066 | 603204.240 | 872.612 |
| B3 | Marco B3 | 7797702.453 | 603701.764 | 917.476 |
| M1 | Marco M1 | 7797895.410 | 603166.188 | 866.415 |
| M2 | Marco M2 | 7798224.951 | 603387.740 | 878.446 |
| P1 | Marco P1 | 7797725.0599 | 603037.4223 | 900.518 |
| P2 | Marco P2 | 7797727.7990 | 603081.9594 | 896.213 |
| P3 | Marco P3 | 7797787.0342 | 603121.5513 | 884.940 |
| P4 | Marco P4 | 7797929.5485 | 603211.6355 | 871.095 |
| P5 | Marco P5 | 7797970.8793 | 603237.2298 | 870.163 |
| P6 | Marco P6 | 7798121.2425 | 603330.3861 | 871.682 |
| P9 | Marco P9 | 7798230.8492 | 603410.5553 | 879.479 |
| P9B | Marco P9B | 7798066.9662 | 603659.2369 | 929.346 |

---

## ?? Configuração Avançada

### Adicionar novo ponto de controle

Edite a seção `KNOWN_POINTS` no script:

```python
KNOWN_POINTS = {
    # ... pontos existentes ...
    'M8':  {'N': 7797500.000, 'E': 603300.000, 'Z': 900.000},  # Novo
}
```

### Calibração manual de azimute

Se você souber o azimute exato, passe como parâmetro:

```python
df = parse_gd2i_file(conteudo, KNOWN_POINTS, calib_theta=45.5)
```

---

## ?? Validação de Dados

### Checklist de qualidade:

- [ ] Arquivo GDI válido e não corrompido
- [ ] Estação e Ré estão em KNOWN_POINTS
- [ ] Altura do instrumento registrada corretamente
- [ ] Pontos extraídos aparecem no relatório
- [ ] Coordenadas dentro do intervalo esperado
- [ ] Nenhuma coordenada com valores NaN (missing)

---

## ?? Suporte e Manutenção

### Reportar problemas:
1. Verifique se o arquivo GDI é válido
2. Confirme que as dependências estão instaladas
3. Verifique os logs de processamento
4. Teste com um arquivo conhecido que funcione

### Melhorias futuras:
- [ ] Suporte para mais sistemas de coordenadas
- [ ] Interface gráfica (GUI)
- [ ] Importação automática para banco de dados
- [ ] Visualização de pontos em mapa
- [ ] Cálculo de erro e precisão

---

## ?? Histórico de Versão

| Versão | Data | Alterações |
|--------|------|-----------|
| 1.0 | 2025-01-28 | Versão inicial |
| 1.1 | - | Suporte para multiplos formatos GDI |

---

## ?? Licença

Este código é parte do projeto SLU de monitoramento geotécnico.

---

**Última atualização:** 28 de janeiro de 2025

**Autor:** Desenvolvido para processamento de dados topográficos SLU

**Status:** ? Funcional e testado
