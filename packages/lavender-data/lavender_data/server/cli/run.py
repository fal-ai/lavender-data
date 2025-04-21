from dotenv import load_dotenv
import uvicorn

from lavender_data.logging import get_logger
from lavender_data.server.settings import get_settings


def run(env_file: str = ".env"):
    load_dotenv(env_file)

    settings = get_settings()

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
    get_logger("uvicorn.access", clear_handlers=True)

    server.run()
