from fastapi import FastAPI
from sqlalchemy import text

from app.database.database import engine

from app.modules.auth.controller import auth_router
from app.modules.organizations.controller import organization_router

app = FastAPI(
    title="Project Management System",
    description="Backend API for Project Management System",
    version="1.0.0",
)

app.include_router(auth_router)
app.include_router(organization_router)

@app.get("/")
async def root():
    return {
        "message": "Project Management System API",
        "status": "running",
    }


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
    }


@app.get("/health/database")
async def database_health_check():
    async with engine.connect() as connection:
        result = await connection.execute(text("SELECT 1"))

    return {
        "database": "connected",
        "result": result.scalar(),
    }