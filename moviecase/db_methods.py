from sqlalchemy.orm.exc import NoResultFound
from models import Movie, File, ORPHAN_FILE, REMOVED_FILE
from database import db_session


def insert_movie(the_movie):
    movie = Movie.from_tmdb(the_movie, True)
    db_session.add(movie)
    try:
        db_session.commit()
        return movie.movieid
    except:
        db_session.rollback()
        raise


def insert_movie_file(the_movie, path, movie_name):
    """
    Checks if movie and file are already in the database and updates relationship, else it adds new ones.
    """
    try:
        movie = db_session.query(Movie).filter(Movie.tmdbID == the_movie.id).one()
    except NoResultFound:
        movie = Movie.from_tmdb(the_movie)
        db_session.add(movie)
        db_session.commit()
    try:
        file = db_session.query(File).filter(File.filepath == path).one()
    except NoResultFound:
        file = File(filpath=path, name=movie_name, movieid=movie.movieid)
        db_session.add(file)
    else:
        file.movieid = movie.movieid
    try:
        db_session.commit()
        return movie.movieid
    except:
        db_session.rollback()
    return None


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


def get_latest_movies(limit):
    statement = db_session.query(File).group_by(File.movieid).order_by('id DESC').limit(limit).subquery()
    return db_session.query(Movie).join(statement, Movie.movieid == statement.c.movieid).all()


def get_movies(page=0, sort='title'):
    if page > 0:
        return db_session.query(Movie).order_by(sort).slice(20*(page-1), 20*page).all()
    else:
        return db_session.query(Movie).order_by(sort).all()


def get_movie(movie_id):
    try:
        movie = db_session.query(Movie).filter(Movie.movieid == movie_id).one()
    except NoResultFound:
        raise NoMovieFound("Movie with %d id not found" % movie_id)
    return movie


def get_orphan_files():
    return db_session.query(File).filter(File.movieid == ORPHAN_FILE).all()


def get_removed_files():
    return db_session.query(File).filter(File.movieid == REMOVED_FILE).all()


def get_bound_files():
    return db_session.query(File).filter(File.movieid > 0).join("movie").all()


def get_count_pages():
    return Movie.query.count()//20 + 1


class NoMovieFound(Exception):
    def __init__(self, message):
        Exception.__init__(self)
        self.message = message