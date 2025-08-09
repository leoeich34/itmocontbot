from __future__ import annotations
import argparse, json, sys
from .scrape import ingest, load_or_ingest
from .module_nlp import QAEngine
from .config import DEFAULT_URLS
from .recom import recommend_courses

def cmd_ingest(args):
    data = ingest(DEFAULT_URLS)
    print(f"OK. Saved {sum(len(v['text_chunks']) for v in data.values())} chunks.")

def cmd_ask(args):
    programs = load_or_ingest()
    qa = QAEngine.from_programs(programs)
    only = [args.program] if args.program else None
    ans, sc = qa.ask(args.question, only_programs=only)
    print(f"[score={sc:.3f}]")
    print(ans)

def cmd_recommend(args):
    programs = load_or_ingest()
    key = args.program
    if key not in programs:
        print(f"Unknown program key: {key}. Use one of: {', '.join(programs.keys())}")
        sys.exit(1)
    top, scored = recommend_courses(programs[key], args.skills, top_n=args.top)
    print(f"Рекомендованные дисциплины ({key}):")
    for i, c in enumerate(top, 1):
        print(f"{i}. {c}")
    if args.verbose:
        print("\nТоп-20 по внутреннему скору:")
        for c, sc in scored:
            print(f"{sc:2d}  {c}")

def cmd_compare(args):
    programs = load_or_ingest()
    ai_len = len(programs["ai"]["text_chunks"])
    aip_len = len(programs["ai_product"]["text_chunks"])
    print("Сравнение программ:")
    print(f"- AI:          {ai_len} текстовых фрагментов, ~{len(programs['ai']['courses'])} извлечённых дисциплин")
    print(f"- AI Product:  {aip_len} текстовых фрагментов, ~{len(programs['ai_product']['courses'])} извлечённых дисциплин")

def main():
    p = argparse.ArgumentParser(prog="itmo-chooser CLI")
    sub = p.add_subparsers(required=True)

    s1 = sub.add_parser("ingest", help="спарсить страницы и PDF учебных планов")
    s1.set_defaults(func=cmd_ingest)

    s2 = sub.add_parser("ask", help="задать вопрос по программам")
    s2.add_argument("question")
    s2.add_argument("--program", choices=["ai","ai_product"])
    s2.set_defaults(func=cmd_ask)

    s3 = sub.add_parser("recommend", help="подобрать элективы по бэкграунду")
    s3.add_argument("--program", required=True, choices=["ai","ai_product"])
    s3.add_argument("--skills", required=True, help="через запятую: python,ml,math,nlp,cv,pm,se,ds")
    s3.add_argument("--top", type=int, default=7)
    s3.add_argument("--verbose", action="store_true")
    s3.set_defaults(func=cmd_recommend)

    s4 = sub.add_parser("compare", help="краткое сравнение программ")
    s4.set_defaults(func=cmd_compare)

    args = p.parse_args()
    args.func(args)

if __name__ == "__main__":
    main()