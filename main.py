import os
import random
import requests
import re
from fastapi import FastAPI, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from tqdm import tqdm
from bs4 import BeautifulSoup
from models import Base, Movie
from database import engine, get_db

app = FastAPI()

# Создание таблиц
Base.metadata.create_all(bind=engine)

# Подключение статических файлов
picture_dir = os.path.join(os.getcwd(), "pictures")
if not os.path.isdir(picture_dir):
    os.makedirs(picture_dir)
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/pictures", StaticFiles(directory=picture_dir), name="pictures")

# Адрес сайта для парсинга
base_url = "https://www.film.ru"
first_pages_url = "/a-z/movies"  # Адрес первой страницы с фильмами
page_url = "/nojs?page="  # Адрес для пагинации
pages = range(1, 1001)  # Страницы для парсинга, на одной странице хранится 30 фильмов


# Функция парсинга фильмов со страницы
def parsing_movies(url: str, db: Session):
    # Функция для загрузки обложек
    def download_picture(url_picture, name_picture, picture_dir=picture_dir):

        res = requests.get(url_picture, stream=True)
        file_size = int(res.headers.get('content-length', 0))
        ex = str(url_picture.split("/")[-1]).split(".")[-1]
        path_picture = os.path.join(picture_dir, f"{name_picture}.{ex}")

        # Проверяем значение переменной окружения
        use_progress = os.getenv('USE_PROGRESS_BAR', 'false').lower() == 'true'

        # Определяем, будем ли мы использовать tqdm для отображения прогресса
        progress = response.iter_content(1024)
        if use_progress:
            progress = tqdm(res.iter_content(1024), total=file_size, unit='B', unit_scale=True, unit_divisor=1024)

        with open(path_picture, 'wb') as f:
            for chunk in progress:
                f.write(chunk)

        picture_path = (path_picture.split("\\")[-2] + '/' + path_picture.split("\\")[-1])
        return picture_path

    def one_movie(movie_main):

        # Выделяем div с дополнительной информацией в отдельную переменную
        movie_main_subtitle = str(movie_main.find("div", {"class": "redesign_afisha_movie_main_subtitle"}).text)
        movie_main_subtitle = (movie_main_subtitle.replace("\n                ", " / ")
                               .replace("\n", "")
                               .replace("                        ", " / "))
        # Оригинальное название
        original_name = movie_main_subtitle.split(" / ")[0]
        # Дата выхода
        release = str(movie_main_subtitle.split(" / ")[1]).strip()
        # Название
        title = (str(movie_main.find("a").text).replace("\n                ", "")
                 .replace("\n", ""))
        title_save = title.replace(" ", "_").replace("/", "_")
        symbol_rep = r"[?!#$%^&*~>=+-,:.»«]"
        title_save = re.sub(symbol_rep, '', title_save)
        # Ссылка на оригинальную страницу
        film_url = f'{base_url}{movie_main.find("a")["href"]}'
        # Обложка
        picture_url = f'{base_url}{film.find("img")["src"]}'
        picture_name = download_picture(picture_url, name_picture=f'{title_save}_{release}')
        # Возрастное ограничение
        try:
            age_limit = movie_main_subtitle.split(" / ")[2]
        except IndexError:
            age_limit = "Нет данных"
        # Жанр
        genre = movie_main.find("div", {"class": "redesign_afisha_movie_main_info"}).text.split(" / ")[0]
        # Страна выхода
        try:
            country = movie_main.find("div", {"class": "redesign_afisha_movie_main_info"}).text.split(" / ")[1]
        except IndexError:
            country = "Нет данных"
        # Рейтинг фильма, заберем все 3 рейтинга, которые отдает сайт
        film_rating = movie_main.find("div", {"class": "redesign_afisha_movie_main_rating"})
        ratings_list = list(film_rating.find_all("div"))
        ratings_dict = {}
        # Словарь рейтингов
        for rating in ratings_list:
            rating_name = str(rating.text).replace("\n", "").replace("  ", "").split(":")[0]
            ratings_dict[rating_name] = rating.find("span").text
        # Строка для записи в бд
        movie = Movie(
            title=title,
            url=film_url,
            original_name=original_name,
            picture=picture_name,
            release=release,
            age_limit=age_limit,
            genre=genre,
            country=country,
            rating_film_ru=ratings_dict["film.ru"],
            rating_spectators=ratings_dict["зрители"],
            rating_IMDb=float(ratings_dict["IMDb"])
        )
        # Добавляем в бд
        db.add(movie)
        return movie

    response = requests.get(url)
    soup = BeautifulSoup(response.text, "lxml")

    # Собираем все элементы с классом "redesign_afisha_movie", тк в нем хранится вся информация о фильме
    films = list(soup.find_all("div", {"class": "redesign_afisha_movie"}))
    movies = []
    for film in films:
        # Выделяем основной div в отдельную переменную movie_main
        div_movie_main = film.find("div", {"class": "redesign_afisha_movie_main"})
        movie = one_movie(div_movie_main)
        movies.append(movie)

    db.commit()
    return movies


# Эндпоинт для главной страницы
@app.get("/", response_class=HTMLResponse)
def read_root():
    with open("static/main.html", encoding="UTF-8") as f:
        return HTMLResponse(content=f.read(), media_type="text/html")


# Эндпоинт для загрузки фильмов
@app.post("/load")
def load_movies(db: Session = Depends(get_db)):
    movies = []
    random_pages = random.sample(pages, 4)
    for page in random_pages:
        if page == 1:
            url = f"{base_url}{first_pages_url}{page}"
        else:
            url = f'{base_url}{first_pages_url}{page_url}{page}'
        movies.extend(parsing_movies(f"{url}", db))

    # Сортировка по рейтингу IMDb
    movies_sorted = sorted(movies, key=lambda x: x.rating_IMDb, reverse=True)
    return movies_sorted


# Эндпоинт для получения всех фильмов
@app.get("/movies")
def get_movies(db: Session = Depends(get_db)):
    movies = db.query(Movie).all()
    return movies
