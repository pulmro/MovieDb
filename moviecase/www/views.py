from flask import render_template, request, redirect, url_for


import logging
import tmdb3
import sys

from ..mymovie import *
from ..sqliteiface import *
from .. import config
from . import app

try:
    from flask import _app_ctx_stack as stack
    GREATER09 = True
    print "Flask is >= 0.9"
except ImportError:
    from flask import _request_ctx_stack as stack
    GREATER09 = False
    print "Flask is < 0.9"


def get_db():
    """Opens a new database connection if there is none yet for the current application context."""
    top = stack.top
    if not hasattr(top, 'sqlite_db'):
        top.sqlite_db = sqlite_connect(config.cfg['DBFILE'], DICT_FACTORY)
    return top.sqlite_db


def init_tmdb():
    tmdb3.set_key(config.cfg['API_KEY'])
    tmdb3.set_cache(engine='file', filename=config.cfg['CACHEPATH']+'/.tmdb3cache')
    tmdb3.set_locale(config.cfg['LANG'], config.cfg['COUNTRY'])


class conditional_decorator(object):
    def __init__(self, condition):
        if condition:
            self.decorator = app.teardown_appcontext
        else:
            self.decorator = app.teardown_request

    def __call__(self, func):
        return self.decorator(func)


@conditional_decorator(GREATER09)
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
        files = [ os.path.basename(file['filepath']) for file in getFilesByMovieID(dbcon, movie_id) ]
        return render_template("editmovie.html", movie=movie, files=files)


@app.route('/files')
def files():
    dbcon = get_db()
    shortlistmovies = getMoviesSortedByTitle(dbcon, True)
    orphanfiles = getOrphanFiles(dbcon)
    removedfiles = getRemovedFiles(dbcon)
    moviefiles = getBoundFilesWithMovie(dbcon)
    return render_template("files.html", shortlistmovies=shortlistmovies, orphanfiles=orphanfiles,
                           removedfiles=removedfiles, moviefiles=moviefiles)


@app.route('/cerca', methods=['GET', 'POST'])
def cerca():
    if request.method == 'POST':
        mid = int(request.form['id']) if 'id' in request.form else 0
        fid = int(request.form['fid']) if 'fid' in request.form else 0
        query = request.form['query'] if 'query' in request.form else ""
        res = []
        try:
            init_tmdb()
            resplist = tmdb3.searchMovie(query.encode('utf-8'))
            res = [ mymovieFromTmdb(tMovie, 'w154', False) for tMovie in resplist ]
            #res = [ {'obj':movie, 'urlimage':movie.poster.geturl('w154')} for movie in resplist ]
        except tmdb3.tmdb_exceptions.TMDBHTTPError as e:
            logging.error( "HTTP error({0}): {1}".format(e.httperrno, e.response))
        except:
            logging.error( "Unexpected error: %s", sys.exc_info()[0])
            raise
        return render_template("cerca.html", movieid = mid, fileid = fid, results = res)


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
                # UPDATE files SET movieid=".$movieid." WHERE rowid=".$fid.";
                boundFileWithMovie(dbcon, fid, mid)
            else:
                mMovie = mymovieFromTmdb( tmdb3.Movie(tmdbID), 'w500', True)
                lastrowid = insertNewMovie(dbcon, mMovie)
                boundFileWithMovie(dbcon, fid, lastrowid)
                final_movieid = lastrowid
        else:
            newID = getmoviebyTMDbID(dbcon, tmdbID)
            if newID:
                updateBoundWithMovie(dbcon, mid, newID)
                final_movieid = newID
            else:
                try:
                    init_tmdb()
                    mMovie = mymovieFromTmdb(tmdb3.Movie(tmdbID), 'w500', True)
                    lastrowid = insertNewMovie(dbcon, mMovie)
                    updateBoundWithMovie(dbcon, mid, lastrowid)
                    removeMovie(dbcon, mid)
                    final_movieid = lastrowid
                except tmdb3.tmdb_exceptions.TMDBHTTPError as e:
                    logging.error("HTTP error({0}): {1}".format(e.httperrno, e.response))
                except:
                    logging.error("Unexpected error: %s", sys.exc_info()[0])
                    raise
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
