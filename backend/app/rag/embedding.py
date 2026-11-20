import voyageai

from backend.app.config import get_setting


def _embed_text(text: str) -> list[float]:
    setting = get_setting()
    response = voyageai.Client(api_key=setting.voyageai_api_key).embed(
        [text],
        model=setting.voyageai_model,
        input_type="document",
    )
    return response.embeddings[0]


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
    """Embed the supplied CV text with VoyageAI."""
    return _embed_text(cv_text)