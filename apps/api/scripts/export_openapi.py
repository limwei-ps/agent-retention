"""Dump the FastAPI OpenAPI schema as JSON to stdout.

Used by the root `gen:types` script to regenerate `packages/shared-types`. Imports
the app without running a server, so no port/network is needed.
"""

from __future__ import annotations

import json
import pathlib
import sys

# Make the api root importable regardless of the caller's cwd.
API_ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(API_ROOT))

from app.main import app  # noqa: E402


def main() -> None:
    sys.stdout.write(json.dumps(app.openapi()))


if __name__ == "__main__":
    main()
