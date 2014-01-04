from sqlalchemy.orm.exc import NoResultFound
from models import Movie, File, ORPHAN_FILE
from database import db_session


def insert_movie(the_movie, path, movie_name):
    try:
        movie = db_session.query(Movie).filter(Movie.tmdbID == the_movie.id).one()
    except NoResultFound:
        movie = Movie.from_tmdb(the_movie)
        db_session.add(movie)
        db_session.commit()
    file = File(filpath=path, name=movie_name, movieid=movie.movieid)
    db_session.add(file)
    try:
        db_session.commit()
    except:
        db_session.rollback()


def insert_orphan_file(path, movie_name):
    file = File(filpath=path, name=movie_name, movieid=ORPHAN_FILE)
    db_session.add(file)
    try:
        db_session.commit()
    except:
        db_session.rollback()


def update_movie(tmdb_id, movie):
    db_session.query(Movie).filter(Movie.tmdbID == tmdb_id).update({"title": movie.title,
                                                                    "director": movie.director,
                                                                    "cast": movie.cast,
                                                                    "overview": movie.overview,
                                                                    "runtime": movie.runtime,
                                                                    "year": movie.year,
                                                                    "morandini": movie.morandini})