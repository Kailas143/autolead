from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.api import api_router
from app.core.config import settings
from app.core.database import engine, Base
import app.models as models  # Import models to register them with Base.metadata
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables on startup (Safe mode)
    try:
        print("DEBUG: Attempting to create tables...")
        Base.metadata.create_all(bind=engine)
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