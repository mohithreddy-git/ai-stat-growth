from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import admin, assistant, auth, bootstrap, employee, health, learning, telemetry, users
from app.core.config import get_settings
from app.db.base import Base
from app.db.migrations import run_schema_upgrades
from app.db.session import SessionLocal, engine
from app.services.seed import seed_database
from app.api.routes import demo, studio

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    run_schema_upgrades(engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_database(db)
    finally:
        db.close()
    yield


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="Phase 2 employee competency intelligence API for AI STAT-GROWTH.",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)
app.include_router(health.router, prefix="/api")
app.include_router(auth.router, prefix="/api")
app.include_router(users.router, prefix="/api")
app.include_router(employee.router, prefix="/api")
app.include_router(learning.router, prefix="/api")
app.include_router(bootstrap.router, prefix="/api")
app.include_router(admin.router, prefix="/api")
app.include_router(studio.router, prefix="/api")
app.include_router(demo.router, prefix="/api")
app.include_router(telemetry.router, prefix="/api")
app.include_router(assistant.router, prefix="/api")
