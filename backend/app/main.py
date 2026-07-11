import time
import warnings
from fastapi import FastAPI, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Suppress librosa file format and deprecation warnings to keep logs clean
warnings.filterwarnings("ignore", category=UserWarning, module="librosa")
warnings.filterwarnings("ignore", category=FutureWarning, module="librosa")
from redis import Redis
from app.core.config import settings
from app.api import auth, upload, analysis, monitoring

# Initialize FastAPI
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="API for AI-Powered English Pronunciation Assessment",
    version="1.0.0"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 1. Custom Security Headers & Rate Limiting Middleware
# Simple in-memory fallback if Redis is down
local_rate_limit_db = {}

@app.middleware("http")
async def security_and_rate_limiting_middleware(request: Request, call_next):
    # Retrieve client IP
    client_ip = request.client.host if request.client else "127.0.0.1"
    now = int(time.time())
    
    # Simple Rate Limiter (e.g. 30 requests per minute)
    minute_bucket = now // 60
    rate_limit_exceeded = False
    
    # Try Redis first
    try:
        r = Redis.from_url(settings.REDIS_URL, socket_connect_timeout=1)
        redis_key = f"rate_limit:{client_ip}:{minute_bucket}"
        current_requests = r.incr(redis_key)
        if current_requests == 1:
            r.expire(redis_key, 60)
        if current_requests > settings.RATE_LIMIT_PER_MINUTE:
            rate_limit_exceeded = True
    except Exception:
        # Fallback to local in-memory tracking
        key = (client_ip, minute_bucket)
        local_rate_limit_db[key] = local_rate_limit_db.get(key, 0) + 1
        if local_rate_limit_db[key] > settings.RATE_LIMIT_PER_MINUTE:
            rate_limit_exceeded = True
            
        # Clean old records from memory map to prevent memory leaks
        for k in list(local_rate_limit_db.keys()):
            if k[1] < minute_bucket:
                local_rate_limit_db.pop(k, None)

    if rate_limit_exceeded:
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={"detail": "Too many requests. Please try again later."}
        )

    # Execute request
    response: Response = await call_next(request)
    
    # Apply standard OWASP security headers
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = "default-src 'self'; frame-ancestors 'none';"
    
    return response


# 2. Global Error Handling
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    # Log exception internally, return generic error code to protect database structure details
    import logging
    logging.error(f"Unhandled system error: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal server error occurred. Please contact support."}
    )


# 3. Mount Routers
# Mount under v1 namespace
app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["Authentication"])
app.include_router(upload.router, prefix=f"{settings.API_V1_STR}/upload", tags=["Uploads"])
app.include_router(analysis.router, prefix=settings.API_V1_STR, tags=["Analysis & Scoring"])
app.include_router(monitoring.router, prefix=settings.API_V1_STR, tags=["Monitoring"])

# Mount flat endpoints at root level to satisfy direct REST requirements (e.g. POST /upload, GET /health)
app.include_router(upload.router, prefix="/upload", tags=["Direct Upload"])
app.include_router(analysis.router, prefix="", tags=["Direct Analysis"])
app.include_router(monitoring.router, prefix="", tags=["Direct Monitoring"])
