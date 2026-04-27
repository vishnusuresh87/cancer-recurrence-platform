import os
import httpx
from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Cancer Platform BFF", version="1.0.0")

# Centralized CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Service URLs from Environment
AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://auth-service:8001")
PREDICTION_SERVICE_URL = os.getenv("PREDICTION_SERVICE_URL", "http://prediction-service:8003")

@app.api_route("/api/auth{path:path}", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])
async def auth_proxy(request: Request, path: str):
    """Proxy requests to Auth Service"""
    return await proxy_request(f"{AUTH_SERVICE_URL}/api/v1/auth{path}", request)

@app.api_route("/api/predict{path:path}", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])
async def predict_proxy(request: Request, path: str):
    """Proxy requests to Prediction Service"""
    """Proxy requests to Prediction Service (Increased timeout for ML inference)"""
    return await proxy_request(f"{PREDICTION_SERVICE_URL}/api/v1/predict{path}", request, timeout=30.0)

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "bff-service"}

async def proxy_request(url: str, request: Request, timeout: float = 10.0):
    """Helper to forward requests and return responses as-is"""
    method = request.method
    headers = dict(request.headers)
    # Remove host header to avoid confusion in downstream services
    headers.pop("host", None)
    
    content = await request.body()
    
    print(f"📡 BFF Proxy: {method} {request.url.path} -> {url}")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.request(
                method,
                url,
                headers=headers,
                params=request.query_params,
                content=content,
                timeout=timeout
            )
            
            # Return response with same status and headers
            return Response(
                content=response.content,
                status_code=response.status_code,
                headers=dict(response.headers)
            )
    except httpx.ConnectError:
        print(f"❌ BFF Error: Could not connect to {url}. Service might be down.")
        raise HTTPException(status_code=503, detail=f"Service at {url} is unreachable.")
    except httpx.TimeoutException:
        print(f"❌ BFF Error: Request to {url} timed out after {timeout}s.")
        raise HTTPException(status_code=504, detail=f"Request to upstream service timed out.")
    except Exception as e:
        print(f"❌ BFF Error: Proxy failed: {str(e)}")
        raise HTTPException(status_code=503, detail=f"Service unavailable: {str(e)}")
