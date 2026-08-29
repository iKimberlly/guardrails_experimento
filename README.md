# Ambiente experimental — Regex + Agente Guardrails

Ambiente independente para reproduzir e ampliar a avaliação descrita no artigo.

## Objetivo

Comparar três configurações usando exatamente as mesmas entradas:

1. `regex` — somente validação determinística;
2. `agent` — somente agente semântico;
3. `combined` — Regex primeiro, agente depois.

O ambiente apenas classifica texto. Não executa comandos, não acessa banco corporativo e não realiza ações destrutivas.

## Estrutura

- `app/main.py` — API FastAPI.
- `app/regex_guard.py` — regras determinísticas experimentais.
- `app/agent.py` — agente semântico; começa em modo `mock` e pode usar endpoint OpenAI-compatible.
- `app/models.py` — modelos de entrada/saída.
- `benchmark.py` — executa um CSV de prompts nas três configurações.
- `data/prompts.csv` — dataset inicial pequeno para validar o ambiente.
- `postman/collection.json` — coleção para testes manuais.
- `results/` — resultados dos experimentos.

## 1. Criar ambiente virtual no Windows

    python -m venv .venv
    .venv\Scripts\activate

## 2. Instalar dependências

    pip install -r requirements.txt

## 3. Configurar

Copie `.env.example` para `.env`.

Para validar o ambiente sem LLM externo:

    AGENT_PROVIDER=mock

O `mock` é somente para testar a infraestrutura. Para os resultados científicos, depois configuraremos o modelo/versão efetivamente utilizado e registraremos prompt, parâmetros e versão.

## 4. Iniciar a API

    uvicorn app.main:app --reload

Depois abra:

    http://127.0.0.1:8000/docs

## 5. Rodar benchmark

Com a API ligada:

    python benchmark.py

Os resultados brutos serão salvos em `results/benchmark_raw.csv`.

## Importante para o TCC

As Regex deste primeiro ambiente são regras experimentais baseadas nas categorias descritas no artigo. Elas não devem ser apresentadas como as regras originais da empresa sem confirmação.

O dataset inicial contém apenas 20 prompts para validar a infraestrutura. Depois ampliaremos para 100–300 prompts e faremos a rotulagem antes da execução dos experimentos.
