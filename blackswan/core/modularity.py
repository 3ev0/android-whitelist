__author__ = 'ivo'

import logging
import argparse

from blackswan import config

_log = logging.getLogger(__name__)

modules = {}

class ModuleBase():
    def __init__(self):
        self.config = {}

    @classmethod
    def register(cls):
        cls.argparser = argparse.ArgumentParser(description=cls.description)
        cls.argparser.add_argument("-d", "--debug", action="store_true", help="Enable debugging")
        cls.argparser.add_argument("-b", "--db", default=config.def_db, help="The blackswan db file. Default: {}".format(config.def_db))
        cls.add_args()
        modules[cls.__name__] = cls
        _log.info("Module %s registered", cls.__name__)
        return

    def parse_args(self):
        args = self.argparser.parse_args()
        if args.debug:
            config.set_debug()
        self.configure(**vars(args))
        return True

    @classmethod
    def add_args(cls):
        raise NotImplementedError

    def work(self):
        raise NotImplementedError

    def __repr__(self):
        return "<{}({})>".format(self.__name__, repr(self.config))

    def run(self):
        _log.info("Plugin %s started", self.__class__.__name__)
        self.work()
        _log.info("Plugin %s finished", self.__class__.__name__)

    def configure(self, **kwargs):
        self.config.update(kwargs)
        _log.info("Module %s configured: \n%s", self.__class__.__name__, repr(self.config))
