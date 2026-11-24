from functools import lru_cache

from mistralai.client import Mistral
from backend.app.config import get_setting


@lru_cache(maxsize=1)
def _get_client() -> Mistral:
    setting = get_setting()
    return Mistral(api_key=setting.mistral_api_key)


def _embed_text(text: str) -> list[float]:
    setting = get_setting()
    response = _get_client().embeddings.create(
        model=setting.mistral_model,
        inputs=[text],
    )
    return response.data[0].embedding


def embed_job_listing(
    title: str,
    description: str | None,
    location: str,
) -> list[float]:
    """Embed a job using only its title, description, and location."""
    fields = [f"Title: {title}"]
    if description:
        fields.append(f"Description: {description}")
    fields.append(f"Location: {location}")

    return _embed_text("\n".join(fields))


def embed_cv_text(cv_text: str) -> list[float]:
    """Embed the supplied CV text with Mistral."""
    return _embed_text(cv_text)