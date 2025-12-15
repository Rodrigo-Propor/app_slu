# Guia Prático - Conversor GDI para TXT

## ?? Tutoriais Passo a Passo

### Tutorial 1: Conversão Básica

#### Objetivo:
Converter arquivos GDI da pasta `perfil/` em arquivos `.txt` com coordenadas.

#### Passos:

**1. Preparar ambiente**
```bash
cd D:\APP\app_slu\topo
```

**2. Verificar se Python está instalado**
```bash
python --version
```

Esperado: `Python 3.11.x` ou superior

**3. Instalar dependências (se necessário)**
```bash
pip install pandas numpy
```

**4. Executar o conversor**
```bash
python converter_perfil.py
```

**5. Verificar resultado**
```bash
dir conversoes_final
```

Você deve ver arquivos como:
```
PERFILM.txt
PERFIL1.txt
PERFIL2.txt
```

**6. Visualizar primeiro arquivo**
```bash
type conversoes_final\PERFILM.txt
```

Saída esperada:
```
Ponto,Descricao,Este,Norte,Cota
P9,R,603410.5553,7798230.8492,879.4790
P6,A,603330.3861,7798121.2425,871.6820
```

---

### Tutorial 2: Processamento com Script Completo

#### Objetivo:
Usar o script `app.py` para processamento mais completo com consolidação.

#### Passos:

**1. Executar script completo**
```bash
python app.py
```

**2. Observar saída**
```
============================================================
CONVERSOR DE COORDENADAS - ESTAÇÃO TOTAL GDI
============================================================

[1/3] Processando arquivos da raiz...
[2/3] Processando arquivos da pasta 'perfil'...
[3/3] Consolidando pontos...

? Processamento concluído!
```

**3. Verificar arquivo consolidado**
```bash
type conversoes_final\pontos_consolidados.txt
```

Este arquivo contém TODOS os pontos de todos os arquivos processados.

---

### Tutorial 3: Integração com Banco de Dados SLU

#### Objetivo:
Importar os dados convertidos para o banco SQLite do projeto.

#### Passos:

**1. Converter arquivos**
```bash
python converter_perfil.py
```

**2. Usar os dados em Python**
```python
import pandas as pd

# Ler arquivo convertido
df = pd.read_csv('conversoes_final/PERFIL1.txt')

# Exibir primeiras linhas
print(df.head())

# Filtrar por tipo de ponto
p_survey = df[df['Descricao'].isin(['PS', 'PE', 'CR'])]

# Salvar em outro formato
df.to_excel('output/PERFIL1.xlsx', index=False)
```

---

## ?? Exemplos de Dados

### Entrada: Arquivo GDI Bruto

**Arquivo:** `PERFILM.unknown`

```
_'B1_(E_)0.450_+M2_ ?+00355391m0885515+0310233d+00355328t00+00+00000_*R_,1.600_+P9_ ?+00373107m0884714+0333449d+00373023t00+00+01234
0000_*A_,1.600_+P6_ ?+00237449m0895739+0320522d+00237449t00+00+00000_*A_,1.600_+P5_ ?+00060612m0911554+0325941d+00060598t00+00+01234
0000_*A_,1.600_+P4_ ?+00012035m0914853+0375705d+00012029t00+00+00000_*A_,1.600_+P3_ ?+00157224m0850644+2115154d+00156651t00+00+01234
```

**Interpretação:**
- Estação: **B1** com altura de instrumento **0.450m**
- Ré: **M2** (para calibração)
- Pontos medidos: P9, P6, P5, P4, P3
- Tipo: R (Ré), A (Alvo)

### Saída: Arquivo TXT Convertido

**Arquivo:** `PERFILM.txt`

```csv
Ponto,Descricao,Este,Norte,Cota
P9,R,603410.5553,7798230.8492,879.4790
P6,A,603330.3861,7798121.2425,871.6820
P5,A,603237.2298,7797970.8793,870.1630
P4,A,603211.6355,7797929.5485,871.0950
P3,A,603121.5513,7797787.0342,884.9400
```

---

## ?? Compreendendo os Dados

### Coordenadas SAD69

O sistema usa o datum **SAD69** (Sistema de Referência Geodésico Sul-Americano).

```
Este (E)    : 603410.5553  (Longitude local, metros)
Norte (N)   : 7798230.8492 (Latitude local, metros)
Cota (Z)    : 879.4790     (Altitude, metros)
```

### Precisão

- **Coordenadas planimétricas (E, N):** 4 casas decimais = ±0.0001m = ±0.1mm
- **Coordenadas altimétricas (Z):** 4 casas decimais = ±0.0001m = ±0.1mm

A precisão é limitada pela estação total (geralmente ±5-10mm em campo).

---

## ??? Troubleshooting Prático

### Problema 1: Arquivo não é processado

**Sintoma:**
```
File: PERFIL_NOVO
  WARNING: No points extracted
```

**Diagnóstico:**
- Arquivo pode estar vazio
- Formato diferente de GDI
- Estação não cadastrada em KNOWN_POINTS

**Solução:**
```bash
# Ver conteúdo do arquivo
type perfil\PERFIL_NOVO

# Se vazio, verificar se foi transmitido corretamente
# Se não vazio, analisar formato
```

