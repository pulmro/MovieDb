from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm.exc import NoResultFound

from sqlalchemy import event
from config import cfg


def on_connect(conn, record):
    conn.execute('pragma foreign_keys=ON')


def init_db():
    import models
    Base.metadata.create_all(bind=engine)
    try:
        models.Movie.query.filter(models.Movie.movieid == -1).one()
    except NoResultFound:
        orphan_movie = models.Movie(movieid=-1, title='Unknown Movie', director='Unknown Director')
        db_session.add(orphan_movie)
    try:
        models.Movie.query.filter(models.Movie.movieid == -1).one()
    except NoResultFound:
        removed_movie = models.Movie(movieid=-2, title='Removed Movie', director='Unknown Director')
        db_session.add(removed_movie)
    try:
        db_session.commit()
    except:
        db_session.rollback()

if cfg['TESTING'] is True:
    engine = create_engine('sqlite:///{0}/{1}'.format(cfg['DBPATH'], 'test.db'), convert_unicode=True, echo=True)
else:
    engine = create_engine('sqlite:///{0}'.format(cfg['DBFILE']), convert_unicode=True)
event.listen(engine, 'connect', on_connect)
db_session = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))

Base = declarative_base()
Base.query = db_session.query_property()


