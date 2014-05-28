#/usr/bin/env python
import logging
import argparse
import os
import os.path
import subprocess
import hashlib
import json
import shutil
import struct

import magic
import plyvel

from androidwhitelist import storage

_log = logging.getLogger()
_tempdir = "/tmp"
_config = {"tempdir":"/tmp",
          "dbpath": "hashes.db",
          "dbif": None
          }

def hash_file(filepath):
    _log.debug("Hashing %s", filepath)
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

def is_yaffs_image(filepath):
    """
    According to yaffs2 yaffs_guts.c source code:
    struct yaffs_obj_hdr {
        enum yaffs_obj_type type; <-- This can be an int value between 0 and 4 (likely 3)
        int parent_obj_id; <-- Usually 1, but not sure enough to use
        u16 sum_no_longer_used;	/* checksum of name. No longer used */ <-- this is set to 0xFFFF
    """
    if not os.path.isfile(filepath):
        return False
    try:
        headerbytes = open(filepath, "br").read(10)
        (parent_obj_id, sum_no_longer_used) = struct.unpack("I4x2s", headerbytes)
        _log.debug("%d, %s", parent_obj_id, sum_no_longer_used)
        return (parent_obj_id in range(0,5) and sum_no_longer_used == b"\xFF\xFF")
    except Exception():
        return False

def unpack_yaffs(imagepath):
    return

def mount_image(imagepath):
    fn = os.path.basename(imagepath)
    mountdir = os.path.join(_tempdir, fn)
    if os.path.exists(mountdir):
        if len(os.listdir(mountdir)):
            _log.error("Mountdir %s exists and is not empty", mountdir)
            raise Exception("Mountdir exists")
        else:
            os.rmdir(mountdir)
    os.makedirs(mountdir)
    subprocess.check_call(["sudo", "mount",imagepath, mountdir, "-o", "ro"])
    _log.info("%s mounted", imagepath)
    return mountdir

def unmount_image(path):
    subprocess.check_call(["sudo", "umount", path])
    _log.info("%s unmounted", path)

def explore_filesystem(rootpath, sourceid=None):
    dbif = _config["dbif"]
    _log.info("Exploring from root %s...", rootpath)

    batch_size = 1024
    batch = []
    cnt = 0
    for (root, dirs, files) in os.walk(rootpath):
        for fl in files:
            fp = os.path.join(root, fl)
            _log.info("Encountered file %s", fp)
            hashes = hash_file(fp)
            batch.append((hashes, {"source_id": sourceid, "filepath":fp}))
            if len(batch) >= batch_size:
                cnt += dbif.batch_write(batch)
                batch = []
    cnt += dbif.batch_write(batch)
    _log.info("Done exploring! %d records added to database", cnt)

def main():
    parser = argparse.ArgumentParser(description="Build hash list from images files or dirs")
    parser.add_argument("source", help="Image file or dir")
    parser.add_argument("-i", "--id", default="unknown", help="Provide source identifier to be stored with the hashes")
    parser.add_argument("-d", "--debug", action="store_true", help="Enable debugging")
    parser.add_argument("-o", "--output", default="hashes.db", help="The output database. If existing, the data is added. Default: hashes.db")
    parser.add_argument("-f", "--format", choices=["ldb", "sql"], default="ldb", help="The output format. Default: ldb")
    args = parser.parse_args()
    
    logging.basicConfig(level=logging.DEBUG if args.debug else logging.INFO)
    global _log

    _config["dbpath"] = args.output
    if args.format == "ldb":
        _config["dbif"] = storage.LevelDbIf(_config["dbpath"], create_if_missing=True)
    else:
        raise Exception("db format not implemented")

    source = os.path.abspath(args.source)
    _log.info("New source: %s...", source)
    tempdir, mounted = False, False
    if not os.path.exists(source):
        _log.error("Path does not exist")
    if os.path.isfile(source):
        if "ext4" in str(magic.from_file(source), encoding="utf8"):
            _log.info("Smells like ext4 image")
            rootpath = mount_image(source)
            mounted = True
        elif is_yaffs_image(source):
            _log.info("Smells like yaffs image")
            rootpath = unpack_yaffs(source)
        else:
            _log.error("Unrecognized file type")
            raise Exception("Unrecognized file type")
        tempdir = True
    else:
        _log.info("assuming this the root of file tree")
        rootpath = source

    explore_filesystem(rootpath, sourceid=args.id)
    if mounted:
        unmount_image(rootpath)

if __name__ == "__main__":
    main()
