from dotenv import load_dotenv
import uvicorn

from lavender_data.logging import get_logger
from lavender_data.server.ui import setup_ui


def run(
    host: str = "0.0.0.0",
    port: int = 8000,
    reload: bool = False,
    workers: int = 1,
    disable_ui: bool = False,
    ui_port: int = 3000,
    env_file: str = ".env",
):
    load_dotenv(env_file)

    if not disable_ui:
        setup_ui(f"http://{host}:{port}", ui_port)

    config = uvicorn.Config(
        "lavender_data.server:app",
        host=host,
        port=port,
        reload=reload,
        workers=workers,
        env_file=env_file,
    )

    server = uvicorn.Server(config)

    get_logger("uvicorn", clear_handlers=True)
    get_logger("uvicorn.access", clear_handlers=True)
    get_logger("uvicorn.error", clear_handlers=True)

    server.run()
