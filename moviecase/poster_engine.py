import os
import threading
import urllib
import logging
import config


class PosterDownloadQueue(object):
    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(PosterDownloadQueue, cls).__new__(cls)
            cls.instance.to_download = set()
        return cls.instance


class PosterDownloaderThread(threading.Thread):
    def __init__(self, thread_id, name, counter):
        threading.Thread.__init__(self)
        self.name = name

    def run(self):
        logging.debug("Starting Thread %s", self.name)
        download_posters(self.name)
        logging.debug("Finished Thread %s", self.name)


def download_posters(thread_name):
    poster_queue = PosterDownloadQueue()
    logging.debug("Queue length: %d", len(poster_queue.to_download))
    while poster_queue.to_download:
        (url, size) = poster_queue.to_download.pop()
        logging.debug("%s is downloading poster from %s", thread_name, url)
        fetch_poster(url, size)
    logging.debug("%s finished downloading posters.", thread_name)


def fetch_poster(url, size_dir):
    try:
        basename = os.path.basename(url)
        make_dir(size_dir)
        dest_file = "%s/%s/%s" % (config.cfg['DBPATH'], size_dir, basename)
        urllib.urlretrieve(url, dest_file)
    except IOError as err:
        logging.exception("Error while downloading %s, %s", url, err)


def make_dir(size):
    dir_path = "%s/%s" % (config.cfg['DBPATH'], size)
    if not os.path.isdir(dir_path):
        try:
            os.mkdir(dir_path)
        except OSError as e:
            logging.error("I/O error({0}): {1}".format(e.errno, e.strerror) )
        except:
            logging.error("Unexpected error.")
            raise