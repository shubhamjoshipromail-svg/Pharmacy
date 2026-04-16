import os

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.interactions import router as interactions_router
from app.api.patients import router as patients_router
from app.core.config import settings
from app.db.session import Base, engine
from app.models import *  # noqa: F401,F403

Base.metadata.create_all(bind=engine)

app = FastAPI(title=settings.APP_NAME, debug=settings.DEBUG)
app.include_router(patients_router, prefix="/api/v1")
app.include_router(interactions_router, prefix="/api/v1")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def print_registered_routes() -> None:
    print("Registered routes:")
    for route in sorted(app.routes, key=lambda item: item.path):
        methods = ",".join(sorted(route.methods)) if getattr(route, "methods", None) else ""
        print(f"{methods:20} {route.path}")


@app.get("/health")
def health_check():
    return {"status": "ok", "app": settings.APP_NAME}


frontend_dist = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")
frontend_assets = os.path.join(frontend_dist, "assets")

if os.path.exists(frontend_dist):
    if os.path.exists(frontend_assets):
        app.mount("/assets", StaticFiles(directory=frontend_assets), name="assets")

    @app.get("/")
    async def serve_root():
        return FileResponse(os.path.join(frontend_dist, "index.html"))

    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        if (
            full_path.startswith("api/")
            or full_path.startswith("docs")
            or full_path.startswith("health")
            or full_path.startswith("redoc")
            or full_path == "openapi.json"
        ):
            raise HTTPException(status_code=404)
        return FileResponse(os.path.join(frontend_dist, "index.html"))
