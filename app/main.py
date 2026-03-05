from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

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

    # Routes
    from app.api.routes import artifacts, auth, graph, health, nodes, projects, stream

    app.include_router(health.router)
    app.include_router(auth.router)
    app.include_router(projects.router)
    app.include_router(graph.router)
    app.include_router(nodes.router)
    app.include_router(stream.router)
    app.include_router(artifacts.router)

    return app


app = create_app()
