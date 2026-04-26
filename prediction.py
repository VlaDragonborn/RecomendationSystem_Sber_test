import json
import os
import matplotlib.pyplot as plt
from collections import defaultdict
from collections import Counter

FILENAME = "sessions.jsonl"

def train_test_split(
    sessions: list[list[int]],
) -> tuple[list[list[int]], list[int]]:
    train_sessions = [session[:-1] for session in sessions]
    test_targets = [session[-1] for session in sessions]
    return train_sessions, test_targets

def hit_at_k(
    recommendations: list[list[int]],
    true_items: list[int],
    k: int = 10,
) -> float:
    assert len(recommendations) == len(true_items)
    hits = 0
    for recs, true_item in zip(recommendations, true_items):
        if true_item in recs[:k]:
            hits += 1

    return hits / len(true_items)

# %%% Тривиальный подход %%%
# Если по алгоритму набирается меньше 10 наиболее веротных вариантов 
# мы добавляем самые популярные варианты на оставшиеся места 
def strategy_1( last_id: int,
                markov_tree: dict[int, dict[int, float]],
                top10: dict[int, float]):

    prediction = dict(list(markov_tree[last_id].items())[:10])
    prediction = list(prediction.keys())
    if len(prediction) < 10: 
        prediction += list(top10.keys())[:(10-len(prediction))] 

    return prediction[:10]

# %%% Всегда беру наибольшую вероятность %%% 
# Объединяю прогноз со статистикой и сохраяню только наибольшее
# (провалился на больших данных)
def strategy_2( last_id: int,
                markov_tree: dict[int, dict[int, float]],
                top10: dict[int, float]):

    prediction = dict(list(markov_tree[last_id].items())[:10])  
    recomendation = {p: max(top10.get(p, 0), prediction.get(p, 0)) 
                     for p in set(prediction) | set(top10)}
    recomendation = dict(sorted(recomendation.items(), key=lambda item: item[1], reverse=True))
    recomendation = list(recomendation.keys())[:10]

    return recomendation[:10]

# %%% Тривиальный вариант V2%%%
# Аналогичен тривиальному, однако будет проверять на повторы
# в теории вероятность попадания должна увеличиться 
def strategy_3( last_id: int,
                markov_tree: dict[int, dict[int, float]],
                top10: dict[int, float]):
    
    statistics = list(top10.keys())
    prediction = dict(list(markov_tree[last_id].items())[:10])
    recomendation = list(prediction.keys())

    for ind in range(10):
        if statistics[ind] not in prediction.keys():
            recomendation.append(statistics[ind])

    return recomendation[:10]

    print(recomendation)

# %%% Тривиальный вариант V3 %%% 
# По возможности буду исключать last_id из результатов
def strategy_4( last_id: int,
                markov_tree: dict[int, dict[int, float]],
                top10: dict[int, float]):

    prediction = dict(list(markov_tree[last_id].items())[:10])

    statistics = list(top10.keys())
    prediction = list(prediction.keys())

    if last_id in list(prediction) and len(markov_tree[last_id]) >= 11:
        ind = prediction.index(last_id)
        prediction[ind] = list(markov_tree[last_id].items())[10]

    recomendation = prediction

    for ind in range(10):
        if statistics[ind] not in prediction and statistics[ind] != last_id:
            recomendation.append(statistics[ind])

    
    return recomendation[:10]

# %%% Цепи мароква второго порядка %%%
# Алгоритм будет сравнивать пару чисел и следующее за ними, если такой закономерности нет,
# то алгоритм будет считать как для цепей первого порядка
def strategy_5( last_couple: tuple[int, int],
                markov_tree: dict[int, dict[int, float]],
                markov_tree_2nd: dict[tuple[int, int], dict[int, float]],
                top10: dict[int, float]):

    prediction = dict(list(markov_tree_2nd[last_couple].items())[:10])
    prediction = list(prediction.keys())

    if len(prediction) < 10:
        prediction_1st = list(markov_tree[last_couple[1]].keys())[:10]
        
        for item in prediction_1st:
            if item not in prediction:
                prediction.append(item)
    
    if len(prediction) < 10:
        prediction_top10 = list(top10.keys())[:10]

        for item in prediction_top10:
            if item not in prediction:
                prediction.append(item)

    return prediction[:10]

# %%% Цепи Маркова Второго порядка V2 %%%
# Я попробую сначала брать предикт цепей перовго порядка, затем добавлять 
# предикт второго, если есть место и в последнюю очередь топ10
def strategy_6( last_couple: tuple[int, int],
                markov_tree: dict[int, dict[int, float]],
                markov_tree_2nd: dict[tuple[int, int], dict[int, float]],
                top10: dict[int, float]):

    prediction = dict(list(markov_tree[last_couple[1]].items())[:10])
    prediction = list(prediction.keys())

    if len(prediction) < 10:
        prediction_2nd = list(markov_tree_2nd[last_couple].keys())[:10]
        
        for item in prediction_2nd:
            if item not in prediction:
                prediction.append(item)

    if len(prediction) < 10:
        prediction_top10 = list(top10.keys())[:10]

        for item in prediction_top10:
            if item not in prediction:
                prediction.append(item)

    return prediction[:10]

