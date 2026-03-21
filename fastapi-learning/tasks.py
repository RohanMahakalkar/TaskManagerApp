from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends, Query
from bson import ObjectId
from typing import Optional

from database import tasks_collection
from schemas import TaskCreate, TaskUpdate, TaskOut
from auth import get_current_user, require_roles

tasks_router = APIRouter(prefix="/tasks", tags=["tasks"])


@tasks_router.post("", response_model=dict)
def create_task(task: TaskCreate, current_user: dict = Depends(get_current_user)):
    now = datetime.utcnow()
    result = tasks_collection.insert_one({
        "name": task.name,
        "user_id": current_user["user_id"],
        "created_at": now,
        "updated_at": now,
    })
    return {"task_id": str(result.inserted_id)}


@tasks_router.get("", response_model=dict)
def get_tasks(
    current_user: dict = Depends(get_current_user),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    search: Optional[str] = Query(None),
):
    query = {"user_id": current_user["user_id"]}
    if search:
        query["name"] = {"$regex": search, "$options": "i"}

    total = tasks_collection.count_documents(query)
    skip = (page - 1) * limit

    cursor = tasks_collection.find(query).skip(skip).limit(limit)

    tasks = [
        TaskOut(
            id=str(task["_id"]),
            name=task["name"],
            user_id=task["user_id"],
            created_at=task.get("created_at"),
            updated_at=task.get("updated_at"),
        )
        for task in cursor
    ]

    return {
        "page": page,
        "limit": limit,
        "total": total,
        "pages": (total + limit - 1) // limit,
        "search": search,
        "items": tasks,
    }


@tasks_router.put("/{task_id}", response_model=dict)
def update_task(task_id: str, payload: TaskUpdate, current_user: dict = Depends(get_current_user)):
    if not payload.name:
        raise HTTPException(status_code=400, detail="Nothing to update")
    try:
        oid = ObjectId(task_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid task_id")

    update_data = {"updated_at": datetime.utcnow()}
    if payload.name:
        update_data["name"] = payload.name

    result = tasks_collection.update_one(
        {"_id": oid, "user_id": current_user["user_id"]},
        {"$set": update_data},
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Task not found")

    return {"task_id": task_id, "status": "updated"}


@tasks_router.delete("/{task_id}", response_model=dict)
def delete_task(task_id: str, current_user: dict = Depends(require_roles("admin", "user"))):
    try:
        oid = ObjectId(task_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid task_id")

    filter_query = {"_id": oid}
    if current_user["role"] != "admin":
        filter_query["user_id"] = current_user["user_id"]

    result = tasks_collection.delete_one(filter_query)
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Task not found")

    return {"message": "Task deleted"}
