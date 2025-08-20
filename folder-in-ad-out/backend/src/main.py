from fastapi import FastAPI
from .api.routes import router as api_router

app = FastAPI(title="Folder-in, Ad-out")

@app.get("/health")
def health():
    return {"ok": True}

app.include_router(api_router, prefix="/api")
