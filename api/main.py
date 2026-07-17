import os
from typing import Optional

from api.app import APIApp, create_app


app = create_app()


def get_app() -> APIApp:
    return app


def main(host: Optional[str] = None, port: Optional[int] = None) -> None:
    import uvicorn

    host = host or os.getenv("HOST", "0.0.0.0")
    port_value = port if port is not None else int(os.getenv("PORT", "8000"))
    uvicorn.run("api.main:app", host=host, port=port_value, reload=False)


if __name__ == "__main__":
    main()
