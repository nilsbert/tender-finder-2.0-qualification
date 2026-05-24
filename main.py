import os
from core.logger import setup_logger
from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
from dotenv import load_dotenv

from core.database import db
from api.routes import router as qualification_router
from rating.routes import router as keywords_router

load_dotenv()
logger = setup_logger("main", "qualification")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize DB (Schema/Tables)
    await db.init_db()
    yield


app = FastAPI(
    title="Tender Finder Qualification Microservice",
    description="Isolated Qualification & Rating Service",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "http://localhost:8009").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check(response: Response):
    """Deep health check verifying database connectivity."""
    from sqlalchemy import text

    db_status = "healthy"
    try:
        async with db.engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception as e:
        logger.error(f"❌ Health check DB failure: {e}")
        db_status = "unhealthy"
        response.status_code = 503

    return {"status": "ok" if db_status == "healthy" else "degraded", "database": db_status, "service": "qualification"}


app.include_router(qualification_router, prefix="/api", tags=["qualification"])
app.include_router(keywords_router, prefix="/api", tags=["Keywords"])

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
            raise HTTPException(status_code=404, detail=f"API route not found: {full_path}")

        file_path = os.path.join(ui_dist_path, full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)

        return FileResponse(os.path.join(ui_dist_path, "index.html"))
else:

    @app.get("/")
    async def root():
        return {
            "message": "Qualification Microservice is running. Frontend not found in ui/dist. Please run 'npm run build' in qualification/ui."
        }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8002)
