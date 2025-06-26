from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from lavender_data.server.background_worker import (
    CurrentBackgroundWorker,
    TaskStatus,
)

router = APIRouter(prefix="/background-tasks", tags=["background-tasks"])


class TaskItem(TaskStatus):
    task_id: str


@router.get("/")
def get_tasks(
    background_worker: CurrentBackgroundWorker,
) -> list[TaskItem]:
    tasks = background_worker.list_tasks()
    return [
        TaskItem(task_id=task_id, **status.model_dump())
        for task_id, status in tasks.items()
    ]


@router.post("/{task_uid}/abort")
def abort_task(
    task_uid: str,
    background_worker: CurrentBackgroundWorker,
):
    if background_worker.get_task_status(task_uid) is None:
        raise HTTPException(status_code=404, detail="Task not found")

    try:
        background_worker.abort(task_uid)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
