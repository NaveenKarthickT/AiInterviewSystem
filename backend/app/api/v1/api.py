from fastapi import APIRouter

# Create the parent router first to avoid circular imports
api_router = APIRouter()

# Import sub‑modules after the router exists so they can register their own routes
from app.api.v1 import auth, resumes, interviews, speech, reports, optimization

# Attach sub‑routers
api_router.include_router(auth.router,        prefix="/auth",        tags=["Authentication"])
api_router.include_router(resumes.router,    prefix="/resumes",    tags=["Resumes"])
api_router.include_router(interviews.router, prefix="/interviews", tags=["Interviews"])
api_router.include_router(speech.router,     prefix="/speech",     tags=["Speech"])
api_router.include_router(reports.router,    prefix="/reports",    tags=["Reports"])
api_router.include_router(optimization.router, prefix="/optimization", tags=["Resume Optimization"])
