#   -*- coding: utf-8 -*-

import getopt
import sys
import sched
import time
import thread
import logging

from moviecase import config
from moviecase.moviedb import MovieDb
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
        opts, args = getopt.getopt(argv, "dhcuwv", ["help", "clean", "update", "webserver", "verbose"])
    except getopt.GetoptError:
        usage()
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-v", "--verbose"):
            config.verbose = True
        if opt in ("-h", "--help"):
            usage()
            sys.exit()
        elif opt in ("-c", "--clean"):
            mdb = MovieDb()
            mdb.reset_database()
        elif opt in ("-u", "--update"):
            mdb = MovieDb()
            config.print_current_settings()
            mdb.update_database()
        elif opt in ("-d"):
            mdb = MovieDb()
            config.print_current_settings()
            s = sched.scheduler(time.time, time.sleep)
            s.enter(5, 1, mdb.loop, (s, ))
            try:
                port = int(config.cfg['SERVERPORT'])
                thread.start_new_thread(cherryserver.start_server, (port,))
                s.run()
            except KeyboardInterrupt:
                logging.info("Exiting...")
        elif opt in ("-w", "--webserver"):
            config.print_current_settings()
            logging.info("Starting in server mode only.")
            try:
                port = int(config.cfg['SERVERPORT'])
                cherryserver.start_server(port)
            except KeyboardInterrupt:
                logging.info("Exiting...")

if __name__ == "__main__":
    main(sys.argv[1:])
