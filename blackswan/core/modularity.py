__author__ = 'ivo'

import logging
import argparse

from blackswan import config

_log = logging.getLogger(__name__)

class ModuleBase():
    argparser = None

    def __init__(self):
        self.config = {}

    @classmethod
    def register(cls):
        cls.argparser = argparse.ArgumentParser(description=cls.description, prog=cls.modname, add_help=False)
        cls.argparser.add_argument("-b", "--db", default=config.def_db, help="The blackswan db file. Default: {}".format(config.def_db))
        cls.add_args()
        config.modules[cls.modname] = cls
        _log.debug("Module %s registered", cls.modname)
        return

    @classmethod
    def add_args(cls):
        raise NotImplementedError

    def work(self):
        raise NotImplementedError

    def __repr__(self):
        return "<{}({})>".format(self.modname, repr(self.config))

    def parse_args(self, modargs):
        args = self.argparser.parse_args(args=modargs)
        self.config.update(**vars(args))

    def run(self):
        _log.info("Module %s started", self.modname)
        self.work()
        _log.info("Module %s finished", self.modname)

    def configure(self, **kwargs):
        self.config.update(kwargs)
        _log.info("Module %s configured: \n%s", self.modname, repr(self.config))
