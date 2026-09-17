"""Environment configuration. Reads .env at import; validates lazily.

Nothing here raises on import. A tool that only talks to the UIUC API
(scripts/explore_api.py) must not need a database to exist.
Validation happens where the value is actually used - see require_database_url().
"""

import os
from pathlib import Path

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(REPO_ROOT / ".env")

DATABASE_URL = os.getenv("DATABASE_URL", "")

CIS_BASE_URL = os.getenv(
    "CIS_BASE_URL", "https://courses.illinois.edu/cisapp/explorer/schedule"
)
CIS_YEAR = os.getenv("CIS_YEAR", "2026")
CIS_TERM = os.getenv("CIS_TERM", "fall")

# Optional - only for geocoding and the Week 5 Directions comparison.
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY", "")


def require_database_url() -> str:
    if not DATABASE_URL:
        raise RuntimeError(
            "DATABASE_URL is not set. Copy .env.example to .env and fill it in, "
            "then start Postgres with: docker compose up -d"
        )
    return DATABASE_URL


def require_google_key() -> str:
    if not GOOGLE_MAPS_API_KEY:
        raise RuntimeError(
            "GOOGLE_MAPS_API_KEY is not set. Needed for geocoding and the "
            "Week 5 Directions comparison."
        )
    return GOOGLE_MAPS_API_KEY
