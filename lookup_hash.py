__author__ = 'ivo'
import argparse
import sys
import binascii

import plyvel

def main():
    parser = argparse.ArgumentParser(description="Lookup hash in ldb database")
    parser.add_argument("ldb", help="The database to look in")
    args = parser.parse_args()

    dbif = plyvel.DB(args.ldb, create_if_missing=False)
    for line in sys.stdin:
        hashstr = line.strip()
        try:
            hashbytes = binascii.unhexlify(hashstr)
        except binascii.Error as err:
            print("{} error: {}".format(hashstr, str(err)))
            continue
        val = dbif.get(hashbytes)
        if val:
            print("{} found: {}".format(hashstr, str(val, encoding="utf8")))
        else:
            print("{} not found!".format(hashstr))

if __name__ == "__main__":
    main()



