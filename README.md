# MultiMC wrapper packages for Linux

The source of every Linux package of MultiMC: the `.deb`, the `.rpm` and the AUR's
`multimc-bin`. They all install the same small wrapper: `run.sh`, whose first start downloads the
current Stable build of MultiMC into the user's data folder, plus the desktop file, icon,
metainfo and man page.

## Layout

- `files/`: everything that gets installed
- `Makefile`: what goes where (`make install DESTDIR=...`), the one list all formats use
- `VERSION`: the wrapper's version
- `deb/`, `rpm/`, `arch/`: each format's template (`@VERSION@`, ...) and the script that builds it
  inside its distribution's container
- `build.py`: builds them all

Desktop file, icon and metainfo are named `org.multimc.MultiMC`, the Launcher's Wayland app id,
and the desktop file's `StartupWMClass` is its X11 window class: that's how docks and task
managers find the icon for MultiMC's windows.

## Building

You need Docker (or Podman: `--engine podman`) and network access for the distribution images.

```
./build.py
```

`out/` then holds:

- `multimc-wrapper-<version>.tar.gz`: the source, reproducibly packed from the tracked files; the
  rpm and Arch packages build from it, so it is uploaded with them
- `multimc_<version>-1.deb`
- `MultiMC5-<version>-1.*.noarch.rpm`
- `aur/PKGBUILD` and `aur/.SRCINFO`: for the AUR's `multimc-bin`, checked by building the package
  and running `namcap` on it

## Releasing

Change the files, raise `VERSION`, add an entry to the changelog in `rpm/MultiMC5.spec.in`,
and push. The build server (hopper's Laminar job `packages-production`) builds every commit of
`master` with `build.py`; for a version that isn't published yet it puts the tarball, `.deb`
and `.rpm` on `https://files.multimc.org/downloads/` and pushes `PKGBUILD` and `.SRCINFO` to
the AUR's `multimc-bin`. A commit that doesn't raise `VERSION` is built and checked, and
publishes nothing: a published version is never replaced.
