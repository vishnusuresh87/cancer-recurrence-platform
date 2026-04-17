from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1 import models
from app.config import settings

app = FastAPI(
    title="Model Management Service",
    description="Manage ML model versions, deployments, and A/B testing",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(models.router, prefix="/api/v1/models", tags=["models"])


@app.on_event("startup")
async def startup_event():
    print(f"🚀 Starting {settings.service_name}")
    print(f"📁 Model storage: {settings.model_storage_path}")
    print("✅ Service ready")


@app.get("/")
async def root():
    return {
        "service": settings.service_name,
        "status": "running",
        "docs": "/docs"
    }
    
    