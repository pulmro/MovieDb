#   -*- coding: utf-8 -*-

import os
import mimetypes
import re
import tmdb3
import sys
import logging
import config
import sched
from sqliteiface import *
from mymovie import mymovie, mymovieFromTmdb
import poster_engine

NUM_THREADS = 2


class MovieDb():

    def __init__(self):
        self.init_tmdb()
        #Connecting to local database
        self.db = sqlite_connect(config.cfg['DBFILE'])
        #Welcome message
        logging.info("MovieDb %s by Emanuele Bigiarini, 2012", config.cfg['version'])
        logging.info("Released under GPL license.")

    @staticmethod
    def init_tmdb():
        """Initialize TMDb api"""
        tmdb3.set_key(config.cfg['API_KEY'])
        tmdb3.set_cache(engine='file', filename=config.cfg['CACHEPATH']+'/.tmdb3cache')
        tmdb3.set_locale(config.cfg['LANG'], config.cfg['COUNTRY'])

    def filtername(self, name):
        """Filter special character or parentheses in the filename"""
        name = re.sub(r'\([^)]*\)|\[[^]]*\]', '', name)
        name = name.replace(".", " ")
        name = name.replace("-", " ")
        name = name.replace("_", " ")
        return name.lstrip()

    def loop(self, scheduler):
        (new_movies, deleted_movies) = self.scan_files()
        if new_movies or deleted_movies:
            logging.info("Some new actions to run")
        self.get_movies(new_movies)
        self.remove_movies(deleted_movies)
        self.retrieve_posters(NUM_THREADS)
        scheduler.enter(config.cfg['LOOPTIME'], 1, self.loop, (scheduler,))
        logging.info("Scanning in %d", config.cfg['LOOPTIME'])

    def scan_files(self):
        """Scan for video files in the path comparing with the db, and returns new files and removed"""
        logging.info("Scanning files...")
        m = re.compile('video/.*')
        path = config.cfg['MOVIEPATH']
        movies_in_db = getMoviesPathDict(self.db)
        newmovies = {}
        for dirname, dirnames, filenames in os.walk(path):
            for filename in filenames:
                filepath = unicode(os.path.join(dirname, filename), "utf-8", "ignore")
                file_type = mimetypes.guess_type(filepath)[0]
                if file_type is None and m.match(file_type) and not config.is_blacklisted(dirname):
                    if filepath in movies_in_db:
                        movies_in_db.pop(filepath)
                    else:
                        logging.info("Found %s", filepath.encode('utf-8'))
                        f_name = unicode(self.filtername(os.path.splitext(filename)[0]), "utf-8", "ignore")
                        newmovies[filepath] = mymovie(f_name)
        #Now movies_in_db just contains the files to be removed from the db
        return newmovies, movies_in_db

    def insert_movie(self, res, path, my_movie):
        the_movie = res[0]
        movieid = getmoviebyTMDbID(self.db, the_movie.id)
        if not movieid:
            my_movie.populate(the_movie)
            movieid = insertNewMovie(self.db, my_movie)
        linkNewFileToMovie(self.db, path, my_movie.name, movieid)

    def get_movies(self, new_movies):
        """Search info for movies in new_movies and add them to the db."""
        #TODO: implement multi-threaded search for movies
        for path, movie in new_movies.iteritems():
            logging.info("searching for... %s", movie.name.encode('utf-8'))
            try:
                res = tmdb3.searchMovie(movie.name.encode('utf-8'))
                if len(res) == 0:
                    words = movie.name.split(' ')
                    strings_to_test = [' '.join(words[0:i]).encode('utf-8') for i in range(len(words), 0, -1)]
                    i = 1
                    while len(res) == 0:
                        logging.info("searching for... %s", strings_to_test[i])
                        res = tmdb3.searchMovie(strings_to_test[i])
                        i += 1
                if len(res) == 0:
                    insertOrphanFile(self.db, path, movie.name)
                else:
                    self.insert_movie(res, path, movie)
            except tmdb3.tmdb_exceptions.TMDBHTTPError as e:
                logging.error("HTTP error({0}): {1}".format(e.httperrno, e.response))
                insertOrphanFile(self.db, path, movie.name)
            except:
                logging.error("Unexpected error: %s", sys.exc_info()[0])
                raise

    def remove_movies(self, movie_dict):
        """Remove movie in movie_dict from the db."""
        for path, idz in movie_dict.iteritems():
            logging.info("removing... %s", path.encode('utf-8'))
            removeFile(self.db, path)

    def retrieve_posters(self, num_threads):
        for i in xrange(1, num_threads):
            thread = poster_engine.PosterDownloaderThread(i, "Thread-%d" % i, i)
            thread.start()

    def update_database(self):
        """Download again info from TMDB for the movies in the db."""
        tmdb_ID_list = getTMDbIds(self.db)
        for (tmdbID,) in tmdb_ID_list:
            if tmdbID > 0:
                try:
                    movie = mymovieFromTmdb(tmdb3.Movie(tmdbID), False)
                    updateMoviesByTMDbID(self.db, movie, tmdbID)
                except tmdb3.tmdb_exceptions.TMDBHTTPError as e:
                    logging.error("Movie not updated.")
                    logging.error("HTTP error({0}): {1}".format(e.httperrno, e.response))
                except:
                    logging.error("Unexpected error: %s", sys.exc_info()[0])
                    raise

    def reset_database(self):
        """Clean the db."""
        reset(self.db)
        self.db.close()
