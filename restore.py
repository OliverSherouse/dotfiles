#!/usr/bin/env python3

import logging
import os

from pathlib import Path

logging.basicConfig(level=logging.INFO)


def link(target, source):
    logging.info("Restoring from {0} to {1}".format(source, target))
    if target.is_symlink():
        logging.info("Deleting existing link")
        target.unlink()
    if target.exists():
        backup = Path(str(target) + ".bak")
        target.rename(backup)
        logging.info("Backing up existing {0} to {1}".format(target, backup))
    target.symlink_to(source, source.is_dir())


def main():
    """
    Restore entire current directory to home directory
    """
    target = Path(os.environ["HOME"]).resolve()
    source = Path(__file__).resolve().parent.joinpath("dotfiles")
    for subpath in source.iterdir():
        subtarget = target.joinpath(*f".{subpath.name}".split("__"))
        if subtarget.is_dir():
            subtarget.mkdir(exist_ok=True, parents=True)
            for subsubpath in subpath.iterdir():
                link(subtarget.joinpath(subsubpath.name), subsubpath)
        else:
            link(subtarget, subpath)


if __name__ == "__main__":
    main()
