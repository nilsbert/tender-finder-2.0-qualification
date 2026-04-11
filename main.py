import os
import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
from dotenv import load_dotenv

from .core.database import db
from .api.routes import router as qualification_router
from .rating.routes import router as keywords_router

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize DB (Schema/Tables)
    await db.init_db()
    yield

app = FastAPI(
    title="Tender Finder Qualification Microservice",
    description="Isolated Qualification & Rating Service",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "qualification"}

app.include_router(qualification_router, prefix="/api", tags=["qualification"])
app.include_router(keywords_router, prefix="/api", tags=["Keywords"])

from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse

# Serve isolated frontend static files for the qualification service
ui_dist_path = os.path.join(os.path.dirname(__file__), "ui", "dist")

if os.path.exists(ui_dist_path):
    app.mount("/assets", StaticFiles(directory=os.path.join(ui_dist_path, "assets")), name="assets")
    
    @app.get("/")
    async def root_redirect():
        return RedirectResponse(url="/ms/qualification/")
    
    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        if full_path.startswith("api") or full_path == "health":
            return None
            
        file_path = os.path.join(ui_dist_path, full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
            
        return FileResponse(os.path.join(ui_dist_path, "index.html"))
else:
    @app.get("/")
    async def root():
        return {"message": "Qualification Microservice is running. Frontend not found in ui/dist. Please run 'npm run build' in qualification/ui."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
