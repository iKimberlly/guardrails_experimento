import time
from fastapi import FastAPI, HTTPException

from .models import ValidationRequest, ValidationResponse
from .regex_guard import validate_regex
from .agent import classify

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

app = FastAPI(
    title="Guardrails Experimental Environment",
    version="0.1.0",
)

BASE_DIR = Path(__file__).resolve().parent.parent

app.mount(
    "/static",
    StaticFiles(directory=BASE_DIR / "static"),
    name="static"
)

templates = Jinja2Templates(
    directory=BASE_DIR / "templates"
)

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {"request": request}
    )

def run_regex(prompt: str):
    start = time.perf_counter()
    result = validate_regex(prompt)
    latency = (time.perf_counter() - start) * 1000

    return ValidationResponse(
        approved=result.approved,
        mode="regex",
        layer="regex",
        reasons=result.reasons,
        sanitized_prompt=result.sanitized_prompt,
        matched_rules=result.matched_rules,
        latency_ms=round(latency, 3),
    )

def run_agent(prompt: str):
    start = time.perf_counter()
    result, model = classify(prompt)
    latency = (time.perf_counter() - start) * 1000

    return ValidationResponse(
        approved=result["approved"],
        mode="agent",
        layer="agent",
        reasons=result["reasons"],
        sanitized_prompt=result.get("sanitized_prompt", prompt),
        matched_rules=[],
        latency_ms=round(latency, 3),
        agent_model=model,
    )

def run_combined(prompt: str):
    start = time.perf_counter()

    regex = validate_regex(prompt)
    if not regex.approved:
        latency = (time.perf_counter() - start) * 1000
        return ValidationResponse(
            approved=False,
            mode="combined",
            layer="regex",
            reasons=regex.reasons,
            sanitized_prompt=regex.sanitized_prompt,
            matched_rules=regex.matched_rules,
            latency_ms=round(latency, 3),
            agent_model=None,
        )

    agent_result, model = classify(regex.sanitized_prompt)
    latency = (time.perf_counter() - start) * 1000

    return ValidationResponse(
        approved=agent_result["approved"],
        mode="combined",
        layer="agent",
        reasons=agent_result["reasons"],
        sanitized_prompt=agent_result.get("sanitized_prompt", regex.sanitized_prompt),
        matched_rules=[],
        latency_ms=round(latency, 3),
        agent_model=model,
    )

@app.get("/")
def root():
    return {"status": "ok", "message": "Ambiente experimental de guardrails ativo."}

@app.post("/validate/regex", response_model=ValidationResponse)
def validate_regex_endpoint(request: ValidationRequest):
    return run_regex(request.prompt)

@app.post("/validate/agent", response_model=ValidationResponse)
def validate_agent_endpoint(request: ValidationRequest):
    try:
        return run_agent(request.prompt)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

@app.post("/validate/combined", response_model=ValidationResponse)
def validate_combined_endpoint(request: ValidationRequest):
    try:
        return run_combined(request.prompt)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
