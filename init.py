#   -*- coding: utf-8 -*-

import getopt, sys, sched, time, thread, logging

import config
from moviedb import moviedb
import server2


def usage():
	print "MovieDb 0.0.1 by Emanuele Bigiarini, 2012"
	print "Released under GPL License"
	print ""
	print "-h, --help:\tPrint this help"
	print "-u, --update:\tUpdate existing database"
	print "-c, --reset:\tClean existing database"

def main(argv):
	try:
		opts, args = getopt.getopt(argv, "dhcu", ["help", "clean", "update"])
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
			mdb.updatedatabase()
		elif opt in ("-d"):
			mdb = moviedb()
			s = sched.scheduler(time.time, time.sleep)
			s.enter(5, 1, mdb.scanfiles, (s, ))
			try:
				PORT = config.cfg['SERVERPORT']
				wserver = server2.webinterface(PORT)
				thread.start_new_thread(wserver.run,())
				s.run()
			except KeyboardInterrupt:
				logging.info("Exiting...")
				wserver.shutdown()


if __name__ == "__main__":
	main(sys.argv[1:])
