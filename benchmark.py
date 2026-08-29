"""
Benchmark experimental para comparar:
1) Regex
2) Agente
3) Regex + Agente

Lê data/prompts.csv e executa TODOS os prompts nas três configurações.
Os resultados são salvos em results/benchmark_raw.csv.

Esperado no CSV:
id, category, expected, prompt, subtype, notes

A API deve estar disponível em:
http://127.0.0.1:8000
"""

import csv
import json
import time
from pathlib import Path

import requests
import os


# Configuração do agente
AGENT_PROVIDER = os.getenv("AGENT_PROVIDER", "mock")


# Diretórios
DATASET_PATH = Path("data/prompts.csv")
RESULTS_DIR = Path("results")

# Cria a pasta results caso não exista
RESULTS_DIR.mkdir(exist_ok=True)


# Nome do arquivo de saída conforme o agente
if AGENT_PROVIDER == "ollama":
    output_name = "benchmark_llm.csv"
else:
    output_name = "benchmark_mock.csv"

OUTPUT_PATH = RESULTS_DIR / output_name


BASE_URL = "http://127.0.0.1:8000"

ENDPOINTS = {
    "regex": "/validate/regex",
    "agent": "/validate/agent",
    "combined": "/validate/combined",
}

def load_dataset():
    if not DATASET_PATH.exists():
        raise FileNotFoundError(
            f"Dataset não encontrado: {DATASET_PATH.resolve()}"
        )

    with DATASET_PATH.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))

    required = {"id", "category", "expected", "prompt"}
    missing = required - set(rows[0].keys()) if rows else required

    if missing:
        raise ValueError(
            f"Colunas obrigatórias ausentes no dataset: {sorted(missing)}"
        )

    return rows


def call_api(mode, prompt):
    url = BASE_URL + ENDPOINTS[mode]

    start = time.perf_counter()

    response = requests.post(
        url,
        json={"prompt": prompt},
        timeout=60,
    )

    elapsed_ms = (time.perf_counter() - start) * 1000

    response.raise_for_status()

    data = response.json()

    # Usa a latência reportada pela própria API quando disponível.
    api_latency = data.get("latency_ms")

    return data, elapsed_ms, api_latency


def is_correct(expected, approved):
    expected_bool = expected.lower() == "approved"
    return expected_bool == bool(approved)


def main():
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    dataset = load_dataset()

    print("=" * 70)
    print("BENCHMARK DE GUARDRAILS")
    print("=" * 70)
    print(f"Dataset: {DATASET_PATH.resolve()}")
    print(f"Prompts carregados: {len(dataset)}")
    print(f"Configurações: {len(ENDPOINTS)}")
    print(f"Total esperado de avaliações: {len(dataset) * len(ENDPOINTS)}")
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
                correct = is_correct(row["expected"], approved)

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
                    "sanitized_prompt": data.get("sanitized_prompt"),
                    "agent_model": data.get("agent_model"),
                    "latency_ms_api": api_latency,
                    "latency_ms_client": round(client_latency, 4),
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

            results.append(result)

            if completed % 20 == 0 or completed == total:
                print(f"  Progresso: {completed}/{total}")

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
        newline="",
    ) as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    print("\n" + "=" * 70)
    print("BENCHMARK FINALIZADO")
    print("=" * 70)
    print(f"Resultados: {OUTPUT_PATH.resolve()}")
    print(f"Linhas gravadas: {len(results)}")
    print(f"Esperado: {total}")

    errors = sum(1 for r in results if r["error"])
    correct = sum(1 for r in results if r["correct"])

    print(f"Testes com erro: {errors}")
    print(f"Acertos: {correct}/{total}")
    print("=" * 70)


if __name__ == "__main__":
    main()
