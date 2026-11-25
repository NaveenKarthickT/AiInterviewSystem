from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from app.core.config import settings
from app.core.database import Base, engine
from app.core.rate_limiter import RateLimiterMiddleware
from app.api.v1.api import api_router

# Create database tables automatically for development/testing
Base.metadata.create_all(bind=engine)

api_v1_prefix = "/" + settings.API_V1_STR.strip("/")

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Adaptive AI-driven interview preparation and intelligent resume optimization platform for engineering students.",
    version="1.0.0",
    openapi_url=f"{api_v1_prefix}/openapi.json",
    docs_url=f"{api_v1_prefix}/docs",
    redoc_url=f"{api_v1_prefix}/redoc",
)

# Set CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins in dev mode; configure strictly in prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API v1 router
app.include_router(api_router, prefix=api_v1_prefix)

# --- Security Headers Middleware ---
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains"
        return response

app.add_middleware(SecurityHeadersMiddleware)

# --- Rate Limiter Middleware ---
app.add_middleware(RateLimiterMiddleware)

@app.get("/health", tags=["Health"])
def health_check():
    """Health check endpoint to verify backend status."""
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "api_version": "v1"
    }
