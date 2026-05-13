from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import inspect, text
from app.api.v1.api import api_router
from app.core.config import settings
from app.core.database import engine, Base
import app.models as models  # Import models to register them with Base.metadata
from contextlib import asynccontextmanager


def ensure_campaign_schema_updates() -> None:
    inspector = inspect(engine)
    if "campaigns" not in inspector.get_table_names():
        return

    existing_columns = {column["name"] for column in inspector.get_columns("campaigns")}
    column_updates = {
        "scheduled_for": "ALTER TABLE campaigns ADD COLUMN scheduled_for TIMESTAMPTZ NULL",
        "daily_send_limit": "ALTER TABLE campaigns ADD COLUMN daily_send_limit INTEGER NOT NULL DEFAULT 50",
        "send_window_start_hour": "ALTER TABLE campaigns ADD COLUMN send_window_start_hour INTEGER NOT NULL DEFAULT 9",
        "send_window_end_hour": "ALTER TABLE campaigns ADD COLUMN send_window_end_hour INTEGER NOT NULL DEFAULT 17",
    }

    missing_updates = [
        statement for column_name, statement in column_updates.items()
        if column_name not in existing_columns
    ]

    if not missing_updates:
        return

    with engine.begin() as connection:
        for statement in missing_updates:
            connection.execute(text(statement))

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables on startup (Safe mode)
    try:
        print("DEBUG: Attempting to create tables...")
        Base.metadata.create_all(bind=engine)
        ensure_campaign_schema_updates()
        print("DEBUG: Tables created successfully!")
    except Exception as e:
        print(f"ERROR: Database connection failed during startup: {str(e)}")
        print("DEBUG: Continuing startup anyway to allow log access...")
    yield

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

# Set up CORS
if settings.BACKEND_CORS_ORIGINS:
    allow_origins = [str(origin) for origin in settings.BACKEND_CORS_ORIGINS]
    allow_credentials = True
    
    if "*" in allow_origins:
        allow_credentials = False
        
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allow_origins,
        allow_credentials=allow_credentials,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
