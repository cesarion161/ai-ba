from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.middleware import ErrorHandlerMiddleware, RequestIdMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.APP_NAME,
        lifespan=lifespan,
    )

    # Middleware
    app.add_middleware(RequestIdMiddleware)
    app.add_middleware(ErrorHandlerMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Routes
    from app.api.routes import (
        artifacts,
        auth,
        chat,
        config,
        document_types,
        graph,
        graph_edit,
        health,
        nodes,
        projects,
        stream,
    )

    app.include_router(health.router)
    app.include_router(auth.router)
    app.include_router(projects.router)
    app.include_router(graph.router)
    app.include_router(graph_edit.router)
    app.include_router(nodes.router)
    app.include_router(stream.router)
    app.include_router(artifacts.router)
    app.include_router(config.router)
    app.include_router(document_types.router)
    app.include_router(chat.router)

    return app


app = create_app()
