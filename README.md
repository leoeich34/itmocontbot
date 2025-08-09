# ITMO Contest Bot

Чат-бот, который:
1) парсит страницы двух магистерских программ ITMO + ссылки на PDF "Учебный план"; 
2) отвечает на вопросы по содержимому (офлайн TF-IDF, без внешних API); 
3) рекомендует элективы на основе вашего бэкграунда; 
4) жёстко отсекает нерелевантные запросы.

## Быстрый старт
```bash
pip install -r requirements.txt
python -m src.cli ingest
python -m src.cli ask "Какие направления есть в программе?"
python -m src.cli recommend --program ai --skills "python,ml,math"
cp .env.example .env   # вставьте токен
python -m src.bot