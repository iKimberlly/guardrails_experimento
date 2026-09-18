import time
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request, Header
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .models import ValidationRequest, ValidationResponse
from .regex_guard import validate_regex
from .agent import classify

# IMPORTANTE:
# database.py está na raiz do projeto
from .database import (
    get_connection,
    get_user_vehicles,
    get_user_vehicle,
    get_user_positions,
)


app = FastAPI(
    title="Guardrails Experimental Environment",
    version="0.2.0"
)

BASE_DIR = Path(__file__).resolve().parent.parent

# Arquivos estáticos
app.mount(
    "/static",
    StaticFiles(directory=BASE_DIR / "static"),
    name="static"
)

# Templates
templates = Jinja2Templates(
    directory=BASE_DIR / "templates"
)


# ============================================================
# INTERFACE
# ============================================================

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {"request": request}
    )


# ============================================================
# USUÁRIOS DE TESTE
# ============================================================

@app.get("/users")
def get_users():
    """
    Retorna os usuários disponíveis para o experimento.
    """

    conn = get_connection()

    rows = conn.execute("""
        SELECT id, nome, email
        FROM usuarios
        ORDER BY id
    """).fetchall()

    conn.close()

    return {
        "users": [dict(row) for row in rows]
    }


# ============================================================
# CONSULTA SEGURA DOS VEÍCULOS
# ============================================================

@app.get("/my/vehicles")
def my_vehicles(
    x_user_id: int = Header(..., alias="X-User-ID")
):
    """
    Retorna somente os veículos pertencentes
    ao usuário atualmente selecionado.
    """

    # Verifica se o usuário existe
    conn = get_connection()

    user = conn.execute("""
        SELECT id, nome, email
        FROM usuarios
        WHERE id = ?
    """, (x_user_id,)).fetchone()

    conn.close()

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Usuário de teste inválido."
        )

    vehicles = get_user_vehicles(x_user_id)

    return {
        "usuario": dict(user),
        "total": len(vehicles),
        "veiculos": vehicles
    }


# ============================================================
# CONSULTA DE UM VEÍCULO ESPECÍFICO
# ============================================================

@app.get("/my/vehicles/{veiculo_id}")
def my_vehicle(
    veiculo_id: int,
    x_user_id: int = Header(..., alias="X-User-ID")
):
    """
    Retorna um veículo somente se ele pertencer
    ao usuário selecionado.
    """

    vehicle = get_user_vehicle(
        x_user_id,
        veiculo_id
    )

    if not vehicle:
        raise HTTPException(
            status_code=404,
            detail="Veículo não encontrado."
        )

    return vehicle


# ============================================================
# POSIÇÕES DE UM VEÍCULO
# ============================================================

@app.get("/my/vehicles/{veiculo_id}/positions")
def my_vehicle_positions(
    veiculo_id: int,
    x_user_id: int = Header(..., alias="X-User-ID")
):
    """
    Retorna posições somente de veículos
    pertencentes ao usuário selecionado.
    """

    # Primeiro verifica a propriedade
    vehicle = get_user_vehicle(
        x_user_id,
        veiculo_id
    )

    if not vehicle:
        raise HTTPException(
            status_code=404,
            detail="Veículo não encontrado."
        )

    positions = get_user_positions(
        x_user_id,
        veiculo_id
    )

    return {
        "veiculo_id": veiculo_id,
        "total": len(positions),
        "posicoes": positions
    }


# ============================================================
# GUARDRAIL — REGEX
# ============================================================

def run_regex(prompt: str):
    start = time.perf_counter()

    result = validate_regex(prompt)

    latency = (time.perf_counter() - start) * 1000

    return {
        **result,
        "latency_ms": round(latency, 2),
        "mode": "regex"
    }


@app.post(
    "/validate/regex",
    response_model=ValidationResponse
)
def validate_regex_endpoint(
    request: ValidationRequest
):
    return run_regex(request.prompt)


# ============================================================
# GUARDRAIL — AGENT
# ============================================================

def run_agent(prompt: str):
    start = time.perf_counter()

    result = classify(prompt)

    latency = (time.perf_counter() - start) * 1000

    return {
        **result,
        "latency_ms": round(latency, 2),
        "mode": "agent"
    }


@app.post(
    "/validate/agent",
    response_model=ValidationResponse
)
def validate_agent_endpoint(
    request: ValidationRequest
):
    return run_agent(request.prompt)


# ============================================================
# GUARDRAIL — COMBINED
# ============================================================

def run_combined(prompt: str):
    start = time.perf_counter()

    regex_result = validate_regex(prompt)

    # Regex bloqueou
    if not regex_result["approved"]:
        latency = (time.perf_counter() - start) * 1000

        return {
            **regex_result,
            "latency_ms": round(latency, 2),
            "mode": "combined",
            "layer": "regex"
        }

    # Regex permitiu → envia para agente
    agent_result = classify(prompt)

    latency = (time.perf_counter() - start) * 1000

    return {
        **agent_result,
        "latency_ms": round(latency, 2),
        "mode": "combined",
        "layer": "agent"
    }


@app.post(
    "/validate/combined",
    response_model=ValidationResponse
)
def validate_combined_endpoint(
    request: ValidationRequest
):
    return run_combined(request.prompt)