#!/usr/bin/env python3

import argparse
import datetime as _dt
import logging
import os
import tempfile

from pathlib import Path


LOG = logging.getLogger("restore")


DEFAULT_IGNORE_DIRS = {"__pycache__", ".git"}
DEFAULT_IGNORE_SUFFIXES = {".pyc"}


class ConflictError(RuntimeError):
    pass


def _now_stamp() -> str:
    return _dt.datetime.now().strftime("%Y%m%d-%H%M%S")


def _unique_backup_path(path: Path, stamp: str) -> Path:
    base = Path(str(path) + f".bak.{stamp}")
    if not base.exists() and not base.is_symlink():
        return base
    i = 1
    while True:
        candidate = Path(str(path) + f".bak.{stamp}.{i}")
        if not candidate.exists() and not candidate.is_symlink():
            return candidate
        i += 1


def _is_same_symlink(target: Path, source: Path) -> bool:
    if not target.is_symlink():
        return False
    try:
        return target.resolve() == source.resolve()
    except FileNotFoundError:
        # Broken symlink.
        return False


def _is_same_file_or_resolves_to_same(target: Path, source: Path) -> bool:
    """Return True if target refers to the same underlying file as source.

    This covers cases where a parent directory is already symlinked into the
    repo (so the target path is a plain file but resolves to the same path),
    and also covers hardlinks.
    """
    if not target.exists() or not source.exists():
        return False
    try:
        if target.resolve() == source.resolve():
            return True
    except FileNotFoundError:
        return False

    try:
        return os.path.samefile(os.fspath(target), os.fspath(source))
    except OSError:
        return False


def _mkdirp(path: Path, *, dry_run: bool) -> None:
    if path.is_dir():
        return
    if path.exists() and not path.is_dir():
        raise ConflictError(
            f"Cannot create directory; path exists and is not a directory: {path}"
        )
    if dry_run:
        LOG.info("MKDIR %s", path)
        return
    LOG.info("MKDIR %s", path)
    path.mkdir(parents=True, exist_ok=True)


def link_file(*, target: Path, source: Path, dry_run: bool, force: bool) -> str:
    """Link one file/symlink from source to target.

    Returns an action string: LINK, SKIP.

    If the target exists and is not already correct:
    - without force: raises ConflictError
    - with force: backs up existing path and replaces it
    """
    if _is_same_symlink(target, source):
        LOG.debug("SKIP already linked %s", target)
        return "SKIP"

    if _is_same_file_or_resolves_to_same(target, source):
        LOG.debug("SKIP already present %s", target)
        return "SKIP"

    if target.exists() or target.is_symlink():
        if not force:
            raise ConflictError(f"Target exists: {target}")

        stamp = _now_stamp()
        backup = _unique_backup_path(target, stamp)
        if dry_run:
            LOG.info("BACKUP %s -> %s", target, backup)
        else:
            LOG.info("BACKUP %s -> %s", target, backup)
            target.rename(backup)

    if dry_run:
        LOG.info("LINK %s -> %s", target, source)
        return "LINK"

    LOG.info("LINK %s -> %s", target, source)
    target.symlink_to(source)
    return "LINK"


def _map_top_level(name: str) -> Path:
    # First component becomes dot-prefixed; __ means path separators.
    # Example: local__bin__scripts -> .local/bin/scripts
    parts = name.split("__")
    parts[0] = f".{parts[0]}"
    return Path(*parts)


def iter_links(source_root: Path, home: Path):
    for top in sorted(source_root.iterdir()):
        if top.name in DEFAULT_IGNORE_DIRS:
            continue

        base_target = home / _map_top_level(top.name)

        if top.is_dir():
            # Merge/stow behavior: walk recursively and link files.
            for src_path in sorted(top.rglob("*")):
                rel = src_path.relative_to(top)
                if any(part in DEFAULT_IGNORE_DIRS for part in src_path.parts):
                    continue
                if src_path.suffix in DEFAULT_IGNORE_SUFFIXES:
                    continue
                if src_path.is_dir():
                    continue
                yield (src_path, base_target / rel)
        else:
            if top.suffix in DEFAULT_IGNORE_SUFFIXES:
                continue
            yield (top, base_target)


