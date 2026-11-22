from collections.abc import Iterable
from html import unescape
from typing import Any

from bs4 import BeautifulSoup


def _clean_value(value: Any) -> Any:
    if isinstance(value, str):
        return unescape(value).strip()
    if isinstance(value, list):
        return [_clean_value(item) for item in value]
    if isinstance(value, dict):
        return {key: _clean_value(item) for key, item in value.items()}
    return value


class JobSanitizer:
    """Clean job data returned by the Adzuna API."""

    @staticmethod
    def sanitize_job(job: dict[str, Any]) -> dict[str, Any]:
        # Decode HTML entities, trim string values, and strip HTML from the title.
        sanitized = _clean_value(job)
        title = sanitized.get("title")
        if isinstance(title, str):
            sanitized["title"] = BeautifulSoup(title, "html.parser").get_text(
                " ", strip=True
            )
        return sanitized

    @classmethod
    def sanitize_jobs(cls, jobs: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
        return [cls.sanitize_job(job) for job in jobs]