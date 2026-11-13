# Versioning, downloads and development releases

**🇺🇸 English (default) · [🇧🇷 Português (Brasil)](pt-BR/LANCAMENTO.md)**

DarfinOS is not a standalone Linux distribution or ISO. GitHub's Releases page used to be empty because the manual candidate workflow only uploaded temporary **Actions artifacts**, not repository releases.

## Download options

1. **[Current main source ZIP](https://github.com/AlanDarfin/DarfinOS/archive/refs/heads/main.zip):** always available, automatically reflects the current code. This is **not** a versioned stable release.
2. **[GitHub development prereleases](https://github.com/AlanDarfin/DarfinOS/releases):** tagged `v0.1.0-rcN` packages with SHA-256 checksum files, produced after both the offline test matrix and Arch smoke pass on the same commit.
3. **[Bilingual downloads page](https://darfinos.vercel.app/downloads/):** surfaces the main ZIP immediately and shows the latest suitable prerelease asset if GitHub's public releases API has one. When the release API is empty or unavailable, the page says so rather than pretending a package exists.

## Automatic prerelease pipeline

The `.github/workflows/publish-development.yml` workflow is triggered when the Arch smoke workflow completes on a push to `main`. It checks that:

- The triggering Arch run succeeded on `main`.
- The independent Python/Bash test workflow also succeeded for the **exact same commit SHA** (with a bounded retry for races).
- The Bash/Python files still pass local syntax and Doctor checks.
- `scripts/package_release.sh` generated a versioned `.tar.gz` using `git archive`, with a matching `.sha256` that verifies successfully.

Only then does it create a GitHub **prerelease**, attaching the package and checksum, with a clear development warning. It never marks a candidate as stable, promotes it to Latest stable, or claims to be an ISO.

The versioned tag uses the workflow's `0.1.0-rcN` sequence. If publishing is blocked by GitHub repository permissions or network/API errors, inspect the workflow logs; the website source ZIP remains available.

## Manual candidate (no publication)

The existing `release-candidate.yml` workflow supports manual packaging for review without creating any GitHub release. Its artifacts expire; they are not permanent download links.

## Stability policy

A stable release requires the [manual VM checklist](VALIDACAO_VM.md), including graphical login/reboot, recovery and verification of high-risk modules. A green test matrix or container smoke check by itself is insufficient.

[Downloads](https://darfinos.vercel.app/downloads/) · [Security](SEGURANCA.md) · [Documentation index](README.md)
