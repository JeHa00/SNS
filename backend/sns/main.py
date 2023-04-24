from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from sns.common.config import settings
from sns.common.session import db
from sns.users.controller import router as users
from sns.posts.controller import router as posts

# from sns.comments.controller import router as comments
# from sns.notification.controller import router as notification

app = FastAPI(title=settings.PROJECT_NAME, openapi_url=f"{settings.API_V1_PREFIX}")
db.init_app(app)

if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origin=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


app.include_router(users, tags=["Users"], prefix=settings.API_V1_PREFIX)
app.include_router(posts, tags=["Posts"], prefix=settings.API_V1_PREFIX)
# app.include_router(comments, tags=['Comments'], prefix=settings.API_V1_PREFIX)
# app.include_router(notification, tags=['Notification'], prefix=settings.API_V1_PREFIX)
