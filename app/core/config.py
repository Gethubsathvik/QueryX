"""Application settings, read once from environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
VIEWS_DIR = ROOT / "app" / "views"


@dataclass(frozen=True)
class Settings:
    data_dir: Path
    max_rows: int = 500
    query_timeout: float = 3.0
    anthropic_api_key: str = ""
    model: str = "claude-sonnet-5-5"
    engine: str = ""
    internal_token: str = ""

    @classmethod
    def from_env(cls, data_dir: Path | str | None = None) -> Settings:
        env = os.environ
        return cls(
            data_dir=Path(data_dir or env.get("QUERYX_DATA_DIR") or ROOT / "data"),
            max_rows=int(env.get("QUERYX_MAX_ROWS", "500")),
            query_timeout=float(env.get("QUERYX_QUERY_TIMEOUT", "3")),
            anthropic_api_key=env.get("ANTHROPIC_API_KEY", "").strip(),
            model=env.get("QUERYX_MODEL", "claude-sonnet-5-5"),
            engine=env.get("QUERYX_ENGINE", "").strip().lower(),
            internal_token=env.get("QUERYX_INTERNAL_TOKEN", ""),
        )
