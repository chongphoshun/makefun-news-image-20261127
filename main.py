#!/usr/bin/env python3
"""Deliver the make.fun news-image-20261127 entry image.

Standard library only, no network. The front page is rendered at build
time by draw.py (Pillow); this program only carries the finished
``entry.png`` into the grader's output directory and proves the delivered
copy is byte-identical to the one in the repository.

The image lives next to this file, so the program works from any working
directory. The destination is picked in this order: ``--out <dir>`` on
the command line, then the ``MAKEFUN_OUTPUT_DIR`` environment variable,
then ``/output``.

Exit 0 means the entry is in place, exactly 1024x1024, and its sha256
matches the repository copy. Anything else is an error on stderr with a
non-zero exit.
"""

import argparse
import hashlib
import os
import shutil
import struct
import sys
from pathlib import Path

ENTRY_NAME = "entry.png"
FALLBACK_OUT = "/output"
WANT_WIDTH = 1024
WANT_HEIGHT = 1024

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def parse_args(argv):
    parser = argparse.ArgumentParser(
        description="Copy entry.png into the output directory and verify it.")
    parser.add_argument(
        "--out", metavar="DIR",
        help="output directory (default: $MAKEFUN_OUTPUT_DIR or /output)")
    return parser.parse_args(argv)


def output_dir(args):
    if args.out:
        return Path(args.out)
    env = os.environ.get("MAKEFUN_OUTPUT_DIR")
    if env:
        return Path(env)
    return Path(FALLBACK_OUT)


def digest(path):
    total = hashlib.sha256()
    with open(path, "rb") as stream:
        while True:
            block = stream.read(1 << 16)
            if not block:
                break
            total.update(block)
    return total.hexdigest()


def png_dimensions(path):
    """Read width/height out of the PNG header, rejecting anything else."""
    with open(path, "rb") as stream:
        head = stream.read(33)
    if len(head) < 33:
        raise ValueError("%s: file too short to be a PNG" % path)
    if head[:8] != PNG_SIGNATURE:
        raise ValueError("%s: bad PNG signature" % path)
    if head[12:16] != b"IHDR":
        raise ValueError("%s: first chunk is not IHDR" % path)
    width, height = struct.unpack(">II", head[16:24])
    return width, height


def check_image(path):
    width, height = png_dimensions(path)
    if (width, height) != (WANT_WIDTH, WANT_HEIGHT):
        raise ValueError(
            "%s: image is %dx%d, expected %dx%d"
            % (path, width, height, WANT_WIDTH, WANT_HEIGHT))


def deliver(source, dest_dir):
    """Copy source into dest_dir/entry.png and prove the copy is exact."""
    check_image(source)
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / ENTRY_NAME
    if dest.resolve() == source.resolve():
        raise ValueError("refusing to copy %s onto itself" % source)
    shutil.copyfile(source, dest)
    check_image(dest)
    want = digest(source)
    got = digest(dest)
    if want != got:
        raise ValueError(
            "%s: copy hash %s != source hash %s" % (dest, got, want))
    return dest, want


def main(argv):
    args = parse_args(argv)
    here = Path(__file__).resolve().parent
    source = here / ENTRY_NAME
    if not source.is_file():
        print("error: %s not found (run draw.py first)"
              % source, file=sys.stderr)
        return 1
    try:
        dest, sha = deliver(source, output_dir(args))
    except (ValueError, OSError) as problem:
        print("error: %s" % problem, file=sys.stderr)
        return 1
    print("delivered %s (%d bytes, sha256 %s)"
          % (dest, dest.stat().st_size, sha))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
