import argparse
import logging
import os
import datetime
import stat
import hashlib

import magic

import blackswan
from blackswan.support import progressbar
from blackswan.core import modularity
from blackswan.core import database
from blackswan import config

_log = logging.getLogger(__name__)

class Explore(modularity.ModuleBase):
    description = "Explore filesystem and store file metadata in sqlite database file."

    @staticmethod
    def hash_file(fp, hexdigest=True):
        if isinstance(fp, str):
            fp = open(fp, "br")
        BUF_SIZE = 4096
        hasher_sha1 = hashlib.sha1()
        hasher_md5 = hashlib.md5()
        hasher_sha256 = hashlib.sha256()
        while True:
            chunk = fp.read(BUF_SIZE)
            if not chunk:
                break
            hasher_sha1.update(chunk)
            hasher_md5.update(chunk)
            hasher_sha256.update(chunk)
        if hexdigest:
            return hasher_sha1.hexdigest(), hasher_md5.hexdigest(), hasher_sha256.hexdigest()
        else:
            return hasher_sha1.digest(), hasher_md5.digest(), hasher_sha256.digest()

    @staticmethod
    def files(rootdir):
        """
        Generator function. Traverse filesystem from rootdir.
        Does not yield symbolic links and does not follow symlinks to dirs (due to os.walk functionality).
        @yield: absolute filepath
        """
        for (root, dirs, files) in os.walk(rootdir, followlinks=False):
            for fn in files:
                yield (os.path.relpath(os.path.join(root, fn), rootdir), os.path.join(root, fn))

    @staticmethod
    def get_dirtree_size(rootdir):
        """ Get total dir tree size.
        @return: (total files, total bytes, skipped)
        """
        total_size = 0
        total_files = 0
        skipped = 0
        for (root, dirs, files) in os.walk(rootdir, followlinks=False):
            total_files += len(files)
            for fl in files:
                try:
                    total_size += os.lstat(os.path.join(root, fl)).st_size
                except OSError:
                    skipped += 1
        return (total_files, total_size, skipped)


    def work(self):
        fsdb = self.config["db"]
        _log.info("Initializing database %s...", fsdb)
        if os.path.isfile(fsdb):
            raise Exception("{} allready exists!".format(fsdb))
        dbif = database.DbIf("sqlite:///{}".format(fsdb))
        dbif.init_db(dbinfos={"rootpath": os.path.abspath(self.config["rootpath"]),
                              "program_version": blackswan.__version__,
                              "dbpath": os.path.abspath(fsdb),
                              "created": str(datetime.datetime.now()),
                              "module": __file__})
        _log.info("Calculating file system size...")
        (total_files, total_size, skipped) = Explore.get_dirtree_size(self.config["rootpath"])
        if skipped:
            _log.warning("File system size calc skipped %d files due to errors", skipped)
        _log.info("Total files found: %d (%d MB)", total_files, round(total_size/1024/1024))
        _log.info("Exploring dir tree at %s", self.config["rootpath"])
        pbar = progressbar.Progressbar(total_files, "Exploring file system...", "files")
        count = 0
        errcount = 0
        for (relpath, fullpath) in Explore.files(self.config["rootpath"]):
            count += 1
            metafile = database.MetaFile()
            _log.debug("Processing %s...", relpath)
            try:
                sinfo = os.lstat(fullpath)
                metafile.size = sinfo.st_size
                metafile.lastmodified = datetime.datetime.fromtimestamp(sinfo.st_mtime)
                metafile.created = datetime.datetime.fromtimestamp(sinfo.st_mtime)
                metafile.lastaccess = datetime.datetime.fromtimestamp(sinfo.st_mtime)
                metafile.uid = sinfo.st_uid
                metafile.gid = sinfo.st_gid
                metafile.permissions = sinfo.st_mode
                if stat.S_ISLNK(sinfo.st_mode):
                    metafile.stmode_type = "symlink"
                elif not stat.S_ISREG(sinfo.st_mode):
                    metafile.stmode_type = "other"
                else:
                    metafile.stmode_type = "regular"
                    try:
                        magicbytes = magic.from_file(fullpath, mime=False)
                        metafile.magic = str(magicbytes, "utf-8") if magicbytes else ""
                    except magic.MagicException as exc: # Magic is buggy as of 0.4.6
                        _log.warning("Magic failed identifying magic of %s", fullpath)
                        metafile.magic = ""
                    try:
                        magicbytes = magic.from_file(fullpath, mime=True)
                        metafile.mimetype = str(magicbytes, "utf-8") if magicbytes else ""
                    except magic.MagicException as exc:
                        _log.warning("Magic failed identifying mimetype of %s", fullpath)
                        metafile.mimetype = ""
                    metafile.path = relpath
                    metafile.extension = os.path.splitext(relpath)[1]
                    with open(fullpath, "rb") as ifh:
                        (metafile.sha1, metafile.md5, metafile.sha256) = self.hash_file(ifh, hexdigest=True)
                    dbif.Session.add(metafile)
            except IOError:
                _log.error("Error processing %s (skipping)", relpath)
                errcount += 1
            except OSError:
                _log.error("Error processing %s (skipping)", relpath)
                errcount += 1
            finally:
                pbar.update(1)
        dbif.Session.commit()
        pbar.finish()
        _log.info("%d files found", count)
        _log.info("%d problematic files encountered", errcount)

    @classmethod
    def add_args(cls):
        cls.argparser.add_argument("rootpath", help="The root of the dirtree to traverse")

Explore.register()

def main():
    explorer = Explore()
    explorer.parse_args()
    explorer.run()

if __name__ == "__main__":
    main()