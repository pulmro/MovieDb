#   -*- coding: utf-8 -*-

import os, mimetypes, re, tmdb3, sys, sched, logging
import config
from sqliteIface import sqliteIface
from mymovie import mymovie

class moviedb():
	
	def __init__(self):
		# Creating TMDb object
		tmdb3.set_key(config.cfg['API_KEY'])
		tmdb3.set_cache(engine='file', filename=config.cfg['CACHEPATH']+'/.tmdb3cache')
		tmdb3.set_locale('it','it')
		#Connecting to local database
		self.database = sqliteIface(config.cfg['DBFILE'])

	
	def filtername(self, name):
		name = re.sub(r'\([^)]*\)|\[[^]]*\]', '',name)
		name = name.replace("."," ")
		name = name.replace("-"," ")
		name = name.replace("_"," ")
		return name.lstrip()

		
	def isBlacklisted(self, dir):
		dir = os.path.realpath(dir)
		flag=False
		for bdir in config.cfg['BLACKLIST']:
			bdir = os.path.realpath(config.cfg['MOVIEPATH']+"/"+bdir)
			if os.path.commonprefix([dir, bdir]) == bdir:
				flag=True
		return flag
	
	
	def scanfiles(self, sc):
		logging.info( "Scanning files...")
		m = re.compile('video/.*')
		path = config.cfg['MOVIEPATH']
		d = self.database.getMoviespathdict()
		newmovies = {}
		for dirname, dirnames, filenames in os.walk(path):
			for filename in filenames:
				filepath = unicode(os.path.join(dirname, filename), "utf-8", "ignore")
				ftype = mimetypes.guess_type(filepath)[0]
				if ftype<>None and m.match(ftype) and not self.isBlacklisted(dirname):
					if filepath in d:
						d.pop(filepath)
					else:
						logging.info( "Found %s", filepath.encode('utf-8'))
						fname = unicode(self.filtername(os.path.splitext(filename)[0]), "utf-8", "ignore")
						newmovies[filepath] = mymovie(fname)
		#Now in d are just the files to be removed from the db
		if newmovies or d:
			logging.info("Some new actions to run")
			self.updatemovies(newmovies, d)
		sc.enter(config.cfg['LOOPTIME'], 1, self.scanfiles, (sc,))
	
	
	def insertMovie(self, res, path, mMovie):
		movieid = self.database.getmoviebyTMDbID(res[0].id)
		if not movieid:
			mMovie.populate(res[0])
			movieid = self.database.insertNewMovie(mMovie)
		self.database.linkNewFileToMovie(path,mMovie.name, movieid)

	
	""" This method search info for movies in newmovies and add them to the db
	      It also remove from the db movies in the removemovies list."""
	def updatemovies(self, newmovies, removemovies):
		for path, movie in newmovies.iteritems():
			logging.info("searching for... %s",movie.name.encode('utf-8'))
			try:
				res = tmdb3.searchMovie(movie.name.encode('utf-8'))
				if (len(res) == 0):
					arr=movie.name.split(' ')
					i=len(arr)/2
					while i>0:
						logging.info("searching for... %s",' '.join(arr[0:i]).encode('utf-8'))
						res = tmdb3.searchMovie(' '.join(arr[0:i]).encode('utf-8'))
						if len(res)>0:
							i=0
						else:
							i=i-1
				if (len(res) == 0):
					self.database.insertOrphanFile(path, movie.name)
				else:
					self.insertMovie(res, path, movie)
			except tmdb3.tmdb_exceptions.TMDBHTTPError as e:
				logging.error( "HTTP error({0}): {1}".format(e.httperrno, e.response))
				self.database.insertOrphanFile(path, movie.name)
			except:
				logging.error( "Unexpected error: %s", sys.exc_info()[0])
				raise
		for path, idz in removemovies.iteritems():
			logging.info("removing... %s",path.encode('utf-8'))
			self.database.removeFile(path)
	
	
	def updatedatabase(self):
		tmdbIDList = self.database.getTMDbIds()
		for tmdbID in tmdbIDList:
			if tmdbID > 0:
				mM = mymovie()
				mM.populate( tmdb3.Movie(tmdbID))
				self.database.updateMoviesByTMDbID(mM, tmdbID)
				
	
	def resetdatabase(self):
		self.database.reset()
		self.database.close()
