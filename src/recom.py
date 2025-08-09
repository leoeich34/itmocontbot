from __future__ import annotations
from typing import Dict, List, Tuple
import re

SKILL_KEYWORDS = {
    "python": ["python", "питон"],
    "ml": ["machine learning","ml","машинн","обучен"],
    "ds": ["data","данн","аналитик","statistics","статист"],
    "math": ["матем", "матстат", "вероят", "алгебр", "анал"],
    "cv": ["computer vision","cv","компьютерн","зрение"],
    "nlp": ["nlp","обработк","текст", "язык"],
    "pm": ["product","продакт","менедж","бизнес","маркет"],
    "se": ["backend","software","разработ","инженер","системн","архитект"],
}

def _score_course(course: str, user_skills: List[str]) -> int:
    s = course.lower()
    score = 0
    for sk in user_skills:
        kws = SKILL_KEYWORDS.get(sk, [sk])
        if any(kw in s for kw in kws):
            score += 2
    # общие полезные слова
    if re.search(r"(практик|workshop|project|проект|практикум)", s, re.I): score += 1
    if re.search(r"(углубл|advanced|продвинут)", s, re.I): score += 1
    return score

def recommend_courses(program: Dict, skills_csv: str, top_n: int = 7) -> Tuple[List[str], List[Tuple[str,int]]]:
    user_skills = [s.strip().lower() for s in skills_csv.split(",") if s.strip()]
    courses = program.get("courses") or []
    if not courses:
        # возьмём самые информативные части из текстов
        guess = [t for t in program.get("text_chunks", []) if 15 < len(t) < 100]
        courses = guess[:20]
    scored = [(c, _score_course(c, user_skills)) for c in courses]
    scored.sort(key=lambda x: x[1], reverse=True)
    top = [c for c, sc in scored[:top_n] if sc > 0]
    if not top:
        # если по ключевым словам ничего не нашлось — вернём первые разумные
        top = courses[:top_n]
    return top, scored[:20]