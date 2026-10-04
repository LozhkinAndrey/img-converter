from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from prometheus_fastapi_instrumentator import Instrumentator
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.routers.transform import router as transform_router

APP_VERSION = "1.0.0"

app = FastAPI(title="Image Converter", version=APP_VERSION)

# Автоматические HTTP-метрики: http_requests_total, http_request_duration_seconds
Instrumentator().instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(status_code=exc.status_code, content={"error": exc.detail})


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(status_code=400, content={"error": f"Некорректный запрос: {exc.errors()[0]['msg']}"})


@app.get("/api/health")
async def health():
    return {"status": "ok", "version": APP_VERSION}


app.include_router(transform_router)

# Статику монтируем последним, чтобы /api/* имели приоритет
app.mount("/", StaticFiles(directory=Path(__file__).resolve().parent.parent / "static", html=True), name="static")
