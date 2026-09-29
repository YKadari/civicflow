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


local_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

frontend_origin = os.getenv(
    "FRONTEND_ORIGIN"
)

if frontend_origin:
    local_origins.append(
        frontend_origin.rstrip("/")
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=local_origins,
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "civicflow-api",
    }


app.include_router(router)