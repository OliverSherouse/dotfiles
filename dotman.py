#!/usr/bin/env python3

import argparse
import datetime as _dt
import logging
import os
import shutil
import tempfile

from pathlib import Path


LOG = logging.getLogger("dotman")


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
        return False


def _is_same_file_or_resolves_to_same(target: Path, source: Path) -> bool:
    """True if target refers to the same underlying file/dir as source.

    This covers:
    - correct symlinks
    - hardlinks
    - paths inside a symlinked parent directory that resolve into the repo
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


def _backup_existing(path: Path, *, dry_run: bool) -> Path:
    stamp = _now_stamp()
    backup = _unique_backup_path(path, stamp)
    if dry_run:
        LOG.info("BACKUP %s -> %s", path, backup)
        return backup
    LOG.info("BACKUP %s -> %s", path, backup)
    path.rename(backup)
    return backup


def link_path(*, target: Path, source: Path, dry_run: bool, force: bool) -> str:
    """Symlink target -> source.

    Returns: LINK or SKIP.
    """
    if _is_same_symlink(target, source) or _is_same_file_or_resolves_to_same(
        target, source
    ):
        LOG.debug("SKIP already present %s", target)
        return "SKIP"

    if target.exists() or target.is_symlink():
        # Allow replacing an empty placeholder directory without --force when
        # the source is a directory and the target is a real directory.
        if (
            source.is_dir()
            and target.exists()
            and target.is_dir()
            and not target.is_symlink()
            and not any(target.iterdir())
        ):
            if dry_run:
                LOG.info("RMDIR %s", target)
            else:
                LOG.info("RMDIR %s", target)
                target.rmdir()
        else:
            if not force:
                raise ConflictError(f"Target exists: {target}")
            _backup_existing(target, dry_run=dry_run)

    if dry_run:
        LOG.info("LINK %s -> %s", target, source)
        return "LINK"

    LOG.info("LINK %s -> %s", target, source)
    target.symlink_to(source, target_is_directory=source.is_dir())
    return "LINK"


def _map_top_level_to_home(name: str) -> Path:
    parts = name.split("__")
    parts[0] = f".{parts[0]}"
    return Path(*parts)


def iter_restore_links(source_root: Path, home: Path):
    for top in sorted(source_root.iterdir()):
        if top.name in DEFAULT_IGNORE_DIRS:
            continue

        base_target = home / _map_top_level_to_home(top.name)

        if top.is_dir():
            # For explicit ~/.config/<app> subtrees, symlink the whole directory.
            if top.name.startswith("config__"):
                yield (top, base_target)
                continue

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

    for src, dst in iter_restore_links(source_root, home):
        _mkdirp(dst.parent, dry_run=dry_run)
        try:
            action = link_path(target=dst, source=src, dry_run=dry_run, force=force)
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


def repo_dest_for_home_path(
    *, home_path: Path, home: Path, dotfiles_root: Path
) -> Path:
    # For stow/unstow, do not resolve symlinks: we want to map the *path in $HOME*.
    home_path = Path(os.path.abspath(home_path.expanduser()))
    rel = home_path.relative_to(home)

    if not rel.parts:
        raise ValueError("Cannot map home root")

    top = rel.parts[0]
    if not top.startswith("."):
        raise ValueError(f"Refusing to stow non-dot path under $HOME: {home_path}")

    parts = rel.parts
    if top == ".config":
        if len(parts) < 2:
            raise ValueError("Expected ~/.config/<app>/...")
        app = parts[1]
        rest = parts[2:]
        return dotfiles_root / f"config__{app}" / Path(*rest)

    if parts[:3] == (".local", "bin", "scripts"):
        rest = parts[3:]
        return dotfiles_root / "local__bin__scripts" / Path(*rest)

    # Generic dotdir/dotfile.
    clean_top = top[1:]
    rest = parts[1:]
    return dotfiles_root / clean_top / Path(*rest)


def run_stow(
    *,
    paths: list[str],
    home: Path,
    dotfiles_root: Path,
    dry_run: bool,
    force: bool,
) -> int:
    rc = 0
    for raw in paths:
        src = Path(raw).expanduser()
        if not src.is_absolute():
            src = Path.cwd() / src
        # Do not resolve symlinks here; treat the requested path as-is.
        src = Path(os.path.abspath(src))

        if not src.exists() and not src.is_symlink():
            LOG.error("Missing path: %s", src)
            rc = 2
            continue

        if src.is_symlink():
            try:
                target = src.resolve(strict=True)
            except FileNotFoundError:
                LOG.error("Broken symlink (cannot stow): %s", src)
                rc = 2
                continue

            # If it's already stowed into this repo, treat it as a no-op.
            try:
                target.relative_to(dotfiles_root)
            except ValueError:
                LOG.error(
                    "Refusing to stow symlink path (pass the real file/dir): %s", src
                )
                rc = 2
                continue

            LOG.debug("SKIP already stowed %s", src)
            continue

        try:
            src.relative_to(home)
        except ValueError:
            LOG.error("Refusing to stow path outside $HOME: %s", src)
            rc = 2
            continue

        dst = repo_dest_for_home_path(
            home_path=src, home=home, dotfiles_root=dotfiles_root
        )

        if _is_same_symlink(src, dst) or _is_same_file_or_resolves_to_same(src, dst):
            LOG.debug("SKIP already stowed %s", src)
            continue

        if dst.exists() or dst.is_symlink():
            # Destination exists; only ok if it's already the same.
            if _is_same_file_or_resolves_to_same(dst, src):
                # Just ensure the home path is symlinked.
                try:
                    link_path(target=src, source=dst, dry_run=dry_run, force=force)
                except ConflictError as e:
                    LOG.error("CONFLICT %s (%s)", src, e)
                    rc = 2
                continue

            if not force:
                LOG.error("CONFLICT repo destination exists: %s", dst)
                rc = 2
                continue
            _backup_existing(dst, dry_run=dry_run)

        _mkdirp(dst.parent, dry_run=dry_run)

        if dry_run:
            LOG.info("MOVE %s -> %s", src, dst)
            LOG.info("LINK %s -> %s", src, dst)
            continue

        LOG.info("MOVE %s -> %s", src, dst)
        shutil.move(os.fspath(src), os.fspath(dst))
        LOG.info("LINK %s -> %s", src, dst)
        src.symlink_to(dst, target_is_directory=dst.is_dir())

    return rc


def run_unstow(
    *,
    paths: list[str],
    home: Path,
    dotfiles_root: Path,
    dry_run: bool,
    force: bool,
) -> int:
    rc = 0
    for raw in paths:
        p = Path(raw).expanduser()
        if not p.is_absolute():
            p = Path.cwd() / p
        p = Path(os.path.abspath(p))

        if not p.is_symlink():
            LOG.error("Not a symlink: %s", p)
            rc = 2
            continue

        try:
            target = p.resolve(strict=True)
        except FileNotFoundError:
            LOG.error("Broken symlink: %s", p)
            rc = 2
            continue

        try:
            target.relative_to(dotfiles_root)
        except ValueError:
            LOG.error(
                "Refusing to unstow; symlink target is not inside repo dotfiles: %s -> %s",
                p,
                target,
            )
            rc = 2
            continue

        # Remove symlink, move target back.
        if dry_run:
            LOG.info("UNLINK %s", p)
            LOG.info("MOVE %s -> %s", target, p)
            continue

        # If p exists as something else (shouldn't; it's a symlink), backup if forced.
        if p.exists() and not p.is_symlink():
            if not force:
                LOG.error("CONFLICT destination exists: %s", p)
                rc = 2
                continue
            _backup_existing(p, dry_run=False)

        LOG.info("UNLINK %s", p)
        p.unlink()
        _mkdirp(p.parent, dry_run=False)
        LOG.info("MOVE %s -> %s", target, p)
        shutil.move(os.fspath(target), os.fspath(p))

    return rc


def _self_test() -> None:
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        home = td / "home"
        repo = td / "repo"
        dotfiles = repo / "dotfiles"
        home.mkdir()
        dotfiles.mkdir(parents=True)

        # Restore: ~/.bashrc from dotfiles/bashrc
        (dotfiles / "bashrc").write_text("# bashrc\n", encoding="utf-8")
        # Restore: ~/.config/qtile directory from dotfiles/config__qtile
        (dotfiles / "config__qtile").mkdir()
        (dotfiles / "config__qtile" / "config.py").write_text(
            "# qtile\n", encoding="utf-8"
        )

        rc = run_restore(home=home, source_root=dotfiles, dry_run=False, force=False)
        assert rc == 0
        assert (home / ".bashrc").is_symlink()
        assert (home / ".config" / "qtile").is_symlink()
        assert (home / ".config" / "qtile" / "config.py").exists()

        # Stow: file
        cfg = home / ".config" / "app"
        cfg.mkdir(parents=True)
        f = cfg / "thing.txt"
        f.write_text("x\n", encoding="utf-8")
        rc2 = run_stow(
            paths=[os.fspath(f)],
            home=home,
            dotfiles_root=dotfiles,
            dry_run=False,
            force=False,
        )
        assert rc2 == 0
        assert f.is_symlink()
        assert (dotfiles / "config__app" / "thing.txt").exists()

        # Stow: directory
        d = home / ".config" / "dirapp"
        d.mkdir(parents=True)
        (d / "a").write_text("a\n", encoding="utf-8")
        rc3 = run_stow(
            paths=[os.fspath(d)],
            home=home,
            dotfiles_root=dotfiles,
            dry_run=False,
            force=False,
        )
        assert rc3 == 0
        assert d.is_symlink()
        assert (dotfiles / "config__dirapp").is_dir()


def main() -> int:
    repo_root = Path(__file__).resolve().parent
    default_source = repo_root / "dotfiles"

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--verbose", action="store_true", help="Enable debug logging")

    parser = argparse.ArgumentParser(
        description="Dotfiles manager (stdlib-only).", parents=[common]
    )
    parser.add_argument(
        "--self-test", action="store_true", help="Run built-in self-test"
    )

    subparsers = parser.add_subparsers(dest="cmd")

    # restore
    p_restore = subparsers.add_parser(
        "restore", help="Symlink repo dotfiles into $HOME", parents=[common]
    )
    p_restore.add_argument("--dry-run", action="store_true")
    p_restore.add_argument("--force", action="store_true")
    p_restore.add_argument(
        "--home",
        default=os.environ.get("HOME", str(Path.home())),
        help="Target home directory",
    )
    p_restore.add_argument(
        "--source", default=str(default_source), help="Source dotfiles directory"
    )

    # stow
    p_stow = subparsers.add_parser(
        "stow", help="Move a home path into repo and symlink it back", parents=[common]
    )
    p_stow.add_argument("--dry-run", action="store_true")
    p_stow.add_argument("--force", action="store_true")
    p_stow.add_argument(
        "--home",
        default=os.environ.get("HOME", str(Path.home())),
        help="Target home directory",
    )
    p_stow.add_argument(
        "--source", default=str(default_source), help="Repo dotfiles directory"
    )
    p_stow.add_argument("paths", nargs="+", help="Paths to stow")

    # unstow
    p_unstow = subparsers.add_parser(
        "unstow",
        help="Move a symlinked path out of repo back into place",
        parents=[common],
    )
    p_unstow.add_argument("--dry-run", action="store_true")
    p_unstow.add_argument("--force", action="store_true")
    p_unstow.add_argument(
        "--home",
        default=os.environ.get("HOME", str(Path.home())),
        help="Target home directory",
    )
    p_unstow.add_argument(
        "--source", default=str(default_source), help="Repo dotfiles directory"
    )
    p_unstow.add_argument("paths", nargs="+", help="Paths to unstow")

    args = parser.parse_args()
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO)

    if args.self_test:
        _self_test()
        LOG.info("Self-test OK")
        return 0

    cmd = args.cmd or "restore"

    if cmd == "restore":
        home = Path(args.home).expanduser().resolve()
        source_root = Path(args.source).expanduser().resolve()
        return run_restore(
            home=home, source_root=source_root, dry_run=args.dry_run, force=args.force
        )

    if cmd == "stow":
        home = Path(args.home).expanduser().resolve()
        source_root = Path(args.source).expanduser().resolve()
        return run_stow(
            paths=args.paths,
            home=home,
            dotfiles_root=source_root,
            dry_run=args.dry_run,
            force=args.force,
        )

    if cmd == "unstow":
        home = Path(args.home).expanduser().resolve()
        source_root = Path(args.source).expanduser().resolve()
        return run_unstow(
            paths=args.paths,
            home=home,
            dotfiles_root=source_root,
            dry_run=args.dry_run,
            force=args.force,
        )

    parser.error(f"Unknown command: {cmd}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
