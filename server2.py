from CGIHTTPServer import CGIHTTPRequestHandler
from BaseHTTPServer import HTTPServer
from SocketServer import ThreadingMixIn

import logging
"""  
class ThreadingServer(ThreadingMixIn, HTTPServer): pass

class myHandler(CGIHTTPRequestHandler,object) :
	def parsePath(self, pathString) :
		args = pathString.split('?')[1]
		basepath = pathString.split('?')[0]
		pairs = [s.split('=') for s in args.split('&')]
		pairDict = {}
		for item in pairs :
			pairDict[item[0]] = item[1]
		return (basepath, pairDict)
	
	def do_GET(self):
		print "load", self.path
		if self.path.find('?') > 0 :
			(base,args) = self.parsePath(self.path)
			print base, args

"""

class myHandler(CGIHTTPRequestHandler):
	
	def log_message(self, format, *args):
		logging.info("%s - - [%s] %s" %
                     (self.client_address[0],
                     self.log_date_time_string(),
                     format%args))


class webinterface():
	
	def __init__(self, port):
		self.PORT = port
		#handler = CGIHTTPRequestHandler
		handler = myHandler
		handler.cgi_directories = ['/']
		self.httpd = HTTPServer(("", port), handler)
	
	def run(self):
		logging.info("Serving at port %d", self.PORT)
		self.httpd.serve_forever()
		
	def shutdown(self):
		self.httpd.shutdown()
		
