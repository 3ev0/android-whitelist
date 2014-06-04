__author__ = 'ivo'

import logging
import os.path
import datetime
import binascii

from blackswan.core import modularity,database
from blackswan.core.database import MetaFile
from blackswan import config
from blackswan.support import sanity, progressbar

import plyvel

_log = logging.getLogger(__name__)

class LdbHashFilter(modularity.ModuleBase):

    description = "Exclude files from the database by filtering on hashes in LevelDb database"

    def work(self):
        dbpath = os.path.abspath(self.config["db"])
        filterpath = os.path.abspath(self.config["filter"])

        sanity.assert_exists(dbpath)
        _log.info("Database: %s", os.path.abspath(dbpath))
        sanity.assert_exists(filterpath)
        try:
            filterDbIf = plyvel.DB(filterpath, create_if_missing=False)
        except plyvel.IOError as err:
            _log.error("Could not open as ldb database %s", filterpath)
            _log.error(repr(err))
            raise err
        _log.info("Filter: %s", os.path.abspath(filterpath))


        destdbIf = database.DbIf("sqlite:///{}".format(dbpath))
        destdbIf.add_db_info(key="filter_applied", value=filterpath)
        destdbIf.add_db_info(key="updated", value=datetime.datetime.now(), replace=True)
        total = destdbIf.Session.query(database.MetaFile).filter(MetaFile.excluded == False).count()
        exclcnt = cnt = 0
        pbar = progressbar.Progressbar(total, "Filtering database...", unit="files")
        for mf in destdbIf.Session.query(MetaFile).filter(MetaFile.excluded == False):
            res = filterDbIf.get(binascii.unhexlify(mf.sha1))
            if res:
                _log.debug("Found a match: %s", str(res, encoding="utf8"))
                mf.excluded = True
                exclcnt += 1
            cnt += 1
            if not (cnt % 10):
                pbar.update(10)
        destdbIf.Session.commit()
        pbar.finish()
        _log.info("%d of %d records excluded from %s", exclcnt, total, dbpath)
        return True
        pass

    @classmethod
    def add_args(cls):
        cls.argparser.add_argument("--filter", "-f", required=True, help="Reference set against which is compared. Should be ldb database")
        pass

LdbHashFilter.register()

def main():
    hashfilter = LdbHashFilter()
    hashfilter.parse_args()
    hashfilter.run()

if __name__ == "__main__":
    main()