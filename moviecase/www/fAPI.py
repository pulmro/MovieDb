from flask import request, jsonify, send_file, g, _app_ctx_stack

from ..sqliteiface import *
from .. import config
from . import app
from exceptions import ApiDbConnectionError, ApiBadRequest, ApiNotFound


def get_db():
    """Opens a new database connection if there is none yet for the current application context."""
    top = _app_ctx_stack.top
    if not hasattr(top, 'sqlite_db'):
        try:
            top.sqlite_db = sqlite_connect(config.cfg['DBFILE'], DICT_FACTORY)
        except sqlite3.OperationalError as e:
            raise ApiDbConnectionError(e.message)
    return top.sqlite_db


@app.teardown_appcontext
def close_db_connection(exception):
    """Closes the database again at the end of the request."""
    top = _app_ctx_stack.top
    if hasattr(top, 'sqlite_db'):
        top.sqlite_db.close()


@app.route('/api/serverinfo', methods=['GET'])
def getServerInfo():
    return jsonify({'result': 'OK', 'service': 'MovieDb', 'version': config.cfg['version']})


@app.route('/api/recentmovies', methods=['GET'])
def getRecentMovies():
    dbcon = get_db()
    return jsonify({'result': 'OK', 'response': get5LatestMovies(dbcon)})


@app.route('/api/movies', methods=['GET'])
def getMovieList():
    try:
        shortFlag = bool(request.args['short'][0])
        sort = request.args['sort']
    except:
        raise ApiBadRequest("Check your parameters: short=true|false, page=num_page, sort=title|year")
    page = int(request.args['page']) if 'page' in request.args else 0
    dbcon = get_db()
    if sort == 'year':
        response = {'result': 'OK', 'response': getMoviesSortedByYear(dbcon, shortFlag, page),
                    'current_page': page, 'total_count_page': getCountPage(dbcon)}
    elif sort == 'title':
        response = {'result': 'OK', 'response': getMoviesSortedByTitle(dbcon, shortFlag, page),
                    'current_page': page, 'total_count_page': getCountPage(dbcon)}
    else:
        raise ApiBadRequest("Check your `sort` parameter.")
    return jsonify(response)


@app.route('/api/movies/<int:movie_id>', methods=['GET'])
def getMovie(movie_id):
    dbcon = get_db()
    movie = getMovieByID(dbcon, movie_id)
    if movie is not None:
        response = {'result': 'OK', 'response': movie}
    else:
        raise ApiNotFound("None movie with given id.")
    return jsonify(response)


@app.route('/api/movies/<int:movie_id>/poster', methods=['GET'])
def getPoster(movie_id):
    size = request.args['size'] if request.args and 'size' in request.args else 'medium'
    dbcon = get_db()
    try:
        movie = getMovieByID(dbcon, movie_id)
        filename = "%s/%s/%s" % (config.cfg['DBPATH'], size, movie['imagefile'])
        response = send_file(filename)
    except:
        raise ApiNotFound("Error retrieving poster: {0}".format(movie['imagefile']))
    return response


@app.errorhandler(ApiDbConnectionError)
def db_connection_error(error):
    return jsonify({'result': 'KO', 'error': error.message}), 500


@app.errorhandler(ApiBadRequest)
def bad_request(error):
    return jsonify({'result': 'KO', 'error': "Bad Request! {0}".format(error.message)}), 400


@app.errorhandler(ApiNotFound)
def generic_error(error):
    return jsonify({'result': 'KO', 'error': error.message}), 404