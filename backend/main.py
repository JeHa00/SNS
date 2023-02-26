from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from core.config import settings
from apis.api_v1.api import api_router

app = FastAPI(title=settings.PROJECT_NAME, openapi_url=f"{settings.API_V1_STR}")

if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origin=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(api_router, prefix=settings.API_V1_STR)