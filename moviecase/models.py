from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship, backref
from database import Base
import tmdb3
import os
import config
from poster_engine import PosterDownloadQueue, PosterDownloaderThread

dir_for_size = {'w92': 'small', 'w185': 'medium', 'w342': 'large'}


class Movie(Base):
    __tablename__ = 'movies'
    movieid = Column(Integer, primary_key=True)
    title = Column(String(255), unique=True)
    director = Column(String(500))
    cast = Column(String(1024))
    overview = Column(Text)
    runtime = Column(Integer)
    year = Column(Integer)
    morandini = Column(Text)
    imagefile = Column(String(60))
    tmdbID = Column(Integer)

    def populate(self, the_movie, download_poster=True):
        self.title = the_movie.title
        for person in the_movie.cast:
            self.cast = self.cast + '{0}: {1};'.format(person.name, person.character)
        if len(the_movie.crew) > 0:
            directors = [person.name for person in the_movie.crew if person.job == 'Director']
            self.director = ','.join(directors)
        self.overview = the_movie.overview
        #runtime in it_IT locale is not set so we get from the en_US
        #TODO: move to the MovieDb
        tmdb3.set_locale('en', 'US')
        self.runtime = tmdb3.Movie(the_movie.id).runtime
        tmdb3.set_locale(config.cfg['LANG'], config.cfg['COUNTRY'])
        if the_movie.releasedate:
            self.year = the_movie.releasedate.year
        if the_movie.poster:
            image_url = the_movie.poster.geturl('w185')
            if download_poster:
                queue = PosterDownloadQueue()
                poster_urls = set((the_movie.poster.geturl(size), dir_for_size[size])
                                  for size in dir_for_size.keys())
                queue.to_download.update(poster_urls)
                bname = os.path.basename(image_url)
                self.imagefile = bname
            else:
                self.imagefile = image_url
        self.tmdbID = the_movie.id
        return self

    def download_poster(self):
        """ Download poster on command"""
        PosterDownloaderThread(1, "Thread-%d for %s" % (1, self.title), 1).start()

    @staticmethod
    def movie_from_tmdb(the_movie, download_poster):
        return Movie().populate(the_movie, download_poster)


class File(Base):
    __tablename__ = 'files'
    id = Column(Integer, primary_key=True)
    filepath = Column(String(512), unique=True)
    name = Column(String(200))
    movieid = Column(Integer, ForeignKey('movies.movieid'))
    movie = relationship("Movie", backref=backref('files', order_by=name))