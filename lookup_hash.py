__author__ = 'ivo'
import argparse
import sys
import binascii


from androidwhitelist import storage

def hashtype(hashstr):
    if len(hashstr) == 32:
        return "md5"
    elif len(hashstr) == 20:
        return "sha1"
    else:
        return "sha256"

def main():
    parser = argparse.ArgumentParser(help="Lookup hash in ldb database")
    parser.add_argument("ldb", description="The database to look in")
    args = parser.parse_args()

    for line in sys.stdin:
        hashstr = line.strip()


if __name__ == "__main__":
    main()



