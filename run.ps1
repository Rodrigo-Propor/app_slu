$ErrorActionPreference = 'Stop'

$venvPython = Join-Path '.venv' 'Scripts\python.exe'
if (-not (Test-Path $venvPython)) {
    py -3.11 -m venv .venv
}

& $venvPython -m pip install --upgrade pip
& $venvPython -m pip install streamlit pandas openpyxl

$port = 8501
while (Test-NetConnection -ComputerName 'localhost' -Port $port -InformationLevel Quiet) { $port++ }
& $venvPython -m streamlit run streamlit_app.py --server.port $port --server.headless true
