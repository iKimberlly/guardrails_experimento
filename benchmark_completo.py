import csv
import json
import time
import os
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()

# ============================================================
# CONFIGURACAO
# ============================================================

AGENT_PROVIDER = os.getenv("AGENT_PROVIDER", "mock").lower()

DATASET_PATH = Path("data/prompts.csv")
RESULTS_DIR = Path("results")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# None = benchmark completo: 240 prompts x 3 modos = 720 testes
TEST_LIMIT = None

# O Qwen3 esta rodando localmente em CPU; 120s evita timeouts prematuros.
REQUEST_TIMEOUT = 60

if AGENT_PROVIDER == "ollama":
    OUTPUT_PATH = RESULTS_DIR / "benchmark_llm.csv"
else:
    OUTPUT_PATH = RESULTS_DIR / "benchmark_mock.csv"

BASE_URL = os.getenv(
    "BENCHMARK_BASE_URL",
    "http://127.0.0.1:8000"
).rstrip("/")

ENDPOINTS = {
    "regex": "/validate/regex",
    "agent": "/validate/agent",
    "combined": "/validate/combined",
}


# ============================================================
# DATASET
# ============================================================

def load_dataset():
    if not DATASET_PATH.exists():
        raise FileNotFoundError(
            f"Dataset nao encontrado: {DATASET_PATH.resolve()}"
        )

    with DATASET_PATH.open(
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as f:
        rows = list(csv.DictReader(f))

    required = {"id", "category", "expected", "prompt"}
    missing = required - set(rows[0].keys()) if rows else required

    if missing:
        raise ValueError(
            f"Colunas obrigatorias ausentes no dataset: {sorted(missing)}"
        )

    return rows


# ============================================================
# API
# ============================================================

def call_api(mode, prompt):
    url = BASE_URL + ENDPOINTS[mode]

    start = time.perf_counter()

    response = requests.post(
        url,
        json={"prompt": prompt},
        timeout=REQUEST_TIMEOUT,
    )

    elapsed_ms = (time.perf_counter() - start) * 1000

    response.raise_for_status()

    data = response.json()

    api_latency = data.get("latency_ms")

    return data, elapsed_ms, api_latency


# ============================================================
# AVALIACAO
# ============================================================

def is_correct(expected, approved):
    expected_bool = expected.lower() == "approved"
    return expected_bool == bool(approved)


# ============================================================
# BENCHMARK COMPLETO
# ============================================================

def main():
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    dataset = load_dataset()

    if TEST_LIMIT is not None:
        dataset = dataset[:TEST_LIMIT]

    print("=" * 70)
    print("BENCHMARK DE GUARDRAILS")
    print("=" * 70)
    print(f"Dataset: {DATASET_PATH.resolve()}")
    print(f"Provider: {AGENT_PROVIDER}")
    print(f"Prompts carregados: {len(dataset)}")
    print(f"Configuracoes: {len(ENDPOINTS)}")
    print(
        f"Total esperado de avaliacoes: "
        f"{len(dataset) * len(ENDPOINTS)}"
    )
    print(f"Timeout por requisicao: {REQUEST_TIMEOUT}s")
    print(f"Saida: {OUTPUT_PATH.resolve()}")
    print("=" * 70)

    contagem = {}

    for row in dataset:
        categoria = row["category"]
        contagem[categoria] = contagem.get(categoria, 0) + 1

    print("\nDistribuicao do dataset:")

    for categoria, quantidade in sorted(contagem.items()):
        print(f"  {categoria}: {quantidade}")

    print("=" * 70)

    results = []

    total = len(dataset) * len(ENDPOINTS)
    completed = 0

    for mode, endpoint in ENDPOINTS.items():
        print(f"\nExecutando: {mode} ({endpoint})")

        for row in dataset:
            completed += 1

            try:
                data, client_latency, api_latency = call_api(
                    mode,
                    row["prompt"],
                )

                approved = bool(data.get("approved", False))

                correct = is_correct(
                    row["expected"],
                    approved
                )

                result = {
                    "id": row["id"],
                    "category": row["category"],
                    "expected": row["expected"],
                    "prompt": row["prompt"],
                    "subtype": row.get("subtype", ""),
                    "notes": row.get("notes", ""),
                    "mode": mode,
                    "approved": approved,
                    "correct": correct,
                    "layer": data.get("layer"),
                    "reasons": json.dumps(
                        data.get("reasons", []),
                        ensure_ascii=False,
                    ),
                    "matched_rules": json.dumps(
                        data.get("matched_rules", []),
                        ensure_ascii=False,
                    ),
                    "sanitized_prompt": data.get(
                        "sanitized_prompt"
                    ),
                    "agent_model": data.get(
                        "agent_model"
                    ),
                    "latency_ms_api": api_latency,
                    "latency_ms_client": round(
                        client_latency,
                        4
                    ),
                    "error": "",
                }

            except Exception as exc:
                result = {
                    "id": row["id"],
                    "category": row["category"],
                    "expected": row["expected"],
                    "prompt": row["prompt"],
                    "subtype": row.get("subtype", ""),
                    "notes": row.get("notes", ""),
                    "mode": mode,
                    "approved": "",
                    "correct": False,
                    "layer": "",
                    "reasons": "",
                    "matched_rules": "",
                    "sanitized_prompt": "",
                    "agent_model": "",
                    "latency_ms_api": "",
                    "latency_ms_client": "",
                    "error": repr(exc),
                }

                print(
                    f"  ERRO em {mode} "
                    f"id={row['id']}: {repr(exc)}"
                )

            results.append(result)

            if completed % 10 == 0 or completed == total:
                print(
                    f"  Progresso: {completed}/{total} "
                    f"({completed / total * 100:.1f}%)"
                )

    # ========================================================
    # SALVAR RESULTADOS
    # ========================================================

    fieldnames = [
        "id",
        "category",
        "expected",
        "prompt",
        "subtype",
        "notes",
        "mode",
        "approved",
        "correct",
        "layer",
        "reasons",
        "matched_rules",
        "sanitized_prompt",
        "agent_model",
        "latency_ms_api",
        "latency_ms_client",
        "error",
    ]

    with OUTPUT_PATH.open(
        "w",
        encoding="utf-8-sig",
        newline=""
    ) as f:
        writer = csv.DictWriter(
            f,
            fieldnames=fieldnames
        )
        writer.writeheader()
        writer.writerows(results)

    errors = sum(1 for r in results if r["error"])
    correct = sum(1 for r in results if r["correct"])

    print("\n" + "=" * 70)
    print("BENCHMARK FINALIZADO")
    print("=" * 70)
    print(f"Resultados: {OUTPUT_PATH.resolve()}")
    print(f"Linhas gravadas: {len(results)}")
    print(f"Esperado: {total}")
    print(f"Testes com erro: {errors}")
    print(f"Acertos: {correct}/{total}")

    if total:
        print(
            f"Acuracia geral: "
            f"{correct / total * 100:.2f}%"
        )

    print("=" * 70)


if __name__ == "__main__":
    main()
