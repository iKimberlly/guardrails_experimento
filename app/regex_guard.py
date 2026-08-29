import re
from dataclasses import dataclass

@dataclass
class RegexResult:
    approved: bool
    reasons: list[str]
    matched_rules: list[str]
    sanitized_prompt: str

# Regras EXPERIMENTAIS baseadas nas categorias descritas no artigo.
# Quando recuperarmos as regras originais do projeto, elas poderão substituir estas.
RULES = {
    "sql_destructive": re.compile(
        r"\b(delete|drop|truncate|update|insert|alter)\b", re.IGNORECASE
    ),
    "credentials": re.compile(
        r"\b(password|senha|token|api[-_ ]?key|credential|credencial|secret)\b",
        re.IGNORECASE,
    ),
    "database_sensitive": re.compile(
        r"\b(database|banco de dados|tabela|table|registro|records?)\b",
        re.IGNORECASE,
    ),
    "destructive_natural_language": re.compile(
        r"\b(apague|apagar|exclua|excluir|remova|remover|elimine|eliminar|destrua|destruir)\b",
        re.IGNORECASE,
    ),
    "code_execution": re.compile(
        r"\b(exec|execute|executar|shell|powershell|bash|python|script|c[oó]digo)\b",
        re.IGNORECASE,
    ),
}

def validate_regex(prompt: str) -> RegexResult:
    matched = []
    reasons = []

    for name, pattern in RULES.items():
        if pattern.search(prompt):
            matched.append(name)

    if "sql_destructive" in matched:
        reasons.append("Padrão associado a comando SQL potencialmente destrutivo.")
    if "credentials" in matched:
        reasons.append("Referência potencial a credenciais ou segredo.")
    if "destructive_natural_language" in matched:
        reasons.append("Linguagem associada a ação destrutiva.")
    if "code_execution" in matched:
        reasons.append("Referência potencial a execução de código ou script.")
    if "database_sensitive" in matched:
        reasons.append("Referência a banco, tabela ou registros.")

    approved = len(matched) == 0

    sanitized = prompt
    for token in ["password", "senha", "token", "api key", "api-key", "credential", "credencial"]:
        sanitized = re.sub(re.escape(token), "[REDACTED]", sanitized, flags=re.IGNORECASE)

    return RegexResult(
        approved=approved,
        reasons=reasons,
        matched_rules=matched,
        sanitized_prompt=sanitized,
    )
