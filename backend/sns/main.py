from fastapi import FastAPI
from fastapi import APIRouter
from starlette.middleware.cors import CORSMiddleware

from sns.common.config import settings
from sns.users.controller import router as users_router
# from sns.posts.controller import router as posts_router
# from sns.comments.controller import router as comments_router
# from sns.notification.controller import router as notification_router

app = FastAPI(title=settings.PROJECT_NAME, openapi_url=f"{settings.API_V1_STR}")

if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origin=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


api_router = APIRouter()
app.include_router(users_router, prefix=settings.API_V1_STR)
# app.include_router(posts_router, prefix=settings.API_V1_STR)
# app.include_router(comments_router, prefix=settings.API_V1_STR)
# app.include_router(notification_router, prefix=settings.API_V1_STR)