---

### Problema 2: Coordenadas erradas ou fora de escala

**Sintoma:**
```
Ponto,Descricao,Este,Norte,Cota
X,R,999999.0000,999999.0000,9999.0000
```

**Diagnóstico:**
- Ponto de estação não está em KNOWN_POINTS
- Altura do instrumento incorreta
- Dados de entrada corrompidos

**Solução:**
1. Verificar se a estação existe:
```python
KNOWN_POINTS.keys()  # Ver estações disponíveis
```

2. Adicionar nova estação se necessário:
```python
KNOWN_POINTS['M8'] = {'N': 7797500.000, 'E': 603300.000, 'Z': 900.000}
```

3. Reconverter arquivo

---

### Problema 3: Pontos faltando

**Sintoma:**
```
Processing completed: 10 file(s) converted
File: PERFIL5.txt
  Extracted: 45 points
```

Mas você esperava mais pontos.

**Possíveis causas:**
- Algumas linhas do arquivo não têm formato válido
- Pontos de código desconhecido foram ignorados
- Arquivo truncado ou corrompido

**Verificação:**
```bash
# Contar linhas no arquivo original
wc -l perfil\PERFIL5
# Resultado deve ser próximo ao número de pontos * linhas

# Ver estrutura
head -20 perfil\PERFIL5
```

---

## ?? Analisando Resultados

### Script Python para análise

```python
import pandas as pd
from pathlib import Path

# Ler arquivo convertido
df = pd.read_csv('conversoes_final/PERFIL1.txt')

# Informações gerais
print(f"Total de pontos: {len(df)}")
print(f"Tipos de pontos: {df['Descricao'].unique()}")
print(f"Coordenadas este: min={df['Este'].min()}, max={df['Este'].max()}")
print(f"Coordenadas norte: min={df['Norte'].min()}, max={df['Norte'].max()}")
print(f"Cotas: min={df['Cota'].min()}, max={df['Cota'].max()}")

# Agrupar por tipo
print("\nPontos por tipo:")
print(df['Descricao'].value_counts())

# Estatísticas
print("\nEstatísticas:")
print(df[['Este', 'Norte', 'Cota']].describe())
```

---

## ?? Workflows Comuns

### Workflow 1: Levantamento Topográfico Completo

```
1. Coleta em Campo
   ?? Estação Total GDI
   ?? Múltiplos perfis
   ?? Coordenadas de controle

2. Download dos dados
   ?? USB da estação
   ?? Arquivos GDI

3. Conversão
   ?? python converter_perfil.py

4. Validação
   ?? Revisar coordenadas
   ?? Detectar outliers
   ?? Comparar com esperado

5. Importação
   ?? Banco SLU
   ?? Relatórios/Mapas
```

### Workflow 2: Monitoramento Contínuo

```
Semana 1
?? Coleta de dados
?? Conversão
?? Armazenamento

Semana 2
?? Coleta de dados
?? Conversão
?? Comparação com Semana 1
?? Detecção de mudanças

Semana 3, 4, ...
?? Repetir Semana 2
```

---

## ?? Exportando para Outros Formatos

### Converter para Excel

```python
import pandas as pd

df = pd.read_csv('conversoes_final/PERFIL1.txt')
df.to_excel('relatorios/PERFIL1_relatorio.xlsx', index=False)
```

### Converter para CSV (separador vírgula)

```python
df = pd.read_csv('conversoes_final/PERFIL1.txt')
df.to_csv('relatorios/PERFIL1.csv', index=False, sep=',')
```

### Gerar KML para Google Earth

```python
import pandas as pd
from pathlib import Path

df = pd.read_csv('conversoes_final/PERFIL1.txt')

kml = """<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
<Document>
"""

for _, row in df.iterrows():
    # Converter para lat/lon (aproximado)
    # Note: Este é um exemplo simplificado
    kml += f"""
  <Placemark>
    <name>{row['Ponto']}</name>
    <description>{row['Descricao']} - Cota: {row['Cota']}</description>
    <Point>
      <coordinates>{row['Este']},{row['Norte']},{row['Cota']}</coordinates>
    </Point>
  </Placemark>
"""

kml += """
</Document>
</kml>
"""

Path('relatorios/pontos.kml').write_text(kml)
```

---

## ? Checklist de Uso

- [ ] Arquivos GDI colocados em `topo/perfil/`
- [ ] Python 3.11+ instalado
- [ ] Dependências instaladas (`pip install pandas numpy`)
- [ ] Executado `converter_perfil.py`
- [ ] Verificado arquivos em `conversoes_final/`
- [ ] Validado formato dos dados
- [ ] Comparado coordenadas com valores esperados
- [ ] Integrado com banco de dados SLU

---

## ?? Recursos Adicionais

- **Formato GDI:** Ver documentação da Estação Total Leica/Topcon
- **SAD69:** Sistema de Referência Geodésico Sul-Americano
- **Pandas:** https://pandas.pydata.org/docs/
- **NumPy:** https://numpy.org/doc/

---

**Última atualização:** 28 de janeiro de 2025
