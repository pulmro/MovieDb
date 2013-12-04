#   -*- coding: utf-8 -*-

import tmdb3, thread, os, urllib
import config


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

    def populate(self, the_movie, poster_size='w500', download_poster=True):
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
            urlimage = the_movie.poster.geturl(poster_size)
            if download_poster:
                bname = os.path.basename(urlimage)
                #self.imagefile = config.DBPATH+'/'+bname
                self.imagefile = bname
                stdoutmutex = thread.allocate_lock()
                thread.start_new_thread(self.fetchPoster, (urlimage, self.imagefile, self.title, stdoutmutex))
            else:
                self.imagefile = urlimage
        self.tmdbID = the_movie.id

    def fetchPoster(self, url, imgfile, movieTitle, mutex):
        destfile = config.cfg['DBPATH']+'/'+imgfile
        urllib.urlretrieve(url, destfile)
        with mutex:
            print "Downloaded poster for "+self.title.encode('ascii', 'ignore')+': '+imgfile


def mymovieFromTmdb(the_movie, poster_size, download_poster):
    m = mymovie()
    m.populate(the_movie, poster_size, download_poster)
    return m
