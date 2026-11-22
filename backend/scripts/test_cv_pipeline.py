from backend.app.parser.pdf_parser import PdfParser
from backend.app.parser.cv_info_extractor import extract_cv_info
from backend.app.rag.embedding import embed_cv_text
from backend.app.models.cv import CV
from backend.app.db.supabase_client import get_supabase
from pathlib import Path

supabase = get_supabase()
# apna supabase client yahan import karo

path = Path(r"D:\Building Something\backend\testing\sample\myCV.pdf")
raw_text = PdfParser.extract_text(path)
print("TEXT:", raw_text[:300])                  # 1. text sahi nikla?

info = extract_cv_info(raw_text)
print("INFO:", info.model_dump_json(indent=2))  # 2. skills/experience sahi hain?

cv = CV(file_name=path.name, raw_text=raw_text, embedding=embed_cv_text(raw_text),
        **info.model_dump())
print("DIMS:", len(cv.embedding), "HASH:", cv.content_hash)   # 3. 1024 dims?

supabase.table("cvs").upsert(cv.to_db_row(), on_conflict="content_hash",
                             ignore_duplicates=True).execute()