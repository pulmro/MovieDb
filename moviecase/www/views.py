from flask import render_template, request, redirect, url_for, abort


import logging
import tmdb3
import sys

from ..mymovie import *
from ..sqliteiface import *
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


def get_db():
    """Opens a new database connection if there is none yet for the current application context."""
    top = stack.top
    if not hasattr(top, 'sqlite_db'):
        try:
            top.sqlite_db = sqlite_connect(config.cfg['DBFILE'], DICT_FACTORY)
        except sqlite3.OperationalError as e:
            raise DbConnectionError(e.message)
    return top.sqlite_db


def init_tmdb():
    tmdb3.set_key(config.cfg['API_KEY'])
    tmdb3.set_cache(engine='file', filename=config.cfg['CACHEPATH']+'/.tmdb3cache')
    tmdb3.set_locale(config.cfg['LANG'], config.cfg['COUNTRY'])


@app.teardown_appcontext
def close_db_connection(exception):
    """Closes the database again at the end of the request."""
    top = stack.top
    if hasattr(top, 'sqlite_db'):
        top.sqlite_db.close()


@app.route('/')
@app.route('/index')
def index():
    dbcon = get_db()
    latestmovies = get5LatestMovies(dbcon)
    movies = []
    if request.args:
        sort = request.args['sort']
        if sort == 'year':
            movies = getMoviesSortedByYear(dbcon, False)
        elif sort == 'title':
            movies = getMoviesSortedByTitle(dbcon, False)
    else:
        movies = getMoviesSortedByTitle(dbcon, False)
    return render_template("index.html", latestmovies=latestmovies, allmovies=movies)


@app.route('/editmovie')
def editmovie():
    movie_id = request.args['id']
    if movie_id:
        dbcon = get_db()
        movie = getMovieByID(dbcon, movie_id)
        files = [os.path.basename(file['filepath']) for file in getFilesByMovieID(dbcon, movie_id)]
        return render_template("editmovie.html", movie=movie, files=files)


@app.route('/files')
def files():
    dbcon = get_db()
    shortlistmovies = getMoviesSortedByTitle(dbcon, True)
    orphanfiles = get_orphan_files(dbcon)
    removedfiles = get_removed_files(dbcon)
    moviefiles = get_bounded_files(dbcon)
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
            res = [mymovieFromTmdb(tMovie, False) for tMovie in resplist]
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
        dbcon = get_db()
        if fid > 0:
            if mid > 0:
                boundFileWithMovie(dbcon, fid, mid)
            else:
                mMovie = mymovieFromTmdb(tmdb3.Movie(tmdbID), True)
                lastrowid = insertNewMovie(dbcon, mMovie)
                boundFileWithMovie(dbcon, fid, lastrowid)
                final_movieid = lastrowid
                mMovie.download_poster()
        else:
            movie = getmoviebyTMDbID(dbcon, tmdbID)
            if movie and movie['movieid'] != mid:
                updateBoundWithMovie(dbcon, mid, movie['movieid'])
                final_movieid = movie['movieid']
            else:
                try:
                    init_tmdb()
                    mMovie = mymovieFromTmdb(tmdb3.Movie(tmdbID), True)
                    lastrowid = insertNewMovie(dbcon, mMovie)
                    updateBoundWithMovie(dbcon, mid, lastrowid)
                    removeMovie(dbcon, mid)
                    final_movieid = lastrowid
                    mMovie.download_poster()
                except tmdb3.tmdb_exceptions.TMDBHTTPError as e:
                    logging.error("HTTP error({0}): {1}".format(e.httperrno, e.response))
                    raise MovieDbError("HTTP error({0}): {1}".format(e.httperrno, e.response))
                except:
                    logging.error("Unexpected error: %s", sys.exc_info()[0])
                    raise MovieDbError("Unexpected error: %s", sys.exc_info()[0])
        return redirect(url_for('editmovie', id=final_movieid))


@app.route('/delete', methods=['GET'])
def delete():
    if request.args:
        mid = int(request.args['id']) if 'id' in request.args else 0
        fid = int(request.args['fid']) if 'fid' in request.args else 0
        dbcon = get_db()
        if fid > 0:
            unboundMovieFile(dbcon, fid, mid)
            return files()
        else:
            removeMovie(dbcon, mid)
            return redirect(url_for('index'))


@app.route('/restore')
def restore():
    file_id = request.args['fid']
    if file_id:
        dbcon = get_db()
        restoreFile(dbcon, file_id)
    return files()


@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404


@app.errorhandler(DbError)
def internal_error(error):
    get_db().rollback()
    return render_template('500.html', message=error.message), 500

@app.errorhandler(DbConnectionError)
def db_connection_error(error):
    return render_template('500.html', message=error.message), 500


def get_removed_files(dbcon):
    files = getFiles(dbcon, REMOVED_FILE)
    for f in files:
        f['basename'] = os.path.basename(f['filepath'])
    return files


def get_bounded_files(dbcon):
    files = getFiles(dbcon, BOUNDED_FILE)
    return [({'basename': os.path.basename(file['filepath']), 'rowid': file['rowid']}, getMovieByID(dbcon, file['movieid'])) for file in files]


def get_orphan_files(dbcon):
    files = getFiles(dbcon, ORPHAN_FILE)
    for f in files:
        f['basename'] = os.path.basename(f['filepath'])
    return files