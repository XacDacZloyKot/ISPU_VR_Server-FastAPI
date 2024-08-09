import os
import sys

import uvicorn
from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import ValidationException, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse

from src.auth.base_config import fastapi_users, auth_backend
from src.auth.schemas import UserRead, UserCreate
from src.pages.router import router as router_pages, templates
from src.sensor.router import router as router_sensor

DEBUG = False

app = FastAPI(
    title="ISPU App"
)

# Определяем базовый каталог
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Определяем путь к статическим файлам
if os.path.exists(os.path.join(BASE_DIR, "src", "static")):
    STATIC_DIR = os.path.join(BASE_DIR, "src", "static")
else:
    # В случае, если проект запущен из собранной версии, учитываем путь после сборки
    STATIC_DIR = os.path.join(BASE_DIR, "_internal", "static\\")

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS", "DELETE", "PATCH", "PUT"],
    allow_headers=["Content-Type", "Set-Cookie", "Access-Control-Allow-Headers", "Access-Control-Allow-Origin",
                   "Authorization"],
)


@app.exception_handler(ValidationException)
async def validation_exception_handler(request: Request, exc: ValidationException):
    if DEBUG:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=jsonable_encoder({"detail": exc.errors()}),
        )
    return templates.TemplateResponse("/support_pages/error.html", {"request": request, "error": "Validation error occurred."})


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    if DEBUG:
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
        )
    if exc.status_code == 401:
        return templates.TemplateResponse("/auth/loginUser.html", {"request": request, "error": "Please log in to continue"})
    if exc.status_code == 404:
        return templates.TemplateResponse("/auth/loginUser.html",
                                          {"request": request, "error": "Page not found."})
    return templates.TemplateResponse("/support_pages/error.html", {"request": request, "error": str(exc.detail)})


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    print(f"An error occurred: {exc}")
    if DEBUG:
        return templates.TemplateResponse("/support_pages/error.html", {"request": request, "error": str(exc)})
    return templates.TemplateResponse("/support_pages/error.html", {"request": request, "error": "An unexpected error occurred."})


@app.exception_handler(404)
async def not_found_exception_handler(request: Request, exc: HTTPException):
    return templates.TemplateResponse("/auth/loginUser.html",
                                      {"request": request, "error": "Page not found."})


@app.exception_handler(401)
async def not_found_exception_handler(request: Request, exc: HTTPException):
    return templates.TemplateResponse("/auth/loginUser.html",
                                      {"request": request, "error": "Please log in to continue"})


app.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix="/auth/jwt",
    tags=["auth"],
)

app.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/auth",
    tags=["auth"],
)

app.include_router(router_sensor)
app.include_router(router_pages)

if __name__ == "__main__":
    try:
        log_level = "debug" if DEBUG else "critical"
        uvicorn.run(app, port=8000, host="0.0.0.0", log_level=log_level)
    except Exception as e:
        print("Error occurred:", e)
        sys.exit(1)
    finally:
        print("Press Enter to exit...")
        input()