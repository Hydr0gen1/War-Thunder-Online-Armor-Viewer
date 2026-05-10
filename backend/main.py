from __future__ import annotations
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from routers import vehicles, shells, armor

app = FastAPI(title="War Thunder Armor Viewer API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(vehicles.router)
app.include_router(shells.router)
app.include_router(armor.router)

# Serve GLB models as static files
models_dir = os.path.join(os.environ.get("DATA_DIR", "/app/data"), "models")
os.makedirs(models_dir, exist_ok=True)
app.mount("/api/models", StaticFiles(directory=models_dir), name="models")


@app.get("/health")
def health():
    return {"status": "ok"}
