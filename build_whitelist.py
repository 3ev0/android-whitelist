#/usr/bin/env python
import logging
import argparse
import os
import os.path
import subprocess
import hashlib

import magic
import plyvel

log = None
tempdir = "/tmp"
config = {"tempdir":"/tmp",
          "storefunc": None
          }

def hash_file(filepath):
    with open(filepath, mode="br") as fh:
        mmd5 = hashlib.md5()
        msha1 = hashlib.sha1()
        msha256 = hashlib.sha256()
        blob = fh.read(1024*1024)
        while blob:
            mmd5.update(blob)
            msha1.update(blob)
            msha256.update(blob)
            blob = fh.read(1024*1024)
    return mmd5.hexdigest(), msha1.hexdigest(), msha256.hexdigest()

def unpack_yaffs(imagepath):
    return

def mount_image(imagepath):
    fn = os.path.basename(imagepath)
    mountdir = os.makedirs(os.path.join(tempdir, fn))
    subprocess.checkcall("mount %s %s -o ro".format(imagepath, mountdir))
    return mountdir

def unmount_image(imagepath):
    return

def explore_filesystem(rootpath):
    storefunc = config["storefunc"]
    log.info("Exploring from root %s...", rootpath)
    for (root, dirs, files) in os.walk(rootpath):
        for fl in files:
            fp = os.path.join(root, fl)
            log.debug("Processing file %s", fp)
            md5, sha1, sha256 = hash_file(fp)
            storefunc((md5, sha1, sha256), filepath=fp)
    log.info("Done exploring!")

def store_ldb(hashes, **kwargs):
    log.debug("stored hashes %s", repr(hashes))
    return True

def store_sql(hashes, **kwargs):
    log.debug("stored hashes %s", repr(hashes))
    return True


def main():
    parser = argparse.ArgumentParser(description="Build hash list from images files or dirs")
    parser.add_argument("source", nargs="+", help="Image file or dir")
    parser.add_argument("-d", "--debug", action="store_true", help="Enable debugging")
    parser.add_argument("-o", "--output", default="hashes.db", help="The output database. If existing, the data is added. Default: hashes.db")
    parser.add_argument("-f", "--format", choices=["ldb", "sql"], default="ldb", help="The output format. Default: ldb")
    args = parser.parse_args()
    
    logging.basicConfig(level=logging.DEBUG if args.debug else logging.INFO)
    global log
    log = logging.getLogger()
    
    if args.format == "ldb":
        config["storefunc"] = store_ldb
    else:
        config["storefunc"] = store_sql 

    for source in args.source:
        source = os.path.abspath(source)
        log.info("New source: %s...", source)
        tempdir, mounted = False, False
        if not os.path.exists(source):
            log.error("Path does not exist")
            continue
        if os.path.isfile(source):
            if "ext4" in str(magic.from_file(source), encoding="utf8"):
                log.info("file magic contains 'ext4', assuming ext4 image")
                mounted = True
            else:
                log.info("Assuming yaffs image")
            tempdir = True
        else:
            log.info("assuming this the rootdir of a filesystem")
            rootpath = source

        explore_filesystem(rootpath)



if __name__ == "__main__":
    main()
