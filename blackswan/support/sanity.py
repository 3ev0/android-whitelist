__author__ = 'ivo'
import os
import os.path
import logging

_log = logging.getLogger(__name__)

def assert_exists(path):
    if not os.path.exists(path):
        _log.error("Path {} does not exist".format(path))
        raise Exception("Path {} does not exist".format(path))

def assert_notexists(path):
    if os.path.exists(path):
        _log.error("Path {} exists".format(path))
        raise Exception("Path {} exists".format(path))