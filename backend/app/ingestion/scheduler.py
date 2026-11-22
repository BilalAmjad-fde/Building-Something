import asyncio
import logging
from datetime import timedelta
from typing import Any

from celery import Celery
from pydantic import ValidationError

# Load application settings and services used for scheduling and ingestion.
from backend.app.config import get_setting
from backend.app.db.supabase_client import get_supabase
from backend.app.ingestion.api_client import AdzunaClient
from backend.app.ingestion.deduplicator import JobDeduplicator
from backend.app.ingestion.sanitizer import JobSanitizer
from backend.app.models.job import JobListing

# Configure the module logger and load settings once at startup.
logger = logging.getLogger(__name__)
settings = get_setting()

# Create the Celery application with the configured Redis broker.
celery_app = Celery("job-fetcher", broker=settings.celery_broker_url)

# Register the periodic job-fetch task and run it at the configured interval.
celery_app.conf.beat_schedule = {
    "fetch-adzuna-jobs": {
        "task": "backend.app.ingestion.scheduler.fetch_and_store_jobs",
        "schedule": timedelta(hours=settings.fetch_interval_hour),
    }
}


def _required_text(job: dict[str, Any], field: str) -> str:
    # Read the requested field from the raw Adzuna job response.
    value = job.get(field)

    # Some fields contain a display_name value instead of a direct string.
    if isinstance(value, dict):
        value = value.get("display_name")

    # Reject missing, empty, or non-string values so invalid jobs are not stored.
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Adzuna job is missing required field: {field}")

    # Return the validated text to the caller.
    return value


def _to_job_listing(job: dict[str, Any]) -> JobListing:
    # Require an Adzuna job ID because it is used for identity and deduplication.
    adzuna_id = job.get("id")
    if adzuna_id is None:
        raise ValueError("Adzuna job is missing required field: id")

    # Convert the raw API response into the application's JobListing model.
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
    # Initialize deduplication with the Supabase database client.
    deduplicator = JobDeduplicator(get_supabase())

    # Track how many unique, newly added jobs are found.
    added_count = 0

    # Open the Adzuna HTTP client and automatically close it after fetching.
    async with AdzunaClient() as adzuna_client:
        jobs = await adzuna_client.fetch_jobs(settings.adzuna_country_code)

    # Process each job returned by the external API.
    for raw_job in jobs:
        # Sanitize raw job data before validating or storing it.
        cleaned_job = JobSanitizer.sanitize_job(raw_job)
        try:
            # Convert the cleaned response into the application's job model.
            job = _to_job_listing(cleaned_job)
        except (ValueError, ValidationError) as exc:
            # Log malformed jobs and continue processing the remaining results.
            logger.warning("Skipping invalid Adzuna job: %s", exc)
            continue

        # Store the job only when it is not already present and increase the count.
        if deduplicator.add_if_new(job):
            added_count += 1

    # Return the number of new jobs for reporting or task monitoring.
    return added_count


@celery_app.task(name="backend.app.ingestion.scheduler.fetch_and_store_jobs")
def fetch_and_store_jobs() -> int:
    # Bridge the async ingestion workflow to the synchronous Celery task interface.
    return asyncio.run(_fetch_and_store_jobs())
