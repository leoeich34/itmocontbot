from __future__ import annotations
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

PROGRAMS_JSON = DATA_DIR / "programs.json"

# рабочие ссылки
DEFAULT_URLS = {
    "ai": "https://abit.itmo.ru/program/master/ai",
    "ai_product": "https://abit.itmo.ru/program/master/ai_product",
}

# параметры выдачи ассистента Q&A
MAX_CHUNK_LEN = 550           # число символов на абзац
RELEVANCE_THRESHOLD = 0.1    # если параметр ниже, то отвечаем "вопрос нерелевантен"
TOP_K = 3
