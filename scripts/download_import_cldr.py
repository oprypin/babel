#!/usr/bin/env python3

import contextlib
import hashlib
import os
import shutil
import subprocess
import sys
import zipfile
from urllib.request import urlretrieve

URL = 'http://unicode.org/Public/cldr/42/cldr-common-42.0.zip'
FILENAME = 'cldr-common-42.0.zip'
# Via https://unicode.org/Public/cldr/42/hashes/SHASUM512
FILESUM = '315448fe6a9ac2d5a6a7fd1a27b38c5db30fed053654a803d50e3a8d06aa08ad153e8e57089fa094c561f41a54f37eecda0701b47a1813879902be71945aa38a'
BLKSIZE = 131072


def reporthook(block_count, block_size, total_size):
    bytes_transmitted = block_count * block_size
    cols = shutil.get_terminal_size().columns
    buffer = 6
    percent = float(bytes_transmitted) / (total_size or 1)
    done = int(percent * (cols - buffer))
    bar = ('=' * done).ljust(cols - buffer)
    sys.stdout.write(f'\r{bar}{int(percent * 100): 4d}%')
    sys.stdout.flush()


def log(message):
    sys.stderr.write(f'{message}\n')


def is_good_file(filename):
    if not os.path.isfile(filename):
        log(f"Local copy '{filename}' not found")
        return False
    h = hashlib.sha512()
    with open(filename, 'rb') as f:
        while True:
            blk = f.read(BLKSIZE)
            if not blk:
                break
            h.update(blk)
        digest = h.hexdigest()
        if digest != FILESUM:
            raise RuntimeError(f'Checksum mismatch: {digest!r} != {FILESUM!r}')
        else:
            return True


def main():
    scripts_path = os.path.dirname(os.path.abspath(__file__))
    repo = os.path.dirname(scripts_path)
    cldr_dl_path = os.path.join(repo, 'cldr')
    cldr_path = os.path.join(repo, 'cldr', os.path.splitext(FILENAME)[0])
    zip_path = os.path.join(cldr_dl_path, FILENAME)
    changed = False
    show_progress = (False if os.environ.get("BABEL_CLDR_NO_DOWNLOAD_PROGRESS") else sys.stdout.isatty())

    while not is_good_file(zip_path):
        log(f"Downloading '{FILENAME}' from {URL}")
        tmp_path = f"{zip_path}.tmp"
        urlretrieve(URL, tmp_path, (reporthook if show_progress else None))
        os.replace(tmp_path, zip_path)
        changed = True
        print()
    common_path = os.path.join(cldr_path, 'common')

    if changed or not os.path.isdir(common_path):
        if os.path.isdir(common_path):
            log(f"Deleting old CLDR checkout in '{cldr_path}'")
            shutil.rmtree(common_path)

        log(f"Extracting CLDR to '{cldr_path}'")
        with contextlib.closing(zipfile.ZipFile(zip_path)) as z:
            z.extractall(cldr_path)

    subprocess.check_call([
        sys.executable,
        os.path.join(scripts_path, 'import_cldr.py'),
        common_path])


if __name__ == '__main__':
    main()
