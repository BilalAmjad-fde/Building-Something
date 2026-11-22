import asyncio
import logging
from datetime import timedelta
from typing import Any

from celery import Celery
from pydantic import ValidationError

from backend.app.config import get_setting
from backend.app.db.supabase_client import get_supabase
from backend.app.ingestion.api_client import AdzunaClient
from backend.app.ingestion.deduplicator import JobDeduplicator
from backend.app.ingestion.sanitizer import JobSanitizer
from backend.app.models.job import JobListing

logger = logging.getLogger(__name__)
settings = get_setting()

celery_app = Celery("job-fetcher", broker=settings.celery_broker_url)
celery_app.conf.beat_schedule = {
    "fetch-adzuna-jobs": {
        "task": "backend.app.ingestion.scheduler.fetch_and_store_jobs",
        "schedule": timedelta(hours=settings.fetch_interval_hour),
    }
}


def _required_text(job: dict[str, Any], field: str) -> str:
    value = job.get(field)
    if isinstance(value, dict):
        value = value.get("display_name")
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Adzuna job is missing required field: {field}")
    return value


def _to_job_listing(job: dict[str, Any]) -> JobListing:
    adzuna_id = job.get("id")
    if adzuna_id is None:
        raise ValueError("Adzuna job is missing required field: id")
    return JobListing(
        job_id=str(adzuna_id),
        adzuna_id=str(adzuna_id),
        title=_required_text(job, "title"),
        company=_required_text(job, "company"),
        location=_required_text(job, "location"),
        description=job.get("description"),
        redirect_url=job.get("redirect_url"),
    )


async def _fetch_and_store_jobs() -> int:
    deduplicator = JobDeduplicator(get_supabase())
    added_count = 0

    async with AdzunaClient() as adzuna_client:
        jobs = await adzuna_client.fetch_jobs(settings.adzuna_country_code)

    for raw_job in jobs:
        cleaned_job = JobSanitizer.sanitize_job(raw_job)
        try:
            job = _to_job_listing(cleaned_job)
        except (ValueError, ValidationError) as exc:
            logger.warning("Skipping invalid Adzuna job: %s", exc)
            continue
        if deduplicator.add_if_new(job):
            added_count += 1

    return added_count


@celery_app.task(name="backend.app.ingestion.scheduler.fetch_and_store_jobs")
def fetch_and_store_jobs() -> int:
    return asyncio.run(_fetch_and_store_jobs())
