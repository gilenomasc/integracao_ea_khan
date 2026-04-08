# integracao_ea_khan

Projeto unificado para EA + Khan Academy com um unico ambiente virtual.

## Scripts

- `main_ea.py`
- `main_khan.py`
- `unify_etapas.py`

## Estrutura

- `integracao_ea_khan/ea`: cliente e servicos da exportacao EA
- `integracao_ea_khan/khan`: cliente e servicos da exportacao Khan
- `integracao_ea_khan/matching`: correlacao de alunos entre EA e Khan
- `integracao_ea_khan/integration`: consolidacao do JSON unificado

## Execucao

```powershell
.\.venv\Scripts\python.exe main_ea.py tests\etapa_ea_alunos.json EMAIL SENHA
.\.venv\Scripts\python.exe main_khan.py EMAIL SENHA --etapa-ea-file tests\etapa_ea_alunos.json
.\.venv\Scripts\python.exe unify_etapas.py --ea-email EMAIL --ea-password SENHA --khan-email EMAIL --khan-password SENHA
```

## Testes

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -p "test_*.py"
```
# integracao_ea_khan
