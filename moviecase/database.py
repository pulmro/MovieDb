from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy import event
from config import cfg


def on_connect(conn, record):
    conn.execute('pragma foreign_keys=ON')


def init_db():
    import models
    Base.metadata.create_all(bind=engine)

if cfg['TESTING'] is True:
    engine = create_engine('sqlite:///{0}/{1}'.format(cfg['DBPATH'], 'test.db'), convert_unicode=True, echo=True)
else:
    engine = create_engine('sqlite:///{0}'.format(cfg['DBFILE']), convert_unicode=True)
event.listen(engine, 'connect', on_connect)
db_session = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))

Base = declarative_base()
Base.query = db_session.query_property()


