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

_log = logging.getLogger()
_tempdir = "/tmp"
_config = {"tempdir":"/tmp",
          "dbpath": "hashes.db",
          "dbif": None
          }

def write_hashes(hashes, value, replace=True):
    num_added, num_procd, dupl = 0, 0, 0
    for hash in hashes:
        num_procd += 1
        if _config["dbif"].get(hash):
            dupl += 1
            if not replace:
                _log.debug("%s allready present in db, not adding", repr(hash))
                continue
        _config["dbif"].put(hash, bytes(json.dumps(value), encoding="utf8"))
        num_added += 1
        _log.debug("%s added to database", repr(hash))
    return num_added, num_procd, dupl

def batch_write(items, replace=True):
    _log.debug("Batch write of %d items to %s", len(items), repr(_config["dbif"]))
    num_added, num_procd, dupl = 0, 0, 0
    with _config["dbif"].write_batch() as wb:
        for hashes,value in items:
            for hash in hashes:
                num_procd += 1
                if _config["dbif"].get(hash):
                    dupl += 1
                    if not replace:
                        _log.debug("%s allready present in db, not adding", repr(hash))
                        continue
                wb.put(hash, bytes(json.dumps(value), encoding="utf8"))
                num_added += 1
                _log.debug("%s added to database", repr(hash))
    return num_added, num_procd, dupl

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
        #_log.debug("%d, %s", parent_obj_id, sum_no_longer_used)
        return (parent_obj_id in range(0,5) and sum_no_longer_used == b"\xFF\xFF")
    except Exception():
        return False

def unpack_yaffs(imagepath):
    _log.info("Extracting Yaffs2 image...")
    fn = os.path.basename(imagepath)
    extractdir = os.path.join(_tempdir, fn)
    if os.path.exists(extractdir):
        if len(os.listdir(extractdir)):
            _log.error("Extract dir %s exists and is not empty", extractdir)
            raise Exception("extractdir exists")
        else:
            os.rmdir(extractdir)
    os.makedirs(extractdir)
    subprocess.check_call(["unyaffs", imagepath, extractdir])
    _log.info("Image extracted to %s", extractdir)
    return extractdir

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
    total_added, total_procd, total_dupl = 0, 0, 0
    for (root, dirs, files) in os.walk(rootpath):
        for fl in files:
            fp = os.path.join(root, fl)
            _log.info("Encountered file %s", fp)
            hashes = hash_file(fp)
            batch.append((hashes, {"source_id": sourceid, "filepath":fp}))
            if len(batch) >= batch_size:
                added, procd, dupl = batch_write(batch)
                total_added, total_procd, total_dupl = total_added + added, total_procd + procd, total_dupl + dupl
                batch = []
    added, procd, dupl = batch_write(batch)
    total_added, total_procd, total_dupl = total_added + added, total_procd + procd, total_dupl + dupl
    _log.info("Done exploring!")
    _log.info("%d records processed", total_procd)
    _log.info("%d records allready in db", total_dupl)

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
    dbcreated = False
    if args.format == "ldb":
        if not os.path.exists(_config["dbpath"]):
            dbcreated = True
        _config["dbif"] = plyvel.DB(_config["dbpath"], create_if_missing=True)
        _log.info("Connected to Ldb database %s", repr(_config["dbif"]))
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
    # In case this script is run as sudo because of mounting, we want to change the owner to actual user
    if os.environ["SUDO_USER"] and dbcreated:
        subprocess.check_call(["chown", "-R", "{}:{}".format(os.environ["SUDO_UID"], os.environ["SUDO_GID"]), _config["dbpath"]])
        _log.info("Owner of %s set to %s:%s", _config["dbpath"],os.environ["SUDO_UID"], os.environ["SUDO_GID"])
    if mounted:
        unmount_image(rootpath)
    if tempdir:
        shutil.rmtree(rootpath)
        _log.info("Temp dir %s deleted", rootpath)

if __name__ == "__main__":
    main()
