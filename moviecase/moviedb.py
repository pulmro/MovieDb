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
from mymovie import mymovie


class MovieDb():

    def __init__(self):
        # Initializing TMDb api
        tmdb3.set_key(config.cfg['API_KEY'])
        tmdb3.set_cache(engine='file', filename=config.cfg['CACHEPATH']+'/.tmdb3cache')
        tmdb3.set_locale(config.cfg['LANG'], config.cfg['COUNTRY'])
        #Connecting to local database
        self.db = sqlite_connect(config.cfg['DBFILE'])
        #Welcome message
        logging.info("MovieDb %s by Emanuele Bigiarini, 2012", config.cfg['version'])
        logging.info("Released under GPL license.")

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
        self.update_movies(new_movies)
        self.remove_movies(deleted_movies)
        scheduler.enter(config.cfg['LOOPTIME'], 1, self.loop, (scheduler,))
        logging.info("Scanning in %d", config.cfg['LOOPTIME'])

    def scan_files(self):
        """Scan for video files in the path, comparing with the db new files and removed"""
        logging.info("Scanning files...")
        m = re.compile('video/.*')
        path = config.cfg['MOVIEPATH']
        d = getMoviespathdict(self.db)
        newmovies = {}
        for dirname, dirnames, filenames in os.walk(path):
            for filename in filenames:
                filepath = unicode(os.path.join(dirname, filename), "utf-8", "ignore")
                file_type = mimetypes.guess_type(filepath)[0]
                if file_type <> None and m.match(file_type) and not config.is_blacklisted(dirname):
                    if filepath in d:
                        d.pop(filepath)
                    else:
                        logging.info("Found %s", filepath.encode('utf-8'))
                        f_name = unicode(self.filtername(os.path.splitext(filename)[0]), "utf-8", "ignore")
                        newmovies[filepath] = mymovie(f_name)
        #Now in d are just the files to be removed from the db
        return newmovies, d

    def insertMovie(self, res, path, mMovie):
        movieid = getmoviebyTMDbID(self.db, res[0].id)
        if not movieid:
            mMovie.populate(res[0])
            movieid = insertNewMovie(self.db, mMovie)
        linkNewFileToMovie(self.db, path, mMovie.name, movieid)

    def update_movies(self, new_movies):
        """Search info for movies in new_movies and add them to the db."""
        for path, movie in new_movies.iteritems():
            logging.info("searching for... %s", movie.name.encode('utf-8'))
            try:
                res = tmdb3.searchMovie(movie.name.encode('utf-8'))
                if len(res) == 0:
                    arr = movie.name.split(' ')
                    i = len(arr)/2
                    while i > 0:
                        logging.info("searching for... %s", ' '.join(arr[0:i]).encode('utf-8'))
                        res = tmdb3.searchMovie(' '.join(arr[0:i]).encode('utf-8'))
                        if len(res) > 0:
                            i = 0
                        else:
                            i=i-1
                if len(res) == 0:
                    insertOrphanFile(self.db, path, movie.name)
                else:
                    self.insertMovie(res, path, movie)
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

    def update_database(self):
        """Download again info from TMDB for the movies in the db."""
        tmdb_ID_list = getTMDbIds(self.db)
        for (tmdbID,) in tmdb_ID_list:
            if tmdbID > 0:
                movie = mymovie()
                try:
                    movie.populate(tmdb3.Movie(tmdbID))
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
