"""FastAPI application for cmbenchmark web interface."""

from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from .api.endpoints import router

app = FastAPI(
    title="CM Benchmark API",
    description="REST API for CM Benchmark dataset scanning and parsing",
    version="1.0.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],  # Vite default ports
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(router, prefix="/api", tags=["api"])


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


# Serve static files from web/static/ directory
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    # Mount static files at root to serve assets (JS, CSS, etc.)
    # This must be mounted before the catch-all route
    app.mount("/assets", StaticFiles(directory=str(static_dir / "assets")), name="assets")
    
    # Serve index.html for root path
    @app.get("/")
    async def serve_index():
        """Serve the frontend index.html."""
        index_file = static_dir / "index.html"
        if index_file.exists():
            return FileResponse(str(index_file))
        return {"error": "Frontend not built. Run 'cmbenchmark web' to build and serve."}
    
    # Serve index.html for all non-API routes (SPA routing)
    # This must be registered last to catch all non-API routes
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        """Serve the frontend SPA for all non-API routes."""
        # Don't serve SPA for API routes, health endpoint, or assets
        if full_path.startswith("api") or full_path == "health" or full_path.startswith("assets"):
            return {"error": "Not found"}
        
        index_file = static_dir / "index.html"
        if index_file.exists():
            return FileResponse(str(index_file))
        return {"error": "Frontend not built. Run 'cmbenchmark web' to build and serve."}
else:
    # If static directory doesn't exist, provide a helpful message
    @app.get("/")
    async def root():
        """Root endpoint - frontend not built."""
        return {
            "message": "CM Benchmark API",
            "version": "1.0.0",
            "note": "Frontend not built. Run 'cmbenchmark web' to build and serve the UI."
        }

