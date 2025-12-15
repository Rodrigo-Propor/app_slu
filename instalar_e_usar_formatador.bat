@echo off
echo === Formatador de Tabelas Word ===
echo.

REM Verifica se o Python está instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo ERRO: Python nao encontrado. Por favor, instale o Python primeiro.
    pause
    exit /b 1
)

echo Instalando dependencias...
pip install -r requirements_formatador.txt

if errorlevel 1 (
    echo ERRO: Falha ao instalar dependencias.
    pause
    exit /b 1
)

echo.
echo Dependencias instaladas com sucesso!
echo.
echo Executando o formatador...
python formatar_tabelas_word.py

pause 