# Выводим статистику
def get_stat(history: list[int], frequency: dict):

    plot_dir = "plots"
    os.makedirs(plot_dir, exist_ok=True)

    # График частоты появления каждого ID во всех сессиях
    IDs = list(frequency.keys())
    Freq = list(frequency.values())
    plt.bar(IDs, Freq)
    plt.title('Частота появления ID')
    plt.ylabel('Частота')
    plt.xlabel('ID')
    plt.savefig(os.path.join(plot_dir, 'ID-Frequency'))
    plt.close()

    # Топ 10 самых частых ID и их количество
    sorted_frequency = sorted(frequency.items(), key=lambda item: item[1], reverse=True)[:10]
    IDs = [str(item[0]) for item in sorted_frequency]
    Freq = [item[1] for item in sorted_frequency]
    plt.bar(IDs, Freq)
    plt.title('Самые частые ID')
    plt.ylabel('Количество')
    plt.xlabel('ID')
    plt.savefig(os.path.join(plot_dir, 'ID-Sorted_Frequency'))
    plt.close()

    # Распределение длинн сессий
    session_lens = [len(session) for session in history]
    
    plt.hist(session_lens)
    plt.title('Длинна сессий')
    plt.xlabel('Длинна сесии')
    plt.ylabel('Число сессий')
    plt.savefig(os.path.join(plot_dir, 'Session-len'))
    plt.close()

    # Уникальные ID и среднее число дубликатов
    all_items = [item for session in history for item in session]
    unique_items = set(all_items)
    duplicates = []

    for session in history:
        duplicates.append(len(session)-len(set(session)))

    average_duplicate_count = sum(duplicates)/len(duplicates)

    # Найдём самые популярные пары чисел
    all_pairs = Counter()

    for session in history:
        for item in range(len(session) - 1):
            pair = (session[item], session[item+1])
            all_pairs[pair] += 1

    all_pairs = sorted(all_pairs.items(), key=lambda item: item[1], reverse=True)[:20]
    
    x_pair = [f'{pair[0]}->{pair[1]}' for pair, count in all_pairs]
    y_freq = [count for pair, count in all_pairs]
    plt.figure(figsize=(12, 6))
    plt.bar(x_pair, y_freq)
    plt.title('Самые частые пары')
    plt.xlabel('Пары ID')
    plt.xticks(rotation=45)
    plt.ylabel('Количесвто встреч')
    plt.tight_layout()
    plt.savefig(os.path.join(plot_dir, 'Pairs'))
    plt.close()

    print(f'''    Статистика по обучающей истории из файла "{FILENAME}"
Количество сессий: {len(history)}
Средняя длиина сессии: {sum(session_lens)/len(session_lens)}
Число уникальных ID: {len(unique_items)}
Среднее число повторов за сессию {average_duplicate_count}
---
В папке plots, созданной в текущей дирректории, вы можете посмотреть некотоые графики
На которые я ссылаюсь для анализа
''')
    pass

