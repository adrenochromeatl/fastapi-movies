from fastapi import FastAPI, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from database import engine, get_db
import requests
from bs4 import BeautifulSoup
from models import Base, Movie

app = FastAPI()

# Создание таблиц
Base.metadata.create_all(bind=engine)

# Подключение статических файлов
app.mount("/static", StaticFiles(directory="static"), name="static")

# Базовый адрес сайта
base_url = "https://www.film.ru"
# Адрес первой страницы с фильмами
first_pages_url = "/a-z/movies"
# Адрес для пагинации
page_url = "/nojs?page="
pages = range(1, 21)


def get_movies_site(url: str, db: Session):
    print(f"Полученный URL: {url}")
    print(f"Тип объекта db: {type(db)}")
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "lxml")
    films = list(soup.find_all("div", {"class": "redesign_afisha_movie"}))

    movies = []
    for film in films:
        main_div = film.find("div", {"class": "redesign_afisha_movie_main"})
        title = str(main_div.find("a").text).replace("\n                ", "").replace("\n", "")
        film_url = f'{base_url}{main_div.find("a")["href"]}'
        film_ms0 = str(main_div.find("div", {"class": "redesign_afisha_movie_main_subtitle"}).text)
        film_ms1 = film_ms0.replace("\n                ", " / ").replace("\n", "")
        film_ms2 = film_ms1.replace("                        ", " / ")
        original_name = film_ms2.split(" / ")[0]
        release = str(film_ms2.split(" / ")[1].replace("                  ", ""))

        try:
            age_limit = film_ms2.split(" / ")[2]
        except IndexError:
            age_limit = "Нет данных"

        film_mi = main_div.find("div", {"class": "redesign_afisha_movie_main_info"}).text
        genre = film_mi.split(" / ")[0]

        try:
            country = film_mi.split(" / ")[1]
        except IndexError:
            country = "Нет данных"

        film_rating = main_div.find("div", {"class": "redesign_afisha_movie_main_rating"})
        ratings_list = list(film_rating.find_all("div"))
        ratings_dict = {}

        for rating in ratings_list:
            rating_name = str(rating.text).replace("\n", "").replace("  ", "").split(":")[0]
            ratings_dict[rating_name] = rating.find("span").text

        movie = Movie(
            title=title,
            url=film_url,
            original_name=original_name,
            release=release,
            age_limit=age_limit,
            genre=genre,
            country=country,
            rating_film_ru=ratings_dict["film.ru"],
            rating_spectators=ratings_dict["зрители"],
            rating_IMDb=ratings_dict["IMDb"]
        )

        db.add(movie)
        movies.append(movie)

    db.commit()  # Коммитим после добавления всех фильмов
    return movies  # Возвращаем все фильмы


# Эндпоинт для главной страницы
@app.get("/")
def read_root():
    return FileResponse("static/main.html")  # Укажите путь к вашему HTML-файлу


# Эндпоинт для загрузки фильмов
@app.post("/movies/load")
def load_movies(db: Session = Depends(get_db)):
    print("Начало загрузки фильмов")
    movies = []
    print(f"Вызов get_movies с URL: {base_url + first_pages_url}")
    movies.extend(get_movies_site(f"{base_url}{first_pages_url}", db))

    for page in range(2, 21):
        url = f'{base_url}{first_pages_url}{page_url}{page}'
        print(f"Вызов get_movies с URL: {url}")
        movies.extend(get_movies_site(url, db))

    # Сортировка по рейтингу IMDb
    movies_sorted = sorted(movies, key=lambda x: x.rating_IMDb, reverse=True)
    return movies_sorted


# Эндпоинт для получения всех фильмов
@app.get("/movies")
def get_movies(db: Session = Depends(get_db)):
    movies = db.query(Movie).all()
    return movies
