import logging
from cherrypy import wsgiserver, log, _cplogging

#from moviecase.www import fAPI
from moviecase.www import app

def startServer(port):
	#d = wsgiserver.WSGIPathInfoDispatcher({'/': fAPI.app})
	d = wsgiserver.WSGIPathInfoDispatcher({'/': app})
	server = wsgiserver.CherryPyWSGIServer(('0.0.0.0', port), d )
	#config.update({'log.error_file': 'Web.log', 'log.access_file': 'Access.log'})
	try:
		server.start()
		logging.info("Serving at port %d", port)
	except KeyboardInterrupt:
		#fAPI.database.close()
		
		server.stop()


if __name__ == '__main__':
	startServer(8080)
