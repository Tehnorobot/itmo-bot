import os
import requests
from typing import Dict, Optional, List
from tavily import TavilyClient
import json
from yandex_cloud_ml_sdk import YCloudML
import logging

logger = logging.getLogger(__name__)

logger.setLevel(logging.NOTSET)
logging.basicConfig(level=logging.NOTSET)  # Set logging level

INCLUDE_ANSWER = True
SEARCH_DEPTH = 'advanced'
MAX_RESULTS = 3


API_KEY_TAVILY = ''
AUTH = ''
FOLDER_ID = ''

sdk = YCloudML(
    folder_id=FOLDER_ID,
    auth=AUTH,
)

client = TavilyClient(api_key=API_KEY_TAVILY)

# Выполнение поиска с использованием Tavily
def search_with_tavily(query: str) -> List[Dict]:
    """
    Выполняет поиск по запросу с использованием клиента Tavily.
    :param client: Экземпляр клиента Tavily.
    :param query: Запрос для поиска.
    :return: Список результатов поиска.
    """
    try:
        response = client.search(query, include_answer=INCLUDE_ANSWER, search_depth=SEARCH_DEPTH, max_results=MAX_RESULTS)

        logger.info(f"response: {response}")
        # Проверяем, есть ли результаты поиска
        if response and 'results' in response:
            return response.get('results', [])
        else:
            return []
    except Exception as e:
        logger.info(f"Ошибка при поиске: {e}")
        return {}


# Формирование промпта для Yandex GPT
def create_messages(search_results: List[Dict], query: str) -> str:
    """
    Формирует промпт для модели на основе источника, ответа и вопроса.
    :param content: Извлечённый контент.
    :param answer: Ответ, предоставленный поисковой моделью.
    :param question: Вопрос пользователя.
    :return: Строка промпта.
    """

    text_for_system = f'''
    Ты пишешь ясный, точный и строго по шаблону ответ на запрос пользователя.
    Используя следующий источник:

    {'/n'.join([content.get('content', '') for content in search_results])}

    И возможный ответ на запрос пользователя:

    {search_results[0].get('answer', '')}

    В первую очередь, на основе вожможного ответа на запрос пользователя, а потом на основе контента ты пишешь ответ по шаблону.
    Условия answer:
    1) Если в запросе пользователя перечислены варианты ответов, то ты строго пишешь номер по счету верного ответа из предложенных и ничего более.
    2) Если в запросе пользователя нет вариантов ответов, то ответ.

    Шаблон, по которому ты строго следуешь в формате JSON:
    {{
        "answer": "Ответ на запрос пользователя, исходя из условий answer",
        "reasoning": "Пояснение, почему такой ответ ты выдал на строго только основе текста из источника без упоминания возможного ответа на запрос пользователя."
        "urls": []
    }}

    Пример, когда в запросе пользователя есть варианты ответов (...некий вопрос...\n1. 2007\n2. 2009\n3. 2011\n4. 2015):
    {{
        "answer": 2,
        "reasoning": "Университет ИТМО был включён в число Национальных исследовательских университетов России в 2009 году. Это подтверждается официальными данными Министерства образования и науки РФ.",
        "urls": ["https://itmo.ru/ru/", "https://abit.itmo.ru/"]
    }}


    Пример, когда в запросе пользователя нет вариантов ответа (...некий вопрос...):
    {{
        "answer": Ответ на вопрос,
        "reasoning": "В 2023 году Университет ИТМО впервые вошёл в топ-400 мировых университетов согласно рейтингу ARWU (Shanghai Ranking). Это достижение подтверждается официальным сайтом рейтинга",
        "urls": ["https://itmo.ru/ru/"]
    }}

    Если возможный ответ на запрос пользователя не содержит ответа, то формируй ответ без его учета и источника, сам ищи источники в интернете и ответ на запрос по найденным источникам. Эти источники должны обязятельно содержать валидную ссылку. Ссылки ты должен добавить в ключ "urls" в список.

    Самое главное требование: если у тебя в итоге ответа нет, то в answer пиши значение "null".

    Строго следуй моим требованиям.
    '''

    messages = [
        {
        "role": "system",
        "text": text_for_system,
        },
        {
            "role": "user",
            "text": query,
        }
    ]

    print(messages)


    return messages

# Использование Yandex GPT для генерации ответа
def generate_answer_with_yandex_gpt(messages: List[dict], temperature=0.7) -> str:

    return sdk.models.completions("yandexgpt").configure(temperature=temperature).run(messages)

# Главная функция для обработки запроса
def process_query(query: str) -> Dict:
    """
    Обрабатывает запрос, используя Tavily для поиска и Yandex GPT для генерации ответа.
    :param api_key: API-ключ для Tavily.
    :param query: Запрос для поиска.
    :param question: Вопрос пользователя для генерации ответа.
    :return: Ответ в формате JSON: {'answer': str, 'reasoning': str, 'urls': List[str]}
    """

    query = 'Запрос по университету ИТМО: ' + query

    # Выполнение поиска
    search_results = search_with_tavily(query)

    # Создание промпта для Yandex GPT
    messages = create_messages(search_results, query)

    # Генерация ответа с помощью модели
    answer = generate_answer_with_yandex_gpt(messages)

    try:
        json_ans = json.loads(answer[0].text.replace('```', ''))
    except:
        json_ans = {}

    return json_ans