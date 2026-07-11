import time
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from redis import Redis
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST, Counter, Histogram
from app.core.config import settings
from app.core.database import get_db

router = APIRouter()

# Define Prometheus metrics
REQUEST_COUNT = Counter(
    "api_requests_total",
    "Total number of API requests",
    ["method", "endpoint", "status"]
)

REQUEST_LATENCY = Histogram(
    "api_request_latency_seconds",
    "API request latency in seconds",
    ["endpoint"]
)

AI_INFERENCE_TIME = Histogram(
    "ai_inference_duration_seconds",
    "AI Whisper and LLM inference timings",
    ["model_type"]
)


@router.get("/health")
def health_check(db: Session = Depends(get_db)):
    """Health check for API, DB, and Redis systems."""
    health_status = {
        "status": "healthy",
        "timestamp": time.time(),
        "services": {
            "api": "online",
            "database": "offline",
            "cache_redis": "offline"
        }
    }
    
    # 1. Test Database
    try:
        db.execute(text("SELECT 1"))
        health_status["services"]["database"] = "online"
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["services"]["database"] = f"error: {str(e)}"
        
    # 2. Test Redis
    try:
        r = Redis.from_url(settings.REDIS_URL, socket_connect_timeout=1)
        r.ping()
        health_status["services"]["cache_redis"] = "online"
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["services"]["cache_redis"] = f"error: {str(e)}"

    if health_status["status"] == "unhealthy":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=health_status
        )
        
    return health_status


@router.get("/metrics")
def get_prometheus_metrics():
    """Exposes Prometheus-compatible operational metrics."""
    # Add dummy gauge modifications or scrape updates if needed
    data = generate_latest()
    from fastapi.responses import Response
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)
