import os
import json
import logging
import logging.config

class _logConst():

    PKG_DIR = os.path.dirname(os.path.abspath(__file__))
    BASE_DIR = PKG_DIR + '/..'
    LOG_DIR = BASE_DIR + '/logs'
    LOG_SETTINGS = BASE_DIR + '/logging.json'
    ERROR_LOG = LOG_DIR +'/error.log'
    MAIN_LOG = LOG_DIR +'/main.log'

class frmkLog():
    
    def __init__(self):
        c=_logConst()
        print('\n\nkatelibs package base dir: %s\n\n'%c.PKG_DIR)
        with open(c.LOG_SETTINGS,"r",encoding="utf-8") as fd:
            D = json.load(fd)
            D.setdefault('version',1)
            logging.config.dictConfig(D)

    def getLogger(self,name):
        
        return logging.getLogger(name)
        
