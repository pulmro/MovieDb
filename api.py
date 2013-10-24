#!/usr/bin/python2
import cgi, json
import config

from sqliteIface import sqliteIface, DICT_FACTORY

def isuserhere(form):
	if not 'user' in form:
		print('<h1>Who are you?</h1>')
	else:
		print('<h1>Hello <i>%s</i>!</h1>' % cgi.escape(form['user'].value))

def getMovies(form):
	try:
		if form['sort'].value == 'year':
			R = database.getMoviesSortedByYear()
		elif form['sort'].value == 'title':
			R = database.getMoviesSortedByTitle()
		else:
			R = {'error':'Bad Request! Check your `sort` parameter.'}
	except:
		R={'error':'Error retrieving movies.'}
	return json.dumps(R, sort_keys=False) #return json object
	

methods = {'isuserhere':isuserhere, 'getMovies':getMovies}
form = cgi.FieldStorage() # parse form data
print('Content-type: application/json\n') # hdr plus blank line


method=cgi.escape(form['method'].value)

try:
	database = sqliteIface(config.cfg['DBFILE'],DICT_FACTORY)
	print methods[method](form)
except:
	print(json.dumps({'error':'Unable to connect to the database.'}))
