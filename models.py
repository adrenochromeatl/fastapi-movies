from sqlalchemy import Column, Integer, String, Float
from database import Base


class Movie(Base):
    __tablename__ = "movies"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    url = Column(String)
    original_name = Column(String)
    picture = Column(String)
    release = Column(String)
    age_limit = Column(String)
    genre = Column(String)
    country = Column(String)
    rating_film_ru = Column(String)
    rating_spectators = Column(String)
    rating_IMDb = Column(Float)


