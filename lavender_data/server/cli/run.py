import os
from dotenv import load_dotenv
import uvicorn

from lavender_data.logging import get_logger
from lavender_data.server.settings import get_settings

from .create_api_key import create_api_key
from .db import migrate


def run(env_file: str = ".env", init: bool = False):
    load_dotenv(env_file)

    if init:
        os.environ["LAVENDER_DATA_UI_FORCE_INSTALL_DEPENDENCIES"] = "true"
        migrate(env_file)

    settings = get_settings()

    if init:
        api_key = create_api_key(note="INIT")
        print(f"API key created: {api_key.id}:{api_key.secret}")

    config = uvicorn.Config(
        "lavender_data.server:app",
        host=settings.lavender_data_host,
        port=settings.lavender_data_port,
        reload=False,
        workers=1,
        env_file=env_file,
    )

    server = uvicorn.Server(config)

    get_logger("uvicorn", clear_handlers=True)
    get_logger("uvicorn.access", clear_handlers=True).disabled = True

    try:
        server.run()
    except KeyboardInterrupt:
        pass
