from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1 import auth
from app.config import settings

app = FastAPI(
    title="Cancer Recurrence Auth Service",
    description="User authentication and authorization service",
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
app.include_router(auth.router, prefix="/api/v1/auth", tags=["authentication"])


@app.on_event("startup")
async def startup_event():
    print(f"🚀 Starting {settings.service_name}")
    print(f"🔐 JWT expiry: {settings.jwt_access_token_expire_minutes} minutes")
    print("✅ Service ready")


@app.get("/")
async def root():
    return {
        "service": settings.service_name,
        "status": "running",
        "docs": "/docs"
    }


    