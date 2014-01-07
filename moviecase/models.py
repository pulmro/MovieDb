from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship, backref
from database import Base
import tmdb3
import os
import config
from poster_engine import PosterDownloadQueue, PosterDownloaderThread

dir_for_size = {'w92': 'small', 'w185': 'medium', 'w342': 'large'}

ORPHAN_FILE = -1
REMOVED_FILE = -2


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
    files = relationship("File", backref=backref('movie'), passive_deletes=True)

    def download_poster(self):
        """ Download poster on command"""
        PosterDownloaderThread(1, "Thread-%d for %s" % (1, self.title), 1).start()

    @staticmethod
    def from_tmdb(the_movie, download_poster=True):
        director = ''
        if len(the_movie.crew) > 0:
            directors = [person.name for person in the_movie.crew if person.job == 'Director']
            director = ','.join(directors)
        cast = ';'.join([u'{0}: {1} '.format(person.name, person.character) for person in the_movie.cast])
        #runtime in it_IT locale is not set so we get from the en_US
        #TODO: move to the MovieDb
        tmdb3.set_locale('en', 'US')
        runtime = tmdb3.Movie(the_movie.id).runtime
        tmdb3.set_locale(config.cfg['LANG'], config.cfg['COUNTRY'])
        year = the_movie.releasedate.year if the_movie.releasedate else 0
        if the_movie.poster:
            image_url = the_movie.poster.geturl('w185')
            if download_poster:
                queue = PosterDownloadQueue()
                poster_urls = set((the_movie.poster.geturl(size), dir_for_size[size])
                                  for size in dir_for_size.keys())
                queue.to_download.update(poster_urls)
                bname = os.path.basename(image_url)
                imagefile = bname
            else:
                imagefile = image_url
        return Movie(title=the_movie.title, director=director, cast=cast, overview=the_movie.overview, year=year,
                     runtime=runtime, imagefile=imagefile, tmdbID=the_movie.id)

    def __repr__(self):
        return '<Movie %r>' % self.title

    def serialize(self):
        return {
            'movieid': self.movieid,
            'title': self.title,
            'director': self.director,
            'cast': self.cast,
            'overview': self.overview,
            'runtime': self.runtime,
            'year': self.year,
            'morandini': self.morandini,
            'imagefile': self.imagefile,
            'tmdbID': self.tmdbID
        }


class File(Base):
    __tablename__ = 'files'
    id = Column(Integer, primary_key=True)
    filepath = Column(String(512), unique=True)
    name = Column(String(200))
    movieid = Column(Integer, ForeignKey('movies.movieid', onupdate="cascade", ondelete="SET DEFAULT"),
                     default=ORPHAN_FILE, server_default='-1', nullable=False)

    def __repr__(self):
        return '<File %r>' % self.filepath

    def set_orphan(self):
        self.movieid = ORPHAN_FILE

    def set_removed(self):
        self.movieid = REMOVED_FILE

    def get_basename(self):
        return os.path.basename(self.filepath)