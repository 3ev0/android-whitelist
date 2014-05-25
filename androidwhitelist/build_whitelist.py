#/usr/bin/env python
import logging
import argparse
import os
import os.path
import subprocess
import hashlib
import json

import magic
import plyvel

from androidwhitelist import storage

log = None
tempdir = "/tmp"
config = {"tempdir":"/tmp",
          "dbpath": "hashes.db",
          "dbif": None
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
    return mmd5.digest(), msha1.digest(), msha256.digest()

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
    dbif = config["dbif"]
    log.info("Exploring from root %s...", rootpath)

    batch_size = 1024
    batch = []
    for (root, dirs, files) in os.walk(rootpath):
        for fl in files:
            fp = os.path.join(root, fl)
            log.debug("Processing file %s", fp)
            hashes = hash_file(fp)
            batch.append((hashes, {"filepath":fp}))
            if len(batch) >= batch_size:
                config["dbif"].batch_write(batch)
                batch = []
    config["dbif"].batch_write(batch)

    log.info("Done exploring!")

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

    config["dbpath"] = args.output
    if args.format == "ldb":
        config["dbif"] = storage.LevelDbIf(config["dbpath"], create_if_missing=True)
    else:
        raise Exception("db format not implemented")

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
