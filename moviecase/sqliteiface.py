import sqlite3
import os
from mymovie import mymovie

DICT_FACTORY = 1

REMOVED_FILE = -2
BOUNDED_FILE = 0
ORPHAN_FILE = -1


def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


def sqlite_connect(dbfile, dictfactory=0):
    dbcon = sqlite3.connect(dbfile)
    if dictfactory:
        dbcon.row_factory = dict_factory
    if not existsTable(dbcon):
        createTable(dbcon)
    return dbcon


def createTable(dbcon):
    curs = dbcon.cursor()
    #Table files 3 columns
    curs.execute('CREATE TABLE files(filepath text, name text, movieid integer, primary key(filepath))')
    #Table movies 10 columns
    curs.execute('CREATE TABLE movies (movieid integer, title text, director text, cast text,\
      overview text, runtime integer, year integer, morandini text, imagefile text, tmdbID integer, primary key(movieid))')
    dbcon.commit()
    curs.close()


def existsTable(dbcon):
    res = True
    sql_request = "SELECT name FROM sqlite_master WHERE type='table' AND name='movies'"
    if not requestFetchOne(dbcon, sql_request):
        res = False
    return res


def requestFetchOne(dbcon, sql_request, params=()):
    curs = dbcon.cursor()
    curs.execute(sql_request, params)
    res = curs.fetchone()
    curs.close()
    return res


def requestFetchAll(dbcon, sqlRequest, params=()):
    curs = dbcon.cursor()
    curs.execute(sqlRequest, params)
    res = curs.fetchall()
    curs.close()
    return res


def existMovie(dbcon, filepath):
    res = True
    if not requestFetchOne(dbcon, "SELECT name FROM files WHERE filepath = ?", (filepath,)):
        res = False
    return res


def getmoviebyfile(dbcon, filepath):
    r = requestFetchOne(dbcon, "SELECT movieid FROM files WHERE filepath = ?", (filepath,))
    if r:
        return r[0]
    else:
        return None


def getmoviebyTMDbID(dbcon, id):
    r = requestFetchOne(dbcon, "SELECT movieid FROM movies WHERE tmdbID = ?", (id,))
    return r if r else None


def getFilesByMovieID(dbcon, id):
    return requestFetchAll(dbcon, 'SELECT * FROM files WHERE movieid = ?', (id,))


def getMovieByID(dbcon, id):
    return requestFetchOne(dbcon, 'SELECT * FROM movies WHERE movieid = ?', (id,))


def getCountPage(dbcon):
    response = requestFetchOne(dbcon, "SELECT COUNT(*) FROM movies")
    try:
        num_rows = response[0]
    except KeyError:
        num_rows = response['COUNT(*)']
    return num_rows//20 + 1


def getMovies(dbcon, short_flag, sort):
    if not short_flag:
        curs = dbcon.cursor()
        response = []
        for row in curs.execute('SELECT * FROM movies ORDER BY {0}'.format(sort)):
            if type(row) is dict:
                files = getFilesByMovieID(dbcon, row['movieid'])
                row['filesname'] = [os.path.basename(file['filepath']) for file in files]
            response.append(row)
        curs.close()
        return response
    else:
        return requestFetchAll(dbcon, 'SELECT movieid,title,director FROM movies ORDER BY {0}'.format(sort))


def getMoviesSortedByTitle(dbcon, flag, page=0):
    if page == 0:
        return getMovies(dbcon, flag, 'title')
    else:
        return getMovies(dbcon, flag, 'title')[20*(page-1):20*page]


def getMoviesSortedByYear(dbcon, flag, page=0):
    if page == 0:
        return getMovies(dbcon, flag, 'year')
    else:
        return getMovies(dbcon, flag, 'year')[20*(page-1):20*page]


def get5LatestMovies(dbcon):
    files = requestFetchAll(dbcon, 'SELECT movieid FROM files WHERE movieid>0 ORDER BY rowid DESC')
    seq = [file['movieid'] for file in files]
    seen = set()
    seen_add = seen.add
    return [ getMovieByID(dbcon, id) for id in seq if id not in seen and not seen_add(id) and len(seen)<6 ]


def getFiles(dbcon, file_type):
    sql_expr = {REMOVED_FILE: 'movieid = -2', ORPHAN_FILE: 'movieid = -1', BOUNDED_FILE: 'movieid > 0'}
    return requestFetchAll(dbcon, 'SELECT rowid,* FROM files WHERE {0}'.format(sql_expr[file_type]))


