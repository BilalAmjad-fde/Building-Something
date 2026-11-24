from functools import lru_cache
from backend.app.config import get_setting
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_mistralai import ChatMistralAI

from backend.app.models.cv import CVInfo

setting = get_setting()

MODEL_NAME = setting.gemini_api_model
MAX_CHARS = 30_000  # safety limit for very long CVs

SYSTEM_PROMPT = """You are an expert resume parser. Extract structured information from the CV text provided by the user.

Extract these fields:
- skills: list of technical skills, tools, frameworks and languages. Use standard names
  (e.g. "PyTorch" not "pytorch", "JavaScript" not "js"). No duplicates. No soft skills.
- experience_years: total professional work experience in years as a number. Count only
  jobs and internships, not education or personal projects. Use null if unclear.
- job_titles: list of job titles the person has held.
- education: list of degrees as "Degree, Field, Institution".
- projects: list of objects with "name" and a one-sentence "summary".
- certifications: list of certification names.
- location: city and country, or null.

Rules:
- Only use information that is explicitly present in the CV. Never guess or invent.
- If a field is missing from the CV, return an empty list (or null for single values).
- Do not include name, email, phone number or any contact details.
- Return only the structured output, no explanations.
"""


@lru_cache(maxsize=1)
def _get_llm():
    # Reads GOOGLE_API_KEY from the environment.
    primary = ChatGoogleGenerativeAI(api_key = setting.gemini_api_key,
                                    model=setting.gemini_api_model, temperature=0,max_retries=2).with_structured_output(CVInfo)

    gemini_backup = ChatGoogleGenerativeAI(api_key = setting.gemini_api_key, model="gemini-2.5-flash",
                                           temperature=0,max_retries=2).with_structured_output(CVInfo)

    mistral_backup = ChatMistralAI(model_name="mistral-small-latest",temperature=0
                                   ,api_key=setting.mistral_api_key).with_structured_output(CVInfo)
    return primary.with_fallbacks([gemini_backup,mistral_backup])
    


def extract_cv_info(raw_text: str) -> CVInfo:
    """Extract skills, experience, titles, education, projects, etc. from CV text."""
    if not isinstance(raw_text, str) or not raw_text.strip():
        raise ValueError("raw_text must be a non-empty string.")

    result = _get_llm().invoke(
        [
            ("system", SYSTEM_PROMPT),
            ("human", f"CV text:\n\n{raw_text[:MAX_CHARS]}"),
        ]
    )
    return result