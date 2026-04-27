from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1 import predict
from app.config import settings

app = FastAPI(
    title="Cancer Recurrence Prediction Service",
    description="ML inference service for cancer recurrence risk prediction",
    version="1.0.0"
)

# CORS (for local frontend development)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(predict.router, prefix="/api/v1/predict", tags=["predictions"])

@app.on_event("startup")
async def startup_event():
    """Load model on startup"""
    from app.inference.model_loader import model_loader
    print(f"🚀 Starting {settings.service_name}")
    print(f"📊 Model version: {settings.model_version}")
    model_loader.load_model()
    print("✅ Service ready")

@app.on_event("shutdown")
async def shutdown_event():
    """Stop poller on shutdown"""
    from app.inference.model_loader import model_loader
    model_loader.stop()


@app.get("/")
async def root():
    return {
        "service": "prediction-service",
        "status": "running",
        "ready": model_loader.model is not None,
        "version": model_loader.model_version
    }


    