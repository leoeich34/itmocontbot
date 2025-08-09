from __future__ import annotations
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .config import RELEVANCE_THRESHOLD, TOP_K

RUS_STOPWORDS = [
    "и","в","во","не","что","он","на","я","с","со","как","а","то","все","она","так","его","но",
    "да","ты","к","у","же","вы","за","бы","по","только","ее","мне","было","вот","от","меня",
    "еще","нет","о","из","ему","теперь","когда","даже","ну","вдруг","ли","если","уже","или",
    "ни","быть","был","него","до","вас","нибудь","опять","уж","вам","ведь","там","потом","себя",
]

def _norm(s: str) -> str:
    s = s.lower()
    s = re.sub(r"[^а-яa-z0-9\-\s.,:;()/%+]", " ", s)
    s = re.sub(r"\s{2,}", " ", s)
    return s.strip()

@dataclass
class QAEngine:
    vectorizer: TfidfVectorizer
    matrix: any
    chunks: List[str]
    meta: List[Tuple[str, int]]  # (program_key, chunk_index)

    @classmethod
    def from_programs(cls, programs: Dict[str, dict]) -> "QAEngine":
        docs, meta = [], []
        for pkey, pobj in programs.items():
            for i, ch in enumerate(pobj["text_chunks"]):
                docs.append(_norm(ch))
                meta.append((pkey, i))
        vec = TfidfVectorizer(stop_words=RUS_STOPWORDS, ngram_range=(1,2), min_df=2)
        X = vec.fit_transform(docs)
        return cls(vec, X, docs, meta)

    def ask(self, question: str, only_programs: Optional[List[str]] = None) -> Tuple[str, float]:
        q = self.vectorizer.transform([_norm(question)])
        sims = cosine_similarity(q, self.matrix).ravel()
        if only_programs:
            mask = [i for i,(pk,_) in enumerate(self.meta) if pk in only_programs]
        else:
            mask = list(range(len(self.meta)))
        if not mask:
            return "Нет данных по выбранной программе.", 0.0
        best = sorted(((sims[i], i) for i in mask), reverse=True)[:TOP_K]
        best_score = best[0][0]
        if best_score < RELEVANCE_THRESHOLD:
            return "Этот вопрос не относится к выбранным программам. Задайте вопрос об обучении, программах, курсе, сроках, дисциплинах и т.п.", float(best_score)
        answer_parts = [self.chunks[i].strip() for _, i in best]
        answer = "\n\n".join(answer_parts)
        return answer, float(best_score)