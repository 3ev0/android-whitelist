__author__ = 'ivo'
import logging
import json

import plyvel

_log = logging.getLogger()

class LevelDbIf():
    def __init__(self, **kwargs):
        self.dbpath = None
        self.dbif = plyvel.DB(self.dbpath, kwargs)
        _log.info("Connected to Ldb database %s", repr(self.dbif))
        pass

    def write_hashes(self, hashes, value):
        for hash in hashes:
            self.dbif.put(hash, json.dumps(value))

    def read_hash(self, **kwargs):
        for hashtype in kwargs:
            val = self.dbif.get(kwargs[hashtype])
            if val is not None:
                return hash, json.loads(val)

    def batch_write(self, items):
        _log.debug("Batch write of %d items to %s", len(items), repr(self.dbif))
        with self.dbif.write_batch() as wb:
            for hashes,value in items:
                for hash in hashes:
                    wb.put(hash, json.dumps(value))

    def delete(self, **kwargs):
        for hashtype in kwargs:
            self.dbif.delete(kwargs[hashtype])
