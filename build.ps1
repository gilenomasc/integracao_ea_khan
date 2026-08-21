<#!
.SYNOPSIS
Gera os executaveis de console para distribuicao no Windows.

.DESCRIPTION
Execute em um ambiente virtual de desenvolvimento com as dependencias de
requirements.txt e requirements-dev.txt instaladas. O resultado fica em dist/.
#>

$ErrorActionPreference = "Stop"
$venvPython = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
$python = if (Test-Path $venvPython) { $venvPython } else { "python" }

$icon = Join-Path $PSScriptRoot "assets\EA_Khan.ico"

if (-not (Test-Path $icon)) {
    throw "Arquivo de ícone não encontrado: $icon"
}

$entries = @(
    "main_ea.py",
    "main_ea_grade_save.py",
    "main_khan.py",
    "main_khan_progress.py",
    "unify_etapas.py"
)

foreach ($entry in $entries) {
    & $python -m PyInstaller --noconfirm --clean --onedir --icon $icon --console --add-data "queries;queries" $entry
    if ($LASTEXITCODE -ne 0) {
        throw "Falha ao empacotar $entry."
    }
}

Write-Host "Pacotes criados em .\dist\"
