import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router


app = FastAPI(
    title="CivicFlow",
    description=(
        "Policy-aware public-service "
        "case-management platform."
    ),
    version="1.0.0",
)


allowed_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "https://civicflow-wkvj.vercel.app",
]


# Optional environment-configured frontend URL.
frontend_origin = os.getenv(
    "FRONTEND_ORIGIN"
)

if frontend_origin:
    origin = frontend_origin.rstrip("/")

    if origin not in allowed_origins:
        allowed_origins.append(
            origin
        )


app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {
        "service": "CivicFlow API",
        "status": "online",
        "docs": "/docs",
    }


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "civicflow-api",
    }


app.include_router(router)