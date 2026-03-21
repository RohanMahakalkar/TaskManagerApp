from fastapi import FastAPI

from auth import auth_router
from tasks import tasks_router

app = FastAPI(title="FastAPI Task Manager")

app.include_router(auth_router)
app.include_router(tasks_router)


@app.get("/")
def home():
    return {"message": "FastAPI + MongoDB + JWT backend"}


@app.get("/health")
def health_check():
    """Health check endpoint for load balancers and orchestrators"""
    return {"status": "healthy", "service": "fastapi-task-manager"}
