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
	
	def populate(self, theMovie, postersize = 'w500', downloadPoster = True):
		self.title = theMovie.title
		for person in theMovie.cast:
			self.cast = self.cast + person.name + ': '+ person.character+'; '
		if len(theMovie.crew) > 0:
			d =[person.name for person in theMovie.crew if person.job=='Director']
			self.director = ','.join(d)
		self.overview = theMovie.overview
		#runtime in it_IT locale is not set so we get from the en_US
		tmdb3.set_locale('en','US')
		self.runtime = tmdb3.Movie(theMovie.id).runtime
		tmdb3.set_locale(config.cfg['LANG'],config.cfg['COUNTRY'])
		if theMovie.releasedate:
			self.year = theMovie.releasedate.year
		if theMovie.poster:
			urlimage = theMovie.poster.geturl(postersize)
			if downloadPoster:
				bname = os.path.basename(urlimage)
				#self.imagefile = config.DBPATH+'/'+bname
				self.imagefile = bname
				stdoutmutex = thread.allocate_lock()
				thread.start_new_thread(self.fetchPoster, (urlimage,self.imagefile,self.title,stdoutmutex))
			else:
				self.imagefile = urlimage
		self.tmdbID = theMovie.id
	
	def fetchPoster(self, url, imgfile, movieTitle, mutex):
		destfile = config.cfg['DBPATH']+'/'+imgfile
		urllib.urlretrieve(url, destfile)
		with mutex:
			print "Downloaded poster for "+self.title.encode('ascii','ignore')+': '+imgfile
		
def mymovieFromTmdb(theMovie, postersize, downloadPoster):
	m = mymovie()
	m.populate(theMovie, postersize, downloadPoster)
	return m
