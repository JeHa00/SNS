from fastapi.exceptions import RequestValidationError
from starlette.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from fastapi import FastAPI

from sns.common.config import settings
from sns.common.session import db
from sns.users.controller import router as users
from sns.posts.controller import router as posts
from sns.comments.controller import router as comments
from sns.notifications.controller import router as notifications

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
app.include_router(comments, tags=["Comments"], prefix=settings.API_V1_PREFIX)
app.include_router(notifications, tags=["Notification"], prefix=settings.API_V1_PREFIX)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    return PlainTextResponse(str(exc), status_code=400)
