from __future__ import annotations
from pdfminer.high_level import extract_text
from io import BytesIO

def pdf_bytes_to_text(content: bytes) -> str:
    """
    Функция извлекает данные из PDF-байтов и возвращает сырой текст.
    """
    try:
        return extract_text(BytesIO(content)) or ""
    except Exception:
        return ""