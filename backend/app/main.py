from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from backend.app.core.config import get_settings
from backend.app.repositories.memory import InMemorySautiRelayRepository
from backend.app.routers import auth, clusters, dashboard, escalations, reports, status
from backend.app.services.auth import AuthService
from backend.app.services.workflow import WorkflowService
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    repository = InMemorySautiRelayRepository()
    app.state.repository = repository
    app.state.auth_service = AuthService(settings)
    app.state.workflow_service = WorkflowService(repository)
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="SautiRelay API",
        version="0.1.0",
        description="API for anonymous SautiRelay signal reporting and mediator escalation.",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.cors_allow_origins),
        allow_credentials=settings.cors_allow_credentials,
        allow_methods=list(settings.cors_allow_methods),
        allow_headers=list(settings.cors_allow_headers),
    )
    app.include_router(status.router)
    app.include_router(auth.router)
    app.include_router(reports.router)
    app.include_router(clusters.router)
    app.include_router(escalations.router)
    app.include_router(dashboard.router)
    return app


app = create_app()
