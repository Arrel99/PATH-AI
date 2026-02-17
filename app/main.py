from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers.ai_router import router as ai_router
from app.path_ai.monitoring.logger import setup_logging

setup_logging()

app = FastAPI(
    title="PATH AI",
    description="TEST PATH AI",
    version="1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ai_router)

@app.get("/")
async def root():
    return {
        "name": "PATH AI",
        "version": "1.0",
        "status": "running",
        "docs": "/docs",
    }
