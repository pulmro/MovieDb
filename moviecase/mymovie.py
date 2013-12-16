#   -*- coding: utf-8 -*-

import tmdb3
import os
import config
from poster_engine import PosterDownloadQueue


class mymovie():

    def __init__(self, myname=''):
        self.name = myname
        self.title = ''
        self.director = ''
        self.cast = ''
        self.overview = ''
        self.runtime = 0
        self.year = 0
        self.morandini = ''
        self.imagefile = ''
        self.tmdbID = 0

    def populate(self, the_movie, download_poster=True):
        self.title = the_movie.title
        for person in the_movie.cast:
            self.cast = self.cast + person.name + ': ' + person.character + '; '
        if len(the_movie.crew) > 0:
            directors = [person.name for person in the_movie.crew if person.job == 'Director']
            self.director = ','.join(directors)
        self.overview = the_movie.overview
        #runtime in it_IT locale is not set so we get from the en_US
        tmdb3.set_locale('en', 'US')
        self.runtime = tmdb3.Movie(the_movie.id).runtime
        tmdb3.set_locale(config.cfg['LANG'], config.cfg['COUNTRY'])
        if the_movie.releasedate:
            self.year = the_movie.releasedate.year
        if the_movie.poster:
            image_url = the_movie.poster.geturl('w185')
            if download_poster:
                queue = PosterDownloadQueue()
                poster_urls = set((the_movie.poster.geturl(size), size) for size in ['w92', 'w185', 'w342'])
                queue.to_download.update(poster_urls)
                bname = os.path.basename(image_url)
                self.imagefile = bname
            else:
                self.imagefile = image_url
        self.tmdbID = the_movie.id
        return self


def mymovieFromTmdb(the_movie, download_poster):
    return mymovie().populate(the_movie, download_poster)
