import os, logging
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

"""Start Logging"""
logging.basicConfig(filename='MovieDb.log', level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

cfg={'API_KEY':'22f63eaeba327fde7b8f6f5df3ff3e8f', 'MOVIEPATH':'/data/Video/Film', 'DBPATH':'/home/emanuele/devel/moviedb/data', 'LOOPTIME':60, 'BLACKLIST':[], 'SERVERPORT':8000, 'LANG':'en','COUNTRY':'US'}

cfg['version']=0.1

try:
	#parser = RawConfigParser(dict_type=MultiOrderedDict)
	parser = RawConfigParser()
	configFilePath = os.path.dirname(os.path.realpath(__file__))+'/config'
	parser.read(configFilePath)
except ParsingError, err:
    print 'Could not parse:', err
    print 'Using Default configuration'

settings=['MOVIEPATH', 'DBPATH', 'LOOPTIME', 'SERVERPORT', 'LANG', 'COUNTRY']

for option in settings:
	if parser.has_option('settings', option):
		cfg[option]=parser.get('settings', option)
	else:
		logging.warning("Using default configuration for %s", option)
if parser.has_option('blacklist','folder'):
	cfg['BLACKLIST']=parser.get('blacklist','folder').split(',')

cfg['DBFILE']=cfg['DBPATH']+'/movie.db'
cfg['CACHEPATH']=cfg['DBPATH']+'/tmp'
cfg['LOOPTIME'] = float(cfg['LOOPTIME'])

if not os.path.isdir(cfg['DBPATH']):
	try:
		os.mkdir(cfg['DBPATH'])
		os.mkdir(cfg['CACHEPATH'])
	except OSError as e:
		logging.error( "I/O error({0}): {1}".format(e.errno, e.strerror) )
	except:
		logging.error("Unexpected error: %s", sys.exc_info()[0])
		raise

if not os.path.isdir(cfg['CACHEPATH']):
	try:
		os.mkdir(cfg['CACHEPATH'])
	except OSError as e:
		logging.error( "I/O error({0}): {1}".format(e.errno, e.strerror))
	except:
		logging.error("Unexpected error:%s", sys.exc_info()[0])
		raise

def printCurrentSettings():
	for key in cfg:
		logging.info("%s : %s",key,cfg[key])
