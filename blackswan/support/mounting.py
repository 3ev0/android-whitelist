__author__ = 'ivo'

import os
import struct
import subprocess
import logging

_log = logging.getLogger(__name__)

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

def is_sparseext4(filepath):
    """
    From ext4_utils/sparse_format.h:
    typedef struct sparse_header {
      __le32    magic;      /* 0xed26ff3a */
      __le16    major_version;  /* (0x1) - reject images with higher major versions */
      __le16    minor_version;  /* (0x0) - allow images with higer minor versions */
      __le16    file_hdr_sz;    /* 28 bytes for first revision of the file format */
      __le16    chunk_hdr_sz;   /* 12 bytes for first revision of the file format */
      __le32    blk_sz;     /* block size in bytes, must be a multiple of 4 (4096) */
      __le32    total_blks; /* total blocks in the non-sparse output image */
      __le32    total_chunks;   /* total chunks in the sparse input image */
      __le32    image_checksum; /* CRC32 checksum of the original data, counting "don't care" */
                    /* as 0. Standard 802.3 polynomial, use a Public Domain */
                    /* table implementation */
    } sparse_header_t;

    #define SPARSE_HEADER_MAGIC 0xed26ff3a
    """
    try:
        headerbytes = open(filepath, "br").read(4)
        (magic,) = struct.unpack("I", headerbytes)
        return magic == 0xed26ff3a
    except Exception():
        return False

def is_ext4(filepath):
    """
    Determine if the file is an ext4 image file.
    First 1024 bytes of file are padding. Then superblock. In superblock at offset 0x38 there should be 2-byte magic
    value of 0xEF53.
    :param filepath: The file to check
    :return:true or false
    """
    try:
        headerbytes = open(filepath, "br").read(4)
        (m) = struct.unpack("1024x62c2c", headerbytes)
        return magic == b"\xed\x26\xff\x3a"
    except Exception():
        return False



def unpack_yaffs(imagepath, destdir):
    _log.info("Extracting Yaffs2 image...")
    fn = os.path.basename(imagepath)
    extractdir = os.path.join(destdir, fn)
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

def mount_image(imagepath, destdir):
    fn = os.path.basename(imagepath)
    mountdir = os.path.join(destdir, fn)
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