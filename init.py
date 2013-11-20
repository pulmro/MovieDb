#   -*- coding: utf-8 -*-

import getopt, sys, sched, time, thread, logging

from moviecase import config
from moviecase.moviedb import moviedb
from moviecase import cherryserver

def usage():
	print "MovieDb 0.1 by Emanuele Bigiarini, 2012"
	print "Released under GPL License"
	print ""
	print "-h, --help:\tPrint this help"
	print "-u, --update:\tUpdate existing database"
	print "-c, --reset:\tClean existing database"
	print "-w, --webserver:\tServer mode only"

def main(argv):
	try:
		opts, args = getopt.getopt(argv, "dhcuw", ["help", "clean", "update","webserver"])
	except getopt.GetoptError:
		usage()
		sys.exit(2)
	for opt, arg in opts:
		if opt in ("-h", "--help"):
			usage()
			sys.exit()
		elif opt in ("-c","--clean"):
			mdb = moviedb()
			mdb.resetdatabase()
		elif opt in ("-u","--update"):
			mdb = moviedb()
			config.printCurrentSettings()
			mdb.updatedatabase()
		elif opt in ("-d"):
			mdb = moviedb()
			config.printCurrentSettings()
			s = sched.scheduler(time.time, time.sleep)
			s.enter(5, 1, mdb.scanfiles, (s, ))
			try:
				PORT = int( config.cfg['SERVERPORT'])
				thread.start_new_thread(cherryserver.startServer,(PORT,))
				s.run()
			except KeyboardInterrupt:
				logging.info("Exiting...")
		elif opt in ("-w","--webserver"):
			config.printCurrentSettings()
			logging.info("Starting in server mode only.")
			try:
				PORT = int( config.cfg['SERVERPORT'])
				cherryserver.startServer(PORT)
			except KeyboardInterrupt:
				logging.info("Exiting...")

if __name__ == "__main__":
	main(sys.argv[1:])
