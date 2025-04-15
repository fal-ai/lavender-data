import uvicorn

from dotenv import load_dotenv
from lavender_data.server.ui import setup_ui


def run(
    host: str = "0.0.0.0",
    port: int = 8000,
    reload: bool = False,
    workers: int = 1,
    disable_ui: bool = False,
    ui_port: int = 3000,
):
    load_dotenv()

    if not disable_ui:
        setup_ui(f"http://{host}:{port}", ui_port)

    uvicorn.run(
        "lavender_data.server:app",
        host=host,
        port=port,
        reload=reload,
        workers=workers,
    )
