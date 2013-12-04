import logging
from cherrypy import wsgiserver

from moviecase.www import app


def start_server(port):
    d = wsgiserver.WSGIPathInfoDispatcher({'/': app})
    server = wsgiserver.CherryPyWSGIServer(('0.0.0.0', port), d)
    try:
        server.start()
        logging.info("Serving at port %d", port)
    except KeyboardInterrupt:
        server.stop()


if __name__ == '__main__':
    start_server(8080)
