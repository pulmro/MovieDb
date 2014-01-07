from flask import request, jsonify, send_file, g, _app_ctx_stack

from .. import config
from . import app
from ..database import db_session
from .. import db_methods
from exceptions import ApiDbConnectionError, ApiBadRequest, ApiNotFound


@app.route('/api/serverinfo', methods=['GET'])
def getServerInfo():
    return jsonify({'result': 'OK', 'service': 'MovieDb', 'version': config.cfg['version']})


@app.route('/api/recentmovies', methods=['GET'])
def getRecentMovies():
    return jsonify({'result': 'OK', 'response': db_methods.get_latest_movies(5)})


@app.route('/api/movies', methods=['GET'])
def getMovieList():
    try:
        #shortFlag = bool(request.args['short'][0])
        sort = request.args['sort']
    except:
        raise ApiBadRequest("Check your parameters: short=true|false, page=num_page, sort=title|year")
    page = int(request.args['page']) if 'page' in request.args else 0
    if sort == 'year':
        response = {'result': 'OK', 'response': [mov.serialize() for mov in db_methods.get_movies(page, sort='year')],
                    'current_page': page, 'total_count_page': db_methods.get_count_pages()}
    elif sort == 'title':
        response = {'result': 'OK', 'response': [mov.serialize() for mov in db_methods.get_movies(page)],
                    'current_page': page, 'total_count_page': db_methods.get_count_pages()}
    else:
        raise ApiBadRequest("Check your `sort` parameter.")
    return jsonify(response)


@app.route('/api/movies/<int:movie_id>', methods=['GET'])
def getMovie(movie_id):
    try:
        movie = db_methods.get_movie(movie_id)
        response = {'result': 'OK', 'response': movie.serialize()}
    except:
        raise ApiNotFound("None movie with given id.")
    return jsonify(response)


@app.route('/api/movies/<int:movie_id>/poster', methods=['GET'])
def getPoster(movie_id):
    size = request.args['size'] if request.args and 'size' in request.args else 'medium'
    try:
        movie = db_methods.get_movie(movie_id)
        filename = "%s/%s/%s" % (config.cfg['DBPATH'], size, movie.imagefile)
        response = send_file(filename)
    except:
        raise ApiNotFound("Error retrieving poster: {0}".format(movie.imagefile))
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