# integracao_ea_khan

Projeto unificado para EA + Khan Academy com um unico ambiente virtual.

## Scripts

- `main_ea.py`
- `main_ea_grade_save.py`
- `main_khan.py`
- `main_khan_progress.py`
- `unify_etapas.py`

## Estrutura

- `integracao_ea_khan/ea`: cliente e servicos da exportacao EA
- `integracao_ea_khan/khan`: cliente e servicos da exportacao Khan
- `integracao_ea_khan/matching`: correlacao de alunos entre EA e Khan
- `integracao_ea_khan/integration`: consolidacao do JSON unificado

## Execucao

```powershell
.\.venv\Scripts\python.exe main_ea.py tests\etapa_ea_alunos.json EMAIL SENHA
.\.venv\Scripts\python.exe main_ea_grade_save.py estudo_exemlo_notas.json EMAIL SENHA
.\.venv\Scripts\python.exe main_ea_grade_save.py estudo_exemlo_notas.json EMAIL SENHA --apply
.\.venv\Scripts\python.exe main_khan.py EMAIL SENHA --etapa-ea-file tests\etapa_ea_alunos.json
.\.venv\Scripts\python.exe unify_etapas.py --ea-email EMAIL --ea-password SENHA --khan-email EMAIL --khan-password SENHA
.\.venv\Scripts\python.exe main_khan_progress.py EMAIL SENHA --unified-file tests\unified\unified_matches.json --simplified-output-file tests\unified\progress_simplified.json
```

`main_ea_grade_save.py` apenas valida a carga por padrao. A opcao `--apply` e necessaria para gravar as notas.

## Testes

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -p "test_*.py"
```

## Distribuicao Windows

Os arquivos de sessao, cache e saidas padrao sao gravados em
`%LOCALAPPDATA%\IntegracaoEA-Khan`, fora da pasta de instalacao. Os caminhos
informados pelo Excel/VBA continuam sendo respeitados pelos argumentos do console.

Para gerar os executaveis de console no ambiente de desenvolvimento:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\build.ps1
```

O script cria um pacote unico em `dist\integracao_ea_khan\`, com todos os
pontos de entrada e uma unica pasta de dependencias compartilhadas. Distribua
essa pasta inteira quando for utilizar `unify_etapas.exe`. A pasta `queries\` e
incluida automaticamente; `auth\` e `state\` nao fazem parte do pacote.
# integracao_ea_khan
