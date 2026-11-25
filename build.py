#!/usr/bin/env python3
"""Build every MeshMC wrapper package from this repository: the one source of truth.

    ./build.py [--out DIR] [--engine docker|podman] [--only deb,rpm,arch]

Into DIR (default out/):
  meshmc-wrapper-<version>.tar.gz   the source: the files `git ls-files` lists, reproducibly
                                     packed (fixed order, owner and times); the rpm and Arch
                                     packages build from it, so it is uploaded with them
  meshmc_<version>-1.deb            built with dpkg-deb in a Debian container
  MeshMC-<version>-1.*.noarch.rpm  built with rpmbuild in a Fedora container
  aur/PKGBUILD, aur/.SRCINFO         for the AUR's meshmc; the Arch container also builds
                                     the package from them and runs namcap, as a check
  meshmc-<version>-1-any.pkg.tar.zst   that check's package (not for publishing)

The version is VERSION's. What gets installed where is the Makefile's: the deb is its
`make install`, and the rpm spec and PKGBUILD call it. deb/, rpm/ and arch/ hold each format's
template (@VERSION@, ...) and the script that builds it inside its distribution's container.
"""

import argparse
import gzip
import hashlib
import io
import math
import os
import re
import shutil
import subprocess
import sys
import tarfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
# fully qualified: podman may refuse short names, or ask which registry
IMAGES = {"deb": "docker.io/library/debian:stable-slim", "rpm": "docker.io/library/fedora:latest",
          "arch": "docker.io/library/archlinux:latest"}


def run(*args, **kwargs):
    return subprocess.run(args, check=True, **kwargs)


def source_tarball(version, out):
    """The tracked files (and new ones not ignored), as meshmc-wrapper-<version>/..., with
    the newest commit's time on every entry, so the same tree gives the same bytes."""
    listed = subprocess.run(["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
                            cwd=HERE, check=True, capture_output=True).stdout.decode()
    files = sorted(f for f in listed.split("\0") if f and (HERE / f).is_file())
    mtime = int(subprocess.run(["git", "log", "-1", "--format=%ct"], cwd=HERE, check=True,
                               capture_output=True, text=True).stdout.strip() or 0)
    prefix = "meshmc-wrapper-%s/" % version
    raw = io.BytesIO()
    with tarfile.open(fileobj=raw, mode="w", format=tarfile.PAX_FORMAT) as tar:
        for name in files:
            path = HERE / name
            info = tarfile.TarInfo(prefix + name)
            info.size = path.stat().st_size
            info.mode = 0o755 if os.access(path, os.X_OK) else 0o644
            info.mtime = mtime
            info.uid = info.gid = 0
            info.uname = info.gname = "root"
            with open(path, "rb") as f:
                tar.addfile(info, f)
    target = out / ("meshmc-wrapper-%s.tar.gz" % version)
    with open(target, "wb") as f, gzip.GzipFile(filename="", mode="wb", fileobj=f, mtime=0) as gz:
        gz.write(raw.getvalue())
    return target


def render(template, values):
    text = template.read_text()
    for key, value in values.items():
        text = text.replace("@%s@" % key, value)
    left = re.findall(r"@[A-Z_]+@", text)
    if left:
        sys.exit("%s: placeholders left unfilled: %s" % (template, " ".join(sorted(set(left)))))
    return text


def in_container(engine, image, out, script):
    """Run one of the format scripts in its distribution's image, with out/ as /work."""
    run(engine, "run", "--rm", "-v", "%s:/work" % out, "-v", "%s:/build-script.sh:ro" % script,
        image, "bash", "/build-script.sh")


def build_deb(engine, version, out):
    root = out / "deb-root"
    shutil.rmtree(root, ignore_errors=True)
    run("make", "-s", "-C", str(HERE), "install", "DESTDIR=%s" % root)
    size_kb = math.ceil(sum(p.stat().st_size for p in root.rglob("*") if p.is_file() and not p.is_symlink()) / 1024)
    (root / "DEBIAN").mkdir()
    (root / "DEBIAN" / "control").write_text(render(HERE / "deb" / "control.in", {"VERSION": version, "INSTALLED_SIZE": str(size_kb)}))
    shutil.copy(HERE / "deb" / "postrm", root / "DEBIAN" / "postrm")
    (root / "DEBIAN" / "postrm").chmod(0o755)
    in_container(engine, IMAGES["deb"], out, HERE / "deb" / "build.sh")
    shutil.rmtree(root)


def build_rpm(engine, version, out):
    (out / "MeshMC.spec").write_text(render(HERE / "rpm" / "MeshMC.spec.in", {"VERSION": version}))
    in_container(engine, IMAGES["rpm"], out, HERE / "rpm" / "build.sh")
    (out / "MeshMC.spec").unlink()


def build_arch(engine, version, out, tarball):
    sha256 = hashlib.sha256(tarball.read_bytes()).hexdigest()
    (out / "aur").mkdir(exist_ok=True)
    (out / "aur" / "PKGBUILD").write_text(render(HERE / "arch" / "PKGBUILD.in", {"VERSION": version, "SOURCE_SHA256": sha256}))
    in_container(engine, IMAGES["arch"], out, HERE / "arch" / "build.sh")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--out", type=Path, default=HERE / "out")
    parser.add_argument("--engine", default=os.environ.get("CONTAINER_ENGINE", "docker"))
    parser.add_argument("--only", default="deb,rpm,arch", help="comma-separated: deb, rpm, arch")
    args = parser.parse_args()

    version = (HERE / "VERSION").read_text().strip()
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    (out / "VERSION").write_text(version + "\n")
    tarball = source_tarball(version, out)
    print("source: %s" % tarball.name)

    formats = args.only.split(",")
    if "deb" in formats:
        build_deb(args.engine, version, out)
    if "rpm" in formats:
        build_rpm(args.engine, version, out)
    if "arch" in formats:
        build_arch(args.engine, version, out, tarball)

    # the containers ran as root: with docker, give the results back to whoever ran this
    # (rootless podman's root is that user already; a chown there would hand them to a
    # subordinate uid)
    if Path(args.engine).name == "docker":
        run(args.engine, "run", "--rm", "-v", "%s:/work" % out, IMAGES["deb"], "chown", "-R", "%d:%d" % (os.getuid(), os.getgid()), "/work")
    print("\nin %s:" % out)
    for path in sorted(out.rglob("*")):
        if path.is_file():
            print("  %s" % path.relative_to(out))


if __name__ == "__main__":
    main()
