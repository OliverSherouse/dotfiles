# Working Agreement

This file records the durable design choices for this dotfiles repo so future changes don't regress portability or safety.

## Repo Policy

- Public repo: do not commit secrets.
  - Secrets belong in `~/.profile_local` (untracked) or other local-only files.
- Avoid committing machine-specific symlinks (e.g. `~/...` absolute paths to local tool installs).
- Prefer merge/stow installs:
  - `~/.config` is a normal directory and contains lots of non-versioned application state.
  - The repo should only manage selected files/subtrees.
- `~/.local/bin` is not managed by this repo.
  - Tool-managed links like `djlint`/`proselint` should be created directly by the tool (e.g. uv) in `~/.local/bin`.
- Owned scripts are managed by this repo and installed to `~/.local/bin/scripts`.
  - Repo source: `dotfiles/local__bin__scripts/`.
  - `dotfiles/profile` must include `~/.local/bin/scripts` on `PATH`.

## Dotfile Manager Tooling

The dotfiles manager is a single self-contained Python tool (stdlib only).

- It supports merge/stow restore of repo contents into `$HOME`.
- It supports adoption ("stow") from a live `$HOME` path into the repo:
  - Move the file or directory into `dotfiles/...` (deterministic mapping).
  - Replace the original with a symlink back to the repo.
- It supports `unstow` to reverse a stow safely.

### Mapping Conventions

- `~/.config/<app>/...` maps to `dotfiles/config__<app>/...`.
- `~/.local/bin/scripts/...` maps to `dotfiles/local__bin__scripts/...`.
- Other dotdirs use clean paths where possible (preferred):
  - `~/.ssh/config` -> `dotfiles/ssh/config`.

### Safety Conventions

- Default mode should be safe:
  - never overwrite existing targets unless `--force`.
  - conflicts are reported and do not destroy data.
- `--force` must backup conflicting paths with timestamped backups.
- Provide `--dry-run` on commands that modify the filesystem.

### Tests

- No separate tests directory.
- Keep an inline `--self-test` mode using `tempfile`.

## Operational Notes

- `dotman restore` may symlink `config__*` as whole directories under `~/.config/<app>`.
  - This makes it easy to version an entire config subtree.
  - Use `.gitignore` inside those subtrees as needed to keep state out of git.
