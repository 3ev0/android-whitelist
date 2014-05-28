__author__ = 'ivo'
import logging
import json

import plyvel

_log = logging.getLogger()

class LevelDbIf():
    def __init__(self, dbpath, **kwargs):
        self.dbpath = dbpath
        self.dbif = plyvel.DB(self.dbpath, **kwargs)
        _log.info("Connected to Ldb database %s", repr(self.dbif))
        pass

    def write_hashes(self, hashes, value):
        cnt = 0
        for hash in hashes:
            if self.dbif.get(hash):
               _log.debug("%s allready present in db, not adding", repr(hash))
            else:
                self.dbif.put(hash, bytes(json.dumps(value), encoding="utf8"))
                cnt += 1
                _log.debug("%s added to database", repr(hash))
        return cnt

    def read_hash(self, **kwargs):
        for hashtype in kwargs:
            val = self.dbif.get(kwargs[hashtype])
            if val is not None:
                return hash, json.loads(str(val, encoding="utf8"))

    def batch_write(self, items):
        _log.debug("Batch write of %d items to %s", len(items), repr(self.dbif))
        cnt = 0
        with self.dbif.write_batch() as wb:
            for hashes,value in items:
                for hash in hashes:
                    if self.dbif.get(hash):
                       _log.debug("%s allready present in db, not adding", repr(hash))
                    else:
                        wb.put(hash, bytes(json.dumps(value), encoding="utf8"))
                        cnt += 1
                        _log.debug("%s added to database", repr(hash))
        return cnt

    def delete(self, **kwargs):
        for hashtype in kwargs:
            self.dbif.delete(kwargs[hashtype])
