__author__ = 'ivo'

import logging
import os.path
import datetime

from sqlalchemy import or_

from blackswan.core import modularity,database
from blackswan.core.database import MetaFile
from blackswan import config
from blackswan.modules import explore
from blackswan.support import sanity, progressbar

_log = logging.getLogger(__name__)

DEF_FILTERDB = "filter.db"

class HashFilter(modularity.ModuleBase):

    description = "Exclude files from the database by filtering by files in some dir tree or blackswan database"
    modname = "hashfilter"

    @staticmethod
    def create_db(rootpath, tempdb):
        explorer = modularity.modules["Explore"]()
        explorer.configure(rootpath=rootpath, db=tempdb)
        explorer.run()
        return tempdb

    @staticmethod
    def filter_type(dbpath):
        if os.path.isfile(dbpath):
            return "sqlite"
        elif os.path.isdir(dbpath):
            return "dirtree"
        else:
            _log.error("Unknown db type for %s", dbpath)
            raise Exception("Unknown db type")

    def work(self):
        dbpath = os.path.abspath(self.config["db"])
        filterpath = os.path.abspath(self.config["filter"])

        sanity.assert_exists(dbpath)
        _log.info("Database: %s", os.path.abspath(dbpath))
        sanity.assert_exists(filterpath)
        _log.info("Filter: %s (assuming %s)", os.path.abspath(filterpath), HashFilter.filter_type(filterpath))

        if HashFilter.filter_type(filterpath) == "sqlite":
            filterDbIf = database.DbIf("sqlite:///{}".format(filterpath))
        else:
            tempdb = DEF_FILTERDB
            if os.path.exists(tempdb):
                os.remove(tempdb)
            tempdb = HashFilter.create_db(filterpath, tempdb)
            filterDbIf = database.DbIf("sqlite:///{}".format(tempdb))

        destdbIf = database.DbIf("sqlite:///{}".format(dbpath))
        destdbIf.add_db_info(key="filter_applied", value=filterpath)
        destdbIf.add_db_info(key="updated", value=datetime.datetime.now(), replace=True)
        total = destdbIf.Session.query(database.MetaFile).filter(MetaFile.excluded == False).count()
        exclcnt = cnt = 0
        pbar = progressbar.Progressbar(total, "Filtering database...", unit="files")
        for mf in destdbIf.Session.query(MetaFile).filter(MetaFile.excluded == False):
            if filterDbIf.Session.query(MetaFile).filter(or_(MetaFile.sha1 == mf.sha1, MetaFile.md5 == mf.md5, MetaFile.sha256 == mf.sha256)).first() is not None:
                _log.debug("Found a match: %s", mf.path)
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
        cls.argparser.add_argument("--filter", "-f", required=True, help="Reference set against which is compared. May be dir or sqlite file")
        pass

HashFilter.register()

def main():
    hashfilter = HashFilter()
    hashfilter.parse_args()
    hashfilter.run()

if __name__ == "__main__":
    main()