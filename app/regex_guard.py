import re
from dataclasses import dataclass


@dataclass
class RegexResult:
    approved: bool
    reasons: list[str]
    matched_rules: list[str]
    sanitized_prompt: str


# ============================================================
# REGRAS EXPERIMENTAIS
# ============================================================
#
# O sistema foi definido como READ-ONLY.
#
# O usuário pode:
#   - visualizar veículos;
#   - consultar veículos;
#   - visualizar posições;
#   - consultar histórico;
#   - visualizar relatórios;
#   - visualizar dashboards.
#
# O usuário NÃO pode:
#   - alterar;
#   - editar;
#   - modificar;
#   - atualizar;
#   - apagar;
#   - excluir;
#   - remover;
#   - inserir;
#   - adicionar;
#   - trocar informações;
#   - ativar/desativar dispositivos;
#   - executar SQL de escrita;
#   - executar código ou comandos.
#
# ============================================================


RULES = {

    # --------------------------------------------------------
    # SQL / COMANDOS DE ESCRITA
    # --------------------------------------------------------

    "sql_destructive": re.compile(
        r"\b(delete|drop|truncate|update|insert|alter)\b",
        re.IGNORECASE,
    ),


    # --------------------------------------------------------
    # OPERAÇÕES DE ESCRITA EM LINGUAGEM NATURAL
    # --------------------------------------------------------
    #
    # Esta é a principal regra adicionada para o modo
    # somente leitura.
    #
    # Os padrões utilizam raízes para capturar variações:
    #
    # alterar / altere / alterando
    # modificar / modifique / modificando
    # excluir / exclua / excluindo
    #
    # --------------------------------------------------------

    "write_operation": re.compile(
        r"""
        \b(
            alter\w* |
            modific\w* |
            edit\w* |
            atualiz\w* |
            mud\w* |
            troqu\w* |
            apag\w* |
            exclu\w* |
            remov\w* |
            elimin\w* |
            destru\w* |
            inser\w* |
            adicion\w* |
            desativ\w* |
            ativ\w* |
            cadast\w*
        )\b
        """,
        re.IGNORECASE | re.VERBOSE,
    ),


    # --------------------------------------------------------
    # CREDENCIAIS / SEGREDOS
    # --------------------------------------------------------

    "credentials": re.compile(
        r"""
        \b(
            password |
            senha |
            token |
            api[-_ ]?key |
            credential |
            credencial |
            secret |
            segredo
        )\b
        """,
        re.IGNORECASE | re.VERBOSE,
    ),


    # --------------------------------------------------------
    # BANCO / REGISTROS SENSÍVEIS
    # --------------------------------------------------------

    "database_sensitive": re.compile(
        r"""
        \b(
            database |
            banco\s+de\s+dados |
            tabela |
            table |
            registro |
            registros |
            record |
            records
        )\b
        """,
        re.IGNORECASE | re.VERBOSE,
    ),


    # --------------------------------------------------------
    # LINGUAGEM DESTRUTIVA
    # --------------------------------------------------------

    "destructive_natural_language": re.compile(
        r"""
        \b(
            apague |
            apagar |
            apaga |
            exclua |
            excluir |
            exclua |
            remova |
            remover |
            remove |
            elimine |
            eliminar |
            destrua |
            destruir |
            destrua
        )\b
        """,
        re.IGNORECASE | re.VERBOSE,
    ),


    # --------------------------------------------------------
    # EXECUÇÃO DE CÓDIGO / COMANDOS
    # --------------------------------------------------------

    "code_execution": re.compile(
        r"""
        \b(
            exec |
            execute |
            executar |
            shell |
            powershell |
            bash |
            python |
            script |
            código |
            codigo
        )\b
        """,
        re.IGNORECASE | re.VERBOSE,
    ),
}


# ============================================================
# VALIDAÇÃO
# ============================================================

def validate_regex(prompt: str) -> RegexResult:

    matched = []
    reasons = []


    # --------------------------------------------------------
    # Verificar todas as regras
    # --------------------------------------------------------

    for name, pattern in RULES.items():

        if pattern.search(prompt):
            matched.append(name)


    # --------------------------------------------------------
    # Motivo: SQL destrutivo
    # --------------------------------------------------------

    if "sql_destructive" in matched:

        reasons.append(
            "Padrão associado a comando SQL de escrita "
            "ou potencialmente destrutivo."
        )


    # --------------------------------------------------------
    # Motivo: operação de escrita
    # --------------------------------------------------------

    if "write_operation" in matched:

        reasons.append(
            "Operação de escrita não permitida. "
            "O sistema é somente leitura."
        )


    # --------------------------------------------------------
    # Motivo: credenciais
    # --------------------------------------------------------

    if "credentials" in matched:

        reasons.append(
            "Referência potencial a credenciais ou segredo."
        )


    # --------------------------------------------------------
    # Motivo: operação destrutiva
    # --------------------------------------------------------

    if "destructive_natural_language" in matched:

        reasons.append(
            "Linguagem associada a ação destrutiva."
        )


    # --------------------------------------------------------
    # Motivo: execução de código
    # --------------------------------------------------------

    if "code_execution" in matched:

        reasons.append(
            "Referência potencial a execução de código "
            "ou script."
        )


    # --------------------------------------------------------
    # Motivo: banco de dados
    # --------------------------------------------------------

    if "database_sensitive" in matched:

        reasons.append(
            "Referência a banco, tabela ou registros."
        )


    # --------------------------------------------------------
    # DECISÃO
    # --------------------------------------------------------
    #
    # Se qualquer regra for acionada:
    #
    # approved = False
    #
    # Portanto, o Regex funciona como primeira camada
    # de bloqueio.
    # --------------------------------------------------------

    approved = len(matched) == 0


    # --------------------------------------------------------
    # SANITIZAÇÃO
    # --------------------------------------------------------

    sanitized = prompt

    sensitive_tokens = [
        "password",
        "senha",
        "token",
        "api key",
        "api-key",
        "credential",
        "credencial",
        "secret",
        "segredo",
    ]

    for token in sensitive_tokens:

        sanitized = re.sub(
            re.escape(token),
            "[REDACTED]",
            sanitized,
            flags=re.IGNORECASE,
        )


    # --------------------------------------------------------
    # RESULTADO
    # --------------------------------------------------------

    return RegexResult(
        approved=approved,
        reasons=reasons,
        matched_rules=matched,
        sanitized_prompt=sanitized,
    )