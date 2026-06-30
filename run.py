#!/usr/bin/env python3
"""Launch the wind-field API server.

Usage:
    python run.py                 # serve on http://127.0.0.1:8000
    python run.py --host 0.0.0.0 --port 8080
"""
from __future__ import annotations

import argparse

import uvicorn


def main() -> None:
    parser = argparse.ArgumentParser(description="Ocean wind-field API server")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--reload", action="store_true")
    args = parser.parse_args()

    uvicorn.run(
        "windfield.api.app:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
    )


if __name__ == "__main__":
    main()
