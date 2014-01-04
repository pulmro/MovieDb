import os
import logging
import sys
from ConfigParser import RawConfigParser
from ConfigParser import ParsingError
#from collections import OrderedDict

"""
class MultiOrderedDict(OrderedDict):
    def __setitem__(self, key, value):
        if isinstance(value, list) and key in self:
            self[key].extend(value)
        else:
            super(OrderedDict, self).__setitem__(key, value)
"""


cfg = {
    'API_KEY': '22f63eaeba327fde7b8f6f5df3ff3e8f',
    'MOVIEPATH': '',
    'DBPATH': '',
    'LOOPTIME': 60,
    'BLACKLIST': [],
    'SERVERPORT': 8000,
    'LANG': 'en',
    'COUNTRY': 'US',
    'version': '0.2',
    'LOGFILE': ''
}

verbose = False

try:
    #parser = RawConfigParser(dict_type=MultiOrderedDict)
    parser = RawConfigParser()
    configFilePath = os.path.dirname(os.path.realpath(__file__))+'/config'
    parser.readfp(open(configFilePath))
except (ParsingError, IOError) as err:
    print 'Could not parse any configuration file:', err
    print 'Look at the config-sample to make yours.'
    print 'Exiting...'
    sys.exit()

settings = ['MOVIEPATH', 'DBPATH', 'LOOPTIME', 'SERVERPORT', 'LANG', 'COUNTRY']

"""
Start Logging in a file if specified in config, else log to stdoutput
"""
log_level = logging.INFO if verbose else logging.DEBUG
try:
    log_file = parser.get('settings', 'LOGFILE')
    if log_file:
        logging.basicConfig(filename=log_file, level=log_level,
                            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    else:
        raise
except:
    logging.basicConfig(level=log_level, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")


for option in settings:
    if parser.has_option('settings', option):
        cfg[option] = parser.get('settings', option)
    else:
        logging.warning("Using default configuration for %s", option)
if parser.has_option('blacklist', 'folder'):
    cfg['BLACKLIST'] = parser.get('blacklist', 'folder').split(',')

cfg['DBFILE'] = cfg['DBPATH']+'/movie.db'
cfg['CACHEPATH'] = cfg['DBPATH']+'/tmp'
cfg['LOOPTIME'] = float(cfg['LOOPTIME'])

if not os.path.isdir(cfg['DBPATH']):
    try:
        os.mkdir(cfg['DBPATH'])
        os.mkdir(cfg['CACHEPATH'])
    except OSError as e:
        logging.error("I/O error({0}): {1}".format(e.errno, e.strerror) )
    except:
        logging.error("Unexpected error: %s", sys.exc_info()[0])
        raise

if not os.path.isdir(cfg['CACHEPATH']):
    try:
        os.mkdir(cfg['CACHEPATH'])
    except OSError as e:
        logging.error("I/O error({0}): {1}".format(e.errno, e.strerror))
    except:
        logging.error("Unexpected error:%s", sys.exc_info()[0])
        raise


def print_current_settings():
    for key in cfg:
        logging.info("%s : %s", key, cfg[key])


def is_blacklisted(directory):
    """Check if directory is blacklisted or child of a blacklisted one."""
    dir_path = os.path.realpath(directory)
    flag = False
    for bl_dir in cfg['BLACKLIST']:
        bl_dir_path = os.path.realpath(cfg['MOVIEPATH']+"/"+bl_dir)
        if os.path.commonprefix([dir_path, bl_dir_path]) == bl_dir_path:
            logging.info("%s is blacklisted", dir_path)
            flag = True
    return flag