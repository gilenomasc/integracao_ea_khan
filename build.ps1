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

if (Test-Path (Join-Path $PSScriptRoot "dist")) {
    Remove-Item (Join-Path $PSScriptRoot "dist") -Recurse -Force
}

$spec = Join-Path $PSScriptRoot "integracao_ea_khan.spec"
& $python -m PyInstaller --noconfirm --clean $spec
if ($LASTEXITCODE -ne 0) {
    throw "Falha ao empacotar o projeto."
}

Write-Host "Pacote criado em .\dist\integracao_ea_khan\"
