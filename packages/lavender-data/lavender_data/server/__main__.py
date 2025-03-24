import argparse
from uvicorn import run


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", type=str, default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--reload", action="store_true")
    parser.add_argument("--workers", type=int, default=1)

    args = parser.parse_args()

    run(
        "lavender_data.server:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        workers=args.workers,
    )
