from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from backend.app.core.config import get_settings
from backend.app.repositories.dynamodb import DynamoDbSautiRelayRepository
from backend.app.repositories.memory import InMemorySautiRelayRepository, LocalJsonSautiRelayRepository
from backend.app.routers import auth, clusters, dashboard, escalations, reports, status
from backend.app.services.auth import AuthService
from backend.app.services.demo_seed import run_demo_seed
from backend.app.services.s3_vectors import S3VectorStore, validate_s3_vectors_region
from backend.app.services.workflow import WorkflowService
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    if settings.repository_backend == "dynamodb":
        if not settings.dynamodb_table_name:
            raise RuntimeError("DYNAMODB_TABLE_NAME is required when REPOSITORY_BACKEND=dynamodb.")
        if not settings.s3_vector_bucket_name or not settings.s3_vector_index_name:
            raise RuntimeError(
                "S3_VECTOR_BUCKET_NAME and S3_VECTOR_INDEX_NAME are required when REPOSITORY_BACKEND=dynamodb."
            )
        validate_s3_vectors_region(settings.aws_region)
        repository = DynamoDbSautiRelayRepository(
            table_name=settings.dynamodb_table_name,
            region_name=settings.aws_region,
            vector_store=S3VectorStore(
                vector_bucket_name=settings.s3_vector_bucket_name,
                index_name=settings.s3_vector_index_name,
                region_name=settings.aws_region,
            ),
        )
    elif settings.environment == "test":
        repository = InMemorySautiRelayRepository()
    else:
        repository = LocalJsonSautiRelayRepository(settings.local_data_dir)
    app.state.repository = repository
    app.state.auth_service = AuthService(settings)
    app.state.workflow_service = WorkflowService(repository)
    if settings.demo_seed_enabled and not getattr(app.state, "demo_seed_completed", False):
        await run_demo_seed(repository, app.state.workflow_service, settings)
        app.state.demo_seed_completed = True
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
