"""HTTP client for the UIUC CIS course API.

Public, no auth. See docs/week1-api-recon.md for the endpoint map.

Key detail: `?mode=detail` on a COURSE url expands all of its sections and their
meetings inline, turning N+1 requests into 1. It does NOT cascade at the subject
level, so the ingest path is: subject listing -> per-course detail fetch.
"""

import time
from typing import Iterator

import httpx

from app.config import CIS_BASE_URL, CIS_TERM, CIS_YEAR

# Politeness delay between requests. Measured ~0.24 s/course including this.
REQUEST_DELAY_SECONDS = 0.15
TIMEOUT_SECONDS = 30.0
MAX_RETRIES = 3


class CISClient:
    """Fetches raw XML text from the CIS API. Does no parsing - see parse.py."""

    def __init__(self, year: str = CIS_YEAR, term: str = CIS_TERM) -> None:
        self.year = year
        self.term = term
        self.term_base = f"{CIS_BASE_URL}/{year}/{term}"
        self._client = httpx.Client(timeout=TIMEOUT_SECONDS)
        self.request_count = 0

    def __enter__(self) -> "CISClient":
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    def close(self) -> None:
        self._client.close()

    def _get(self, url: str) -> str:
        last_error: Exception | None = None
        for attempt in range(MAX_RETRIES):
            try:
                response = self._client.get(url)
                response.raise_for_status()
                self.request_count += 1
                time.sleep(REQUEST_DELAY_SECONDS)
                return response.text
            except Exception as exc:  # noqa: BLE001 - retry anything transient
                last_error = exc
                time.sleep(0.5 * (attempt + 1))
        raise RuntimeError(f"failed after {MAX_RETRIES} attempts: {url}") from last_error

    def fetch_term(self) -> str:
        """XML listing every subject offered in the configured term."""
        return self._get(f"{self.term_base}.xml")

    def fetch_subject(self, subject: str) -> str:
        """XML listing every course under one subject, e.g. 'CS'."""
        return self._get(f"{self.term_base}/{subject}.xml")

    def fetch_course_detail(self, subject: str, course_number: str) -> str:
        """XML for one course with all sections and meetings expanded inline."""
        return self._get(f"{self.term_base}/{subject}/{course_number}.xml?mode=detail")

    def iter_course_details(
        self, subject: str, course_numbers: list[str]
    ) -> Iterator[tuple[str, str]]:
        """Yield (course_number, xml) for each course, skipping ones that fail."""
        for number in course_numbers:
            try:
                yield number, self.fetch_course_detail(subject, number)
            except RuntimeError as exc:
                print(f"  SKIP {subject} {number}: {exc}")
