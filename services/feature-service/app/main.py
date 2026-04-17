from fastapi import FastAPI
from app.api.v1 import transform

app = FastAPI(title="Feature Engineering Service")

app.include_router(transform.router, prefix="/api/v1", tags=["transform"])

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "feature-service"}