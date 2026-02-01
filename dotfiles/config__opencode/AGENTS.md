# Working Agreement (opencode)

This folder is the versioned config for the opencode instance.

## Mapping

- `dotfiles/config__opencode/` -> `~/.config/opencode/`

## Repo Policy

- Public repo: never commit secrets.
- Any API keys/tokens must come from environment variables (preferred) or local-only files ignored by git.

## What We Track

- `opencode.json` is the canonical, portable configuration.
- `package.json` + `bun.lock` pin the opencode plugin dependency for reproducible installs.

## Secrets & Local Overrides

- Keep secrets out of `opencode.json`.
- Use `{env:NAME}` placeholders (e.g. `{env:CONTEXT7_API_KEY}`).
- If you need per-machine settings, put them in a `*.local.json` file (ignored by `.gitignore`).

## Portability Rules

- Avoid absolute paths and machine-specific locations.
- Prefer commands that resolve via `PATH` (e.g. wrappers like `ruff-lsp-venv`, `ty-lsp-venv`).

## Updating Plugin Dependencies

- Edit `package.json`, run `bun install`, and commit the updated `package.json` and `bun.lock`.
- Never commit `node_modules/`.
