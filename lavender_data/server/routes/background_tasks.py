from fastapi import APIRouter, HTTPException

from lavender_data.server.background_worker import (
    CurrentBackgroundWorker,
    TaskMetadata,
)

router = APIRouter(prefix="/background-tasks", tags=["background-tasks"])


@router.get("/")
def get_tasks(
    background_worker: CurrentBackgroundWorker,
) -> list[TaskMetadata]:
    return background_worker.running_tasks()


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
