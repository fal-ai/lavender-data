from fastapi import APIRouter

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
