from supabase import Client

from backend.app.models.job import JobListing


class JobDeduplicator:
    """Insert jobs into Supabase only when their content hash is new."""

    def __init__(self, client: Client) -> None:
        self._client = client

    def add_if_new(self, job: JobListing) -> bool:
        """Return True when the job was inserted, or False when its hash already exists."""
        if not job.content_hash:
            raise ValueError("Job must have a content_hash before it can be stored.")

        existing = (
            self._client.table("jobs")
            .select("id")
            .eq("content_hash", job.content_hash)
            .limit(1)
            .execute()
        )
        if existing.data:
            return False

        self._client.table("jobs").insert(
            job.model_dump(mode="json", exclude={"job_id"})
        ).execute()
        return True
