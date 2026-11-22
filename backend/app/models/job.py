import hashlib
from datetime import date
from typing import Literal
from typing import Optional

from pydantic import BaseModel, Field, model_validator


class JobListing(BaseModel):
    job_id: str = Field(..., description="Unique identifier")
    adzuna_id: str | None = None
    title: str =Field(...,min_length=1,max_length=500)
    company: str =Field(...,min_length=1)
    location: str 
    description: str | None = None
    salary_range: str | None = None
    posting_date: date | None = None
    type: Literal["remote", "onsite"] | None = None
    redirect_url: str | None = None
    embedding: list[float] | None = None
    content_hash: Optional[str] = None

    def compute_hash(self) -> str:
        content = f"{self.title or ''}{self.description or ''}{self.company or ''}"
        return hashlib.md5(content.encode("utf-8"), usedforsecurity=False).hexdigest()

    @model_validator(mode="after")
    def set_content_hash(self) -> "JobListing":
        self.content_hash = self.compute_hash()
        return self

