from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from .api import podcasts, admin, newsletter
from .database import engine
from .models import Base

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(podcasts.router, prefix="/api", tags=["podcasts"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])
app.include_router(newsletter.router, prefix="/api/newsletter", tags=["newsletter"])


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "pod_digest"}


@app.get("/")
async def root():
    return {"message": "Welcome to Podcast Digest API"}