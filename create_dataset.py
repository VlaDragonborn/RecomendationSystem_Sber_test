import json
import random
import numpy as np

random.seed(42)
np.random.seed(42)

NUM_SESSIONS = 1200
MIN_LEN = 3
MAX_LEN = 15
NUM_ITEMS = 500

themes = {
    "office_supplies": list(range(1, 31)),        # товары 1–30
    "electronics": list(range(101, 151)),         # 101–150
    "books": list(range(201, 241)),               # 201–240
    "clothing": list(range(301, 351)),            # 301–350
    "home_decor": list(range(401, 451)),          # 401–450
}

def generate_session():
    # С вероятностью 0.7 сессия следует тематике (последовательные группы)
    if random.random() < 0.7:
        theme_name = random.choice(list(themes.keys()))
        theme_items = themes[theme_name][:]
        random.shuffle(theme_items)
        length = random.randint(MIN_LEN, min(MAX_LEN, len(theme_items)))
        session = theme_items[:length]
    else:
        # Случайные товары из всего каталога
        length = random.randint(MIN_LEN, MAX_LEN)
        session = random.sample(range(1, NUM_ITEMS + 1), length)
    
    # Добавляем немного "шума" — редких товаров, которые повторяются
    if random.random() < 0.3:
        # Вставляем повтор последнего товара (имитация уточнения)
        session.append(session[-1])
    
    # Иногда копируем блок внутри сессии (популярная цепочка)
    if random.random() < 0.2 and len(session) > 3:
        start = random.randint(0, len(session)-3)
        end = start + random.randint(1, 3)
        session.extend(session[start:end])
    
    # Обрезаем до MAX_LEN после дополнений
    return session[:MAX_LEN]

sessions = [generate_session() for _ in range(NUM_SESSIONS)]

with open("generated_sessions.jsonl", "w", encoding="utf-8") as f:
    for sess in sessions:
        f.write(json.dumps(sess, ensure_ascii=False) + "\n")