def boundFileWithMovie(dbcon, fileid, movieid):
    curs = dbcon.cursor()
    curs.execute('UPDATE files SET movieid = ? WHERE rowid = ?', (movieid, fileid))
    dbcon.commit()
    curs.close()


def unboundMovieFile(dbcon, fileid, movieid=0):
    curs = dbcon.cursor()
    if movieid > 0:
        curs.execute('UPDATE files SET movieid=-1 WHERE rowid=?;', (fileid,))
        curs.execute('DELETE FROM movies WHERE (movieid = ? AND movieid NOT IN (SELECT movieid FROM files));', (movieid,))
    else:
        curs.execute('UPDATE files SET movieid=-2 WHERE rowid = ? ;', (fileid,))
    dbcon.commit()
    curs.close()


def updateBoundWithMovie( dbcon, old_movieid, new_movieid):
    curs = dbcon.cursor()
    curs.execute('UPDATE files SET movieid = ? WHERE movieid = ?;', (new_movieid, old_movieid))
    curs.execute('DELETE FROM movies WHERE movieid = ? ;', (old_movieid,))
    dbcon.commit()
    curs.close()


def removeMovie(dbcon, movieid):
    curs = dbcon.cursor()
    curs.execute('DELETE FROM movies WHERE movieid = ? ;', (movieid,))
    curs.execute('UPDATE files SET movieid=-1 WHERE movieid = ? ;', (movieid,))
    dbcon.commit()
    curs.close()


def restoreFile(dbcon, fileid):
    curs = dbcon.cursor()
    curs.execute('UPDATE files SET movieid=-1 WHERE rowid = ?', (fileid,))
    dbcon.commit()
    curs.close()


def getTMDbIds(dbcon):
    curs = dbcon.cursor()
    curs.execute('SELECT tmdbId FROM movies')
    res = curs.fetchall()
    curs.close()
    return res


def getMoviesPathDict(dbcon):
    d = {}
    curs = dbcon.cursor()
    curs.execute('SELECT filepath,movieid FROM files')
    row = curs.fetchone()
    while row:
        d[row[0]] = row[1]
        row = curs.fetchone()
    curs.close()
    return d


def isMovieOrphan(dbcon, movieid):
    res = False
    if not requestFetchOne(dbcon, "SELECT filepath FROM files WHERE movieid = ?", (movieid,)):
        res = True
    return res


def removeFile(dbcon, filepath):
    id = getmoviebyfile(dbcon, filepath)
    curs = dbcon.cursor()
    curs.execute('DELETE FROM files WHERE filepath = ?', (filepath,))
    dbcon.commit()
    if id>0 and isMovieOrphan(dbcon, id):
        curs.execute('DELETE FROM movies WHERE movieid = ?', (id,))
    dbcon.commit()
    curs.close()


def makerow(movie):
    return movie.title, movie.director, movie.cast, movie.overview, movie.runtime, movie.year, movie.morandini,\
        movie.imagefile, movie.tmdbID


def insertOrphanFile(dbcon, path, name):
    curs = dbcon.cursor()
    curs.execute('INSERT INTO files VALUES (?,?,?)', (path, name, -1))
    dbcon.commit()
    curs.close()


def insertNewMovie(dbcon, mMovie):
    row = makerow(mMovie)
    curs = dbcon.cursor()
    curs.execute('INSERT INTO movies VALUES (null,?,?,?,?,?,?,?,?,?)', row)
    dbcon.commit()
    res = curs.lastrowid
    curs.close()
    return res


def linkNewFileToMovie(dbcon, filepath, fname, movieid):
    curs = dbcon.cursor()
    curs.execute('INSERT INTO files VALUES (?,?,?)', (filepath, fname, movieid))
    dbcon.commit()
    curs.close()


def updateMoviesByTMDbID(dbcon, mMovie, tmdbID):
    row = makerow(mMovie)
    curs = dbcon.cursor()
    curs.execute('UPDATE movies SET title=?, director=?, cast=?, overview=?, runtime=?, year=?, morandini=?,'
                 'imagefile=?, tmdbID=? WHERE tmdbID=?', row+(tmdbID,))
    dbcon.commit()
    curs.close()


def reset(dbcon):
    curs = dbcon.cursor()
    curs.execute('DELETE FROM movies')
    curs.execute('DELETE FROM files')
    dbcon.commit()
    curs.close()

