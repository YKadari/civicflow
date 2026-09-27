from fastapi import FastAPI

from app.api.routes import router


app = FastAPI(
    title="CivicFlow API",
    description="Backend API for the CivicFlow case-management platform.",
    version="0.1.0",
)


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "civicflow-api",
    }


app.include_router(router)