import json
from pathlib import Path
import requests
from bs4 import BeautifulSoup


def get_movies(url):
    response = requests.get(url)
    # Запрос данных
    soup = BeautifulSoup(response.text, "lxml")
    # Собираем все теги с нужными данными
    films = list(soup.find_all("div", {"class": "redesign_afisha_movie"}))
    for film in films:
        # Выделяем главный div в отдельную переменную для дальнейшей читабельности
        main_div = film.find("div", {"class": "redesign_afisha_movie_main"})
        # Получаем название, сразу форматируя строку от лишних пробелов
        film_name = str(main_div.find("a").text).replace("\n                ", "").replace("\n", "")
        # Получаем адрес страницы с фильмом
        film_url = f'{base_url}{main_div.find("a")["href"]}'
        # Выделяем описание в отдельную переменную для дальнейшей обработки
        film_ms0 = str(main_div.find("div", {"class": "redesign_afisha_movie_main_subtitle"}).text)
        film_ms1 = film_ms0.replace("\n                ", " / ").replace("\n", "")
        film_ms2 = film_ms1.replace("                        ", " / ")
        # Получаем оригинальное название
        original_name = film_ms2.split(" / ")[0]
        # Получаем дату выхода
        release = film_ms2.split(" / ")[1].replace("                  ", "")
        # Получаем возрастное ограничение
        try:
            age_limit = film_ms2.split(" / ")[2]
        except IndexError:
            age_limit = "Нет данных"
        # Выделяем div с классом "redesign_afisha_movie_main_info" в отдельную переменную
        film_mi = main_div.find("div", {"class": "redesign_afisha_movie_main_info"}).text
        # Получаем жанр фильма
        film_genre = film_mi.split(" / ")[0]
        # Получаем страну производства
        try:
            film_country = film_mi.split(" / ")[1]
        except IndexError:
            film_country = "Нет данных"
        # Выделяем тег "redesign_afisha_movie_main_rating"
        film_rating = main_div.find("div", {"class": "redesign_afisha_movie_main_rating"})
        # Чтобы корректно получить рейтинги на данном сайте, понадобилось собирать их в словарь. Иначе есть риск
        # получить разные рейтинги, тк может съехать таблица, или измениться сайт
        ratings_list = list(film_rating.find_all("div"))
        ratings_dict = {}
        for rating in ratings_list:
            rating_name = str(rating.text).replace("\n", "").replace("  ", "").split(":")[0]
            ratings_dict[rating_name] = rating.find("span").text
        data = {"title": film_name,
                "url": film_url,
                "original_name": original_name,
                "release": release,
                "age_limit": age_limit,
                "genre": film_genre,
                "country": film_country,
                "rating": ratings_dict}
        all_data.append(data)


# Базовый адрес сайта
base_url = "https://www.film.ru"
# Адрес первой страницы с фильмами
first_pages_url = "/a-z/movies"
# Адрес для пагинации
page_url = "/nojs?page="
pages = range(2, 11)
all_data = []
get_movies(base_url + first_pages_url)

for page in pages:
    urle = f'{base_url}{first_pages_url}{page_url}{page}'
    get_movies(urle)

with open(Path(Path.cwd(), "all_data.json"), 'w', encoding="utf-8") as f:
    json.dump(all_data, f, indent=4, ensure_ascii=False)

print(len(all_data))
