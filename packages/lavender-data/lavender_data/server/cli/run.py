import logging

import uvicorn

from lavender_data.logging import sh, fh
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

    logging.getLogger("uvicorn").handlers.clear()
    logging.getLogger("uvicorn").addHandler(sh)
    logging.getLogger("uvicorn").addHandler(fh)

    server.run()
