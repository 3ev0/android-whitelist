__author__ = 'ivo'

import sys
import logging

console = sys.stdout
def_db = "blackswan.db"

def config_log():
    log = logging.getLogger()
    log_level = logging.INFO
    log.setLevel(log_level)
    formatter = logging.Formatter('%(asctime)s|%(module)s|%(levelname)s|%(message)s')#, "%Y-%m-%d %H:%M:%S")
    shandler = logging.StreamHandler()
    shandler.setLevel(logging.DEBUG)
    shandler.setFormatter(formatter)
    log.addHandler(shandler)
    return

def set_debug():
    log = logging.getLogger()
    log.setLevel(logging.DEBUG)
    return

config_log()