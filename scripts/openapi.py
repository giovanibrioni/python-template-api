"""Write openapi.yaml from the FastAPI app. Does not start the server."""

import json
from pathlib import Path

from app.main import app


def main() -> None:
    spec = app.openapi()
    Path("openapi.yaml").write_text(json.dumps(spec, indent=2, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
