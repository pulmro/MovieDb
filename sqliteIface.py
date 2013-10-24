import sqlite3
from mymovie import mymovie

DICT_FACTORY=1

class sqliteIface():
	
	def __init__(self, dbfile, dictfactory=0):
		self.dbcon = sqlite3.connect(dbfile)
		if dictfactory:
			self.dbcon.row_factory = self.dict_factory
		if not self.existsTable():
			self.createTable()
	
	def close(self):
		self.dbcon.close()
	
	def dict_factory(self, cursor, row):
		d = {}
		for idx, col in enumerate(cursor.description):
			d[col[0]] = row[idx]
		return d
	
	def createTable(dbcon):
		curs = self.dbcon.cursor()
		#Table files 3 columns
		curs.execute('CREATE TABLE files(filepath text, name text, movieid integer, primary key(filepath))')
		#Table movies 10 columns
		curs.execute('CREATE TABLE movies (movieid integer, title text, director text, cast text,\
		  overview text, runtime integer, year integer, morandini text, imagefile text, tmdbID integer, primary key(movieid))')
		dbcon.commit()
		curs.close()

	def requestFetchOne(self, sqlRequest, params=()):
		curs = self.dbcon.cursor()
		curs.execute(sqlRequest, params)
		res = curs.fetchone()
		curs.close()
		return res

	def requestFetchAll(self, sqlRequest, params=()):
		curs = self.dbcon.cursor()
		curs.execute(sqlRequest, params)
		res = curs.fetchall()
		curs.close()
		return res

	def existsTable(self):
		res = True
		sqlRequest = "SELECT name FROM sqlite_master WHERE type='table' AND name='movies'"
		if not self.requestFetchOne(sqlRequest):
			res = False
		return res


	def existMovie(self, filepath):
		res = True
		if not self.requestFetchOne("SELECT name FROM files WHERE filepath = ?", (filepath,)):
			res = False
		return res


	def getmoviebyfile(self, filepath):
		r = self.requestFetchOne("SELECT movieid FROM files WHERE filepath = ?", (filepath,))
		if r:
			return r[0]
		else:
			return None


	def getmoviebyTMDbID(self, id):
		r = self.requestFetchOne("SELECT movieid FROM movies WHERE tmdbID = ?", (id,))
		if r:
			return r[0]
		else:
			return None


	def getMoviesSortedByTitle(self):
		return self.requestFetchAll('SELECT * FROM movies ORDER BY title')

	def getMoviesSortedByYear(self):
		return self.requestFetchAll('SELECT * FROM movies ORDER BY year')

	def getTMDbIds(self):
		curs = self.dbcon.cursor()
		curs.execute('SELECT tmdbId FROM movies')
		res = curs.fetchall()
		curs.close()
		return res
	
	
	def getMoviespathdict(self):
		d = {}
		curs = self.dbcon.cursor()
		curs.execute('SELECT filepath,movieid FROM files')
		row = curs.fetchone()
		while row:
			d[row[0]]=row[1]
			row = curs.fetchone()
		curs.close()
		return d


	def isMovieOrphan(self, movieid):
		res = False
		if not self.requestFetchOne("SELECT filepath FROM files WHERE movieid = ?", (movieid,)):
			res = True
		return res
		
	
	def removeFile(self, filepath):
		id = self.getmoviebyfile(filepath)
		curs = self.dbcon.cursor()
		curs.execute('DELETE FROM files WHERE filepath = ?', (filepath,))
		self.dbcon.commit()
		if id>0 and self.isMovieOrphan(id):
			curs.execute('DELETE FROM movies WHERE movieid = ?', (id,))
		self.dbcon.commit()
		curs.close()
	
	
	def makerow(self, mMovie):
		return (mMovie.title, mMovie.director, mMovie.cast, mMovie.overview, mMovie.runtime, mMovie.year, mMovie.morandini, mMovie.imagefile, mMovie.tmdbID)
	
	
	def insertOrphanFile(self, path, name):
		curs = self.dbcon.cursor()
		curs.execute('INSERT INTO files VALUES (?,?,?)', (path, name, -1))
		self.dbcon.commit()
		curs.close()
	
	
	def insertNewMovie(self, mMovie):
		row = self.makerow(mMovie)
		curs = self.dbcon.cursor()
		curs.execute('INSERT INTO movies VALUES (null,?,?,?,?,?,?,?,?,?)', row)
		self.dbcon.commit()
		res = curs.lastrowid
		curs.close()
		return res
	
	
	def linkNewFileToMovie(self, filepath, fname, movieid):
		curs = self.dbcon.cursor()
		curs.execute('INSERT INTO files VALUES (?,?,?)', (filepath, fname, movieid))
		self.dbcon.commit()
		curs.close()

	
	def updateMoviesByTMDbID(self, mMovie, tmdbID):
		row = self.makerow(mMovie)
		curs = self.dbcon.cursor()
		curs.execute('UPDATE movies SET title=?, director=?, cast=?, overview=?, runtime=?, year=?, morandini=?, imagefile=?, tmdbID=? WHERE tmdbID=?', row+(tmdbID,))
		self.dbcon.commit()
		curs.close()
	
	
	def reset(self):
		curs = self.dbcon.cursor()
		curs.execute('DELETE FROM movies')
		curs.execute('DELETE FROM files')
		self.dbcon.commit()
		curs.close()
