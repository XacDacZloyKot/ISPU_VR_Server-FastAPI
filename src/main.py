import os

import uvicorn
from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import ValidationException, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from src.auth.base_config import fastapi_users, auth_backend
from src.auth.schemas import UserRead, UserCreate
from src.pages.router import router as router_pages, templates
from src.sensor.router import router as router_sensor

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


# Благодаря этой функции клиент видит ошибки, происходящие на сервере, вместо "Internal server error"
@app.exception_handler(ValidationException)
async def validation_exception_handler(request: Request, exc: ValidationException):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=jsonable_encoder({"detail": exc.errors()}),
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    if exc.status_code == 401:  # Unauthorized
        return templates.TemplateResponse("/auth/loginUser.html", {"request": request, "error": "Please log in to continue"})
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


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
    uvicorn.run(app, port=8000)