def main():
    sessions = []
    frequency_id = {}

    with open(FILENAME) as f:                   # Чтение данных из файла
        for line in f:
            line = line.strip()
            if line:
                sessions.append(json.loads(line))

    train_space = train_test_split(sessions)
    history = train_space[0]
    targets = train_space[1]

    for session in history:                     # Пробег по данным для вывления частоты и самых популярных id
        for id in session:
            frequency_id[id] = frequency_id.get(id, 0) + 1

    sorted_frequency_id = dict(sorted(frequency_id.items(), key=lambda item: item[1], reverse=True))

    get_stat(history, frequency_id)

    # Вычисление вероятности 10 самых популярных ID 
    total_id_number = len(sorted_frequency_id)
    top10_id_probability = {id: sorted_frequency_id[id]/total_id_number for id in list(sorted_frequency_id.keys())[:10]}

    sequence_graph = defaultdict(list)          # граф содержащий информацию о смежных вершинах
    probability_graph = defaultdict(dict)       # граф аналогичный sequence_graph а так же содержащий веса рёбер
    all_ids = set()                             # Вспомогательное множество для коректной записи вершин в словарь

    #Запись значений в граф (для цепей мароква 1го порядка)
    for session in history:
        for index in range(len(session)-1):
            curent_id = session[index] 
            next_id = session[index+1]
            sequence_graph[curent_id].append(next_id)
            all_ids.add(curent_id)
        all_ids.add(session[-1])


    sequence_graph_2nd = defaultdict(list)         # Эти графы аналогичны предыдущим, но для
    probability_graph_2nd = defaultdict(list)      # цепей Маркова второго порядка
    all_couple_id = set()

    for session in history:
        for index in range(len(session)-2):
            context = (session[index], session[index+1])
            next_id = session[index+2]
            sequence_graph_2nd[context].append(next_id)
            all_couple_id.add(context)
        all_couple_id.add((session[-2], session[-1]))

    # Добавление неизвестных крайних вершин, у которых нет следующей вершины
    # для них следующими вершинами я считаю топ-10 самых популярных ID
    for item_id in all_ids:
        if item_id not in sequence_graph:
            sequence_graph[item_id] = [-1]

    for couple in all_couple_id:
        if couple not in sequence_graph_2nd:
            sequence_graph_2nd[couple] = [-1]

    sequence_graph = dict(sequence_graph)
    sequence_graph_2nd = dict(sequence_graph_2nd)

    # Создание графа с весами рёбер(Цепи Маркова)
    for vertex in sequence_graph:
        neighbours = sequence_graph[vertex]
        
        if neighbours == [-1]:
            probability_graph[vertex] = top10_id_probability
        else:
            count = 0
            probability_dict = defaultdict(int)
            for item in neighbours:
                probability_dict[item] += 1
                count += 1

            probability_dict = dict(sorted(probability_dict.items(), key=lambda item: item[1], reverse=True))
            
            for key in probability_dict:
                probability_dict[key] = probability_dict[key]/count
            
            probability_graph[vertex] = dict(probability_dict)

    markov_tree = dict(probability_graph)

    for couple in sequence_graph_2nd:
        neighbours = sequence_graph_2nd[couple]

        if neighbours == [-1]:
            probability_graph_2nd[couple] = markov_tree[couple[1]]

        else:
            count = 0
            probability_dict = defaultdict(int)
            for item in neighbours:
                probability_dict[item] += 1
                count += 1

            probability_dict = dict(sorted(probability_dict.items(), key=lambda item: item[1], reverse=True))
            
            for key in probability_dict:
                probability_dict[key] = probability_dict[key]/count

            probability_graph_2nd[couple] = dict(probability_dict)
        
    markov_tree_2nd = dict(probability_graph_2nd)

    # Вычисляем успешеность по метрике Hit@10
    recomendations_1 = []      # Массивы для рекомендаций по стратегиям
    recomendations_2 = []
    recomendations_3 = []
    recomendations_4 = []
    recomendations_5 = []
    recomendations_6 = []
    stat_recomend = []         # Массив для топ10 товаров


    for index in range(len(targets)):
        last_id = history[index][-1]       # Элемент для предсказания по цепям Маркова
        last_couple = (history[index][-2], 
                    history[index][-1]) # Пара для предсказания по цепям Маркова 2го порядка

        recomendations_1.append(strategy_1(last_id, markov_tree, top10_id_probability))
        recomendations_2.append(strategy_2(last_id, markov_tree, top10_id_probability))
        recomendations_3.append(strategy_3(last_id, markov_tree, top10_id_probability))
        recomendations_4.append(strategy_4(last_id, markov_tree, top10_id_probability))
        
        recomendations_5.append(strategy_5(last_couple, markov_tree, markov_tree_2nd, top10_id_probability))
        recomendations_6.append(strategy_6(last_couple, markov_tree, markov_tree_2nd, top10_id_probability))

        stat_recomend.append(list(top10_id_probability.keys()))


    Hit_recomendation_1 = hit_at_k(recommendations = recomendations_1, 
                                true_items= targets,
                                k = 10)

    Hit_recomendation_2 = hit_at_k(recommendations = recomendations_2, 
                                true_items= targets,
                                k = 10)

    Hit_recomendation_3 = hit_at_k(recommendations = recomendations_3, 
                                true_items= targets,
                                k = 10)

    Hit_recomendation_4 = hit_at_k(recommendations = recomendations_4, 
                                true_items= targets,
                                k = 10)

    Hit_recomendation_5 = hit_at_k(recommendations = recomendations_5, 
                                true_items= targets,
                                k = 10)

    Hit_recomendation_6 = hit_at_k(recommendations = recomendations_6, 
                                true_items= targets,
                                k = 10)


    Hit_statistics = hit_at_k(recommendations = stat_recomend, 
                                true_items= targets,
                                k = 10)

    print(f'''   Результат работы различных стратегий
Подробнее о стратегиях можно узнать из коментариев в коде
или в файле "Работа рекомендательной системы.txt"

Hit@10 для стртагии: 
Для top10 {Hit_statistics:.5f}
1) {Hit_recomendation_1:.5f} -- Самые популярные соседи + Топ 10 на оставшиеся места
2) {Hit_recomendation_2:.5f} -- (Самые популярные соседи + Топ 10), берём самые большие вероятности
3) {Hit_recomendation_3:.5f} -- (1) + Обработка повторений ID в поплярных соседях и топ 10
4) {Hit_recomendation_4:.5f} -- (2) + Исключение вершины по которой прогнозируем из рекомендаций 
5) {Hit_recomendation_5:.5f} -- Самые популярные соседи для пары чисел + заполнение свободного места
6) {Hit_recomendation_6:.5f} -- Сначала самые популярные соседи + самые популярные соседи пары чисел на оставшееся место
---
Лучшая стратегия по Hit@10: {max(Hit_recomendation_1,
                                 Hit_recomendation_2,
                                 Hit_recomendation_3,
                                 Hit_recomendation_4,
                                 Hit_recomendation_5,
                                 Hit_recomendation_6):.5f}

Небольшой вывод о результатах так же будет в файле с описанием работы''')

if __name__ == "__main__":
    main()