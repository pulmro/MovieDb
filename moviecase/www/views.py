from flask import render_template, request, redirect, url_for, abort


import logging
import tmdb3
import sys
from ..models import Movie, File, ORPHAN_FILE, REMOVED_FILE
from ..database import db_session
from .. import db_methods
from .. import config
from . import app
from exceptions import MovieDbError, DbConnectionError, DbError

try:
    from flask import _app_ctx_stack as stack
    GREATER09 = True
    print "Flask is >= 0.9"
except ImportError:
    print "Flask is < 0.9. Upgrade your Flask installation."
    print "Exiting..."
    sys.exit()


def init_tmdb():
    tmdb3.set_key(config.cfg['API_KEY'])
    tmdb3.set_cache(engine='file', filename=config.cfg['CACHEPATH']+'/.tmdb3cache')
    tmdb3.set_locale(config.cfg['LANG'], config.cfg['COUNTRY'])


@app.teardown_appcontext
def close_db_connection(exception):
    """Closes the database again at the end of the request."""
    db_session.remove()


@app.route('/')
@app.route('/index')
def index():
    latestmovies = db_methods.get_latest_movies(5)
    movies = []
    if request.args:
        sort = request.args['sort']
        if sort == 'year':
            movies = db_methods.get_movies(sort='title')
        elif sort == 'title':
            movies = db_methods.get_movies(sort='year')
    else:
        movies = db_methods.get_movies(sort='title')
    return render_template("index.html", latestmovies=latestmovies, allmovies=movies)


@app.route('/editmovie')
def editmovie():
    try:
        movie_id = int(request.args['id'])
    except:
        raise MovieDbError("Bad request. Check your parameters.", 400)
    try:
        movie = db_methods.get_movie(movie_id)
    except db_methods.NoMovieFound:
        abort(404)
    return render_template("editmovie.html", movie=movie)


@app.route('/files')
def files():
    shortlistmovies = db_methods.get_movies()
    orphanfiles = db_methods.get_orphan_files()
    removedfiles = db_methods.get_removed_files()
    moviefiles = db_methods.get_bound_files()
    return render_template("files.html", shortlistmovies=shortlistmovies, orphanfiles=orphanfiles,
                           removedfiles=removedfiles, moviefiles=moviefiles)


@app.route('/cerca', methods=['GET', 'POST'])
def cerca():
    if request.method == 'POST':
        mid = int(request.form['id']) if 'id' in request.form else 0
        fid = int(request.form['fid']) if 'fid' in request.form else 0
        query = request.form['query'] if 'query' in request.form else ""
        try:
            init_tmdb()
            resplist = tmdb3.searchMovie(query.encode('utf-8'))
            res = [Movie.from_tmdb(the_movie, False) for the_movie in resplist]
        except tmdb3.tmdb_exceptions.TMDBHTTPError as e:
            logging.error("HTTP error({0}): {1}".format(e.httperrno, e.response))
            raise MovieDbError("HTTP error({0}): {1}".format(e.httperrno, e.response))
        except:
            logging.error("Unexpected error: %s", sys.exc_info()[0])
            raise MovieDbError("Unexpected error: %s", sys.exc_info()[0])
        return render_template("cerca.html", movieid=mid, fileid=fid, results=res)


@app.route('/edit', methods=['POST'])
def edit():
    if request.method == 'POST':
        tmdbID = int(request.form['choice']) if 'choice' in request.form else -1
        mid = int(request.form['id']) if 'id' in request.form else 0
        fid = int(request.form['fid']) if 'fid' in request.form else 0
        final_movieid = mid
        if fid > 0:
            file = File.query.get(fid)
            if mid > 0:
                file.movieid = mid
            else:
                the_movie = tmdb3.Movie(tmdbID)
                final_movieid = db_methods.insert_movie_file(the_movie, file.filepath, file.name)
        else:
            movie = Movie.query.filter(Movie.tmdbID == tmdbID).first()
            if movie and movie.movieid != mid:
                final_movieid = movie.movieid
            else:
                try:
                    the_movie = tmdb3.Movie(tmdbID)
                    final_movieid = db_methods.insert_movie(the_movie)
                except tmdb3.tmdb_exceptions.TMDBHTTPError as e:
                    logging.error("HTTP error({0}): {1}".format(e.httperrno, e.response))
                    raise MovieDbError("HTTP error({0}): {1}".format(e.httperrno, e.response))
                except:
                    logging.error("Unexpected error: %s", sys.exc_info()[0])
                    raise MovieDbError("Unexpected error: %s", sys.exc_info()[0])
            File.query.filter(File.movieid == mid).update({"movieid": final_movieid})
            Movie.query.filter(Movie.movieid == mid).delete()
        try:
            db_session.commit()
        except:
            db_session.rollback()
        return redirect(url_for('editmovie', id=final_movieid))


@app.route('/delete_movie', methods=['GET'])
def delete():
    try:
        mid = int(request.args['id'])
    except:
        raise MovieDbError("Bad request. Check your parameters.", 400)
    Movie.query.filter(Movie.movieid == mid).delete()
    try:
        db_session.commit()
    except:
        db_session.rollback()
    return redirect(url_for('index'))


@app.route('/delete_file', methods=['GET'])
def delete_file():
    try:
        fid = int(request.args['fid'])
    except:
        raise MovieDbError("Bad request. Check your parameters.", 400)
    try:
        File.query.get(fid).set_removed()
        db_session.commit()
    except:
        db_session.rollback()
    return files()


@app.route('/set_orphan')
def set_orphan():
    try:
        file_id = request.args['fid']
    except:
        raise MovieDbError("Bad request. Check your parameters.", 400)
    try:
        File.query.get(file_id).set_orphan()
        db_session.commit()
    except:
        db_session.rollback()
    return files()


@app.errorhandler(MovieDbError)
def bad_request(error):
    return render_template('400.html', message=error.message), 400


@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404


@app.errorhandler(DbError)
def internal_error(error):
    db_session.rollback()
    return render_template('500.html', message=error.message), 500


@app.errorhandler(DbConnectionError)
def db_connection_error(error):
    return render_template('500.html', message=error.message), 500