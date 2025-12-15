# Referência Rápida - Conversor GDI

## ? Início Rápido

```bash
# 1. Navegar para pasta
cd D:\APP\app_slu\topo

# 2. Executar conversão
python converter_perfil.py

# 3. Ver resultados
dir conversoes_final
```

---

## ?? Estrutura de Pastas

```
topo/
?? converter_perfil.py      ? Executar este arquivo
?? app.py                   ? Script alternativo
?? perfil/                  ? Coloque arquivos GDI aqui
?? conversoes_final/        ? Resultados aqui
```

---

## ?? O que cada script faz

| Script | Função | Saída |
|--------|--------|-------|
| `converter_perfil.py` | Converte arquivos da pasta perfil/ | .txt individuais |
| `app.py` | Processa raiz + perfil + consolida | .csv + .txt consolidado |

---

## ?? Formato de Entrada/Saída

**ENTRADA (GDI bruto):**
```
_'B1_(E_)0.450_+M2_ ?+00355391m0885515+0310233d...
_*R_,1.600_+P9_ ?+00373107m0884714+0333449d...
```

**SAÍDA (TXT padrão):**
```
Ponto,Descricao,Este,Norte,Cota
P9,R,603410.5553,7798230.8492,879.4790
```

---

## ?? Requisitos

```
Python 3.11+
pandas
numpy
```

**Instalar:**
```bash
pip install pandas numpy
```

---

## ? Problemas Comuns

| Problema | Solução |
|----------|---------|
| "ModuleNotFoundError" | `pip install pandas numpy` |
| "No points extracted" | Verificar formato do arquivo |
| Coordenadas erradas | Confirmar ponto de estação em KNOWN_POINTS |
| Arquivo não encontrado | Verificar caminho em `topo/perfil/` |

---

## ?? Pontos de Controle Disponíveis

Estações cadastradas: B1, B3, B2, M1, M2, M12, M6, M7, P1, P2, P3, P4, P5, P6, P9, P9B

Ver em: `KNOWN_POINTS` no script

---

## ?? Dicas

1. **Lote processado?** Verificar se todos os arquivos têm "SUCCESS"
2. **Dados suspeitos?** Comparar coordenadas com levantamento anterior
3. **Adicionar ponto novo?** Editar `KNOWN_POINTS` no script
4. **Consolidar múltiplos?** Usar `app.py` para gerar arquivo único

---

## ?? Saída Esperada

```
Processing completed: 10 file(s) converted
- PERFILM.txt: 8 points
- PERFIL1.txt: 55 points
- PERFIL2.txt: 33 points
...
Total: 381 points extracted
```

---

## ?? Recursos

- ?? [Documentação Completa](README_CONVERTER_PERFIL.md)
- ?? [Guia Prático](GUIA_PRATICO_CONVERTER.md)
- ?? [Referência de APIs](#)

---

**Pronto para usar! Execute: `python converter_perfil.py`**
