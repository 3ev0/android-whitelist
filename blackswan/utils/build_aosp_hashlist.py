__author__ = 'ivo'

import requests
import re
import tempfile
import os.path
import os
import logging
import tarfile

_log = logging.getLogger()

TMPDIR = tempfile.gettempdir()

def scrape_links():
    index_url = "https://developers.google.com/android/nexus/images"
    index_page = requests.get(index_url)
    results = re.findall("http.*\.tgz", index_page.text)
    _log.info("Scraped %d links from %s", len(results), index_url)
    return results

def get_filename(url):
    return url.split("/")[-1]

def images(members):
    for tarinfo in members:
        if os.path.splitext(tarinfo.name)[1] == ".img":
            yield tarinfo

def untar_images(fp, destdir):
    with tarfile.open(fp) as tar:
        for member in images(tar):
            fn = os.path.basename(member.name)
            destpath = os.path.join(destdir, fn)
            with tar.extractfile(member) as memberfh, open(destpath, "wb") as destfh:
                blob = memberfh.read(4096)
                while blob:
                    destfh.write(blob)
                    blob = memberfh.read(4096)
            _log.info("Extracted %s to %s", member.name, destpath)

def build():
    sources = scrape_links()
    for source in sources:
        _log.info("Processing %s...", source)
        fn = get_filename(source)
        fp = os.path.join(TMPDIR, fn)
        r = requests.get(source, stream=True)
        with open(fp, 'wb') as fd:
            for chunk in r.iter_content(4096):
                fd.write(chunk)
        _log.info("File downloaded to %s", fp)
        untardir = os.path.join(TMPDIR, os.path.splitext(fn)[0])
        untar_images(fp, untardir)
        return

def main():
    logging.basicConfig(level=logging.DEBUG)
    build()
    pass

if __name__ == "__main__":
    main()