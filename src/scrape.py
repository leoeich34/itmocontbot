from __future__ import annotations
import re, json, time
from dataclasses import dataclass, asdict
from typing import List, Dict, Tuple
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

from .config import DEFAULT_URLS, PROGRAMS_JSON, MAX_CHUNK_LEN
from .parsefile import pdf_bytes_to_text

HEADERS = {"User-Agent": "Mozilla/5.0 (itmo-chooser-bot/1.0)"}

@dataclass
class ProgramData:
    key: str                 # ключ "ai" | "ai_product"
    name: str
    url: str
    text_chunks: List[str]
    courses: List[str]       # эвристически извлечённый список дисциплин

def _fetch(url: str) -> requests.Response:
    r = requests.get(url, headers=HEADERS, timeout=30)
    r.raise_for_status()
    return r

def _clean_text(s: str) -> str:
    s = re.sub(r"[ \t]+", " ", s)
    s = re.sub(r"\n{2,}", "\n", s)
    return s.strip()

def _chunk(text: str, max_len: int = MAX_CHUNK_LEN) -> List[str]:
    parts: List[str] = []
    buf = []
    cur = 0
    for para in re.split(r"\n+", text):
        para = para.strip()
        if not para:
            continue
        if cur + len(para) + 1 > max_len and buf:
            parts.append(" ".join(buf))
            buf, cur = [para], len(para)
        else:
            buf.append(para)
            cur += len(para) + 1
    if buf:
        parts.append(" ".join(buf))
    # лёгкая дедупликация
    seen, result = set(), []
    for p in parts:
        key = p.lower()
        if key not in seen:
            result.append(p)
            seen.add(key)
    return result

def _extract_title(soup: BeautifulSoup) -> str:
    h1 = soup.find("h1")
    if h1 and h1.get_text(strip=True):
        return h1.get_text(strip=True)
    if soup.title and soup.title.get_text(strip=True):
        return soup.title.get_text(strip=True)
    return "Программа магистратуры"

def _extract_html_text(soup: BeautifulSoup) -> str:
    # Собираем видимый текст со страницы (основной контент)
    for tag in soup(["script", "style", "noscript"]):
        tag.extract()
    text = soup.get_text("\n")
    text = _clean_text(text)
    # Небольшая фильтрация мусора
    text = "\n".join([ln for ln in text.splitlines() if len(ln.strip()) > 2])
    return text

def _find_plan_links(base_url: str, soup: BeautifulSoup) -> List[str]:
    links = []
    for a in soup.find_all("a", href=True):
        text = (a.get_text() or "").lower()
        href = a["href"]
        if any(word in text for word in ["учеб", "план", "curriculum"]) or href.lower().endswith(".pdf"):
            full = urljoin(base_url, href)
            if full not in links:
                links.append(full)
    # оставим только pdf — учебные планы чаще всего в pdf
    pdfs = [u for u in links if u.lower().endswith(".pdf")]
    return pdfs[:5]  # safety
def _extract_courses_guess(text: str) -> List[str]:
    """
    Здесь расположены строки, похожие на названия дисциплин.
     Они содержат буквы, не слишком длинные/короткие,
      и часто встречаются в списках/таблицах PDF (каждая с новой строки)
    """
    candidates = []
    for ln in text.splitlines():
        s = ln.strip()
        if 6 <= len(s) <= 90 and not s.isupper():
            # отсекаем явные служебные строки
            if not re.search(r"(семестр|кред|зачет|экзамен|hours|ects|таблица|приложение)", s, re.I):
                # должен быть хотя бы 1 пробел (обычно многословные названия)
                if " " in s:
                    candidates.append(s)
    # нормализуем и дедуплицируем
    cleaned = []
    seen = set()
    for c in candidates:
        c = re.sub(r"\s{2,}", " ", c)
        c = c.strip("·•—-–;:, ")
        key = c.lower()
        if 6 <= len(c) <= 90 and key not in seen:
            cleaned.append(c)
            seen.add(key)
    # возьмём до 80 штук, чтобы не заполнять запрос лишней информацией
    return cleaned[:80]

def build_program(url_key: str, url: str) -> ProgramData:
    r = _fetch(url)
    soup = BeautifulSoup(r.text, "html.parser")
    name = _extract_title(soup)
    html_text = _extract_html_text(soup)

    pdf_links = _find_plan_links(url, soup)
    pdf_texts = []
    for pdf_url in pdf_links:
        try:
            pr = _fetch(pdf_url)
            ptxt = pdf_bytes_to_text(pr.content)
            if ptxt:
                pdf_texts.append(ptxt)
            time.sleep(0.5)
        except Exception:
            continue

    all_text = html_text + ("\n\n" + ("\n\n".join(pdf_texts)) if pdf_texts else "")
    text_chunks = _chunk(all_text)

    # список курсов пытаемся вытащить из pdf, иначе пробуем из html
    course_source = "\n".join(pdf_texts) if pdf_texts else html_text
    courses = _extract_courses_guess(course_source)

    return ProgramData(
        key=url_key,
        name=name,
        url=url,
        text_chunks=text_chunks,
        courses=courses,
    )

def ingest(urls: Dict[str, str] = None) -> Dict[str, dict]:
    urls = urls or DEFAULT_URLS
    result: Dict[str, dict] = {}
    for key, url in tqdm(urls.items(), desc="Ingest programs"):
        prog = build_program(key, url)
        result[key] = asdict(prog)
    PROGRAMS_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2))
    return result

def load_or_ingest() -> Dict[str, dict]:
    if PROGRAMS_JSON.exists():
        return json.loads(PROGRAMS_JSON.read_text(encoding="utf-8"))
    return ingest()