def run_restore(*, home: Path, source_root: Path, dry_run: bool, force: bool) -> int:
    counts = {"LINK": 0, "SKIP": 0, "CONFLICT": 0}

    for src, dst in iter_links(source_root, home):
        _mkdirp(dst.parent, dry_run=dry_run)
        try:
            action = link_file(target=dst, source=src, dry_run=dry_run, force=force)
            counts[action] += 1
        except ConflictError as e:
            counts["CONFLICT"] += 1
            LOG.error("CONFLICT %s (%s)", dst, e)

    LOG.info(
        "Done: linked=%d skipped=%d conflicts=%d%s",
        counts["LINK"],
        counts["SKIP"],
        counts["CONFLICT"],
        " (dry-run)" if dry_run else "",
    )
    return 0 if counts["CONFLICT"] == 0 else 2


def _self_test() -> None:
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        home = td / "home"
        repo = td / "repo"
        dotfiles = repo / "dotfiles"
        home.mkdir()
        dotfiles.mkdir(parents=True)

        # ~/.bashrc from dotfiles/bashrc
        (dotfiles / "bashrc").write_text("# bashrc\n", encoding="utf-8")

        # ~/.config/qtile/config.py from dotfiles/config/qtile/config.py
        (dotfiles / "config").mkdir()
        (dotfiles / "config" / "qtile").mkdir(parents=True)
        (dotfiles / "config" / "qtile" / "config.py").write_text(
            "# qtile\n", encoding="utf-8"
        )

        # ~/.local/bin/scripts/tool from dotfiles/local__bin__scripts/tool
        scripts_dir = dotfiles / "local__bin__scripts"
        scripts_dir.mkdir()
        (scripts_dir / "tool").write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")

        # First run links
        rc = run_restore(home=home, source_root=dotfiles, dry_run=False, force=False)
        assert rc == 0
        assert (home / ".bashrc").is_symlink()
        assert (home / ".config" / "qtile" / "config.py").is_symlink()
        assert (home / ".local" / "bin" / "scripts" / "tool").is_symlink()

        # Second run is idempotent
        rc2 = run_restore(home=home, source_root=dotfiles, dry_run=False, force=False)
        assert rc2 == 0

        # Conflict handling
        conflict_path = home / ".bashrc"
        conflict_path.unlink()
        conflict_path.write_text("real file\n", encoding="utf-8")
        rc3 = run_restore(home=home, source_root=dotfiles, dry_run=False, force=False)
        assert rc3 == 2
        rc4 = run_restore(home=home, source_root=dotfiles, dry_run=False, force=True)
        assert rc4 == 0
        assert conflict_path.is_symlink()
        backups = sorted(home.glob(".bashrc.bak.*"))
        assert backups


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Symlink dotfiles into $HOME (merge/stow style)."
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Print actions without modifying files"
    )
    parser.add_argument(
        "--force", action="store_true", help="Backup and replace conflicting targets"
    )
    parser.add_argument(
        "--home",
        default=os.environ.get("HOME", str(Path.home())),
        help="Target home directory (default: $HOME)",
    )
    parser.add_argument(
        "--source",
        default=str(Path(__file__).resolve().parent / "dotfiles"),
        help="Source dotfiles directory (default: ./dotfiles)",
    )
    parser.add_argument("--verbose", action="store_true", help="Enable debug logging")
    parser.add_argument(
        "--self-test", action="store_true", help="Run built-in self-test"
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO)

    if args.self_test:
        _self_test()
        LOG.info("Self-test OK")
        return 0

    home = Path(args.home).expanduser().resolve()
    source_root = Path(args.source).expanduser().resolve()
    return run_restore(
        home=home, source_root=source_root, dry_run=args.dry_run, force=args.force
    )


if __name__ == "__main__":
    raise SystemExit(main())
