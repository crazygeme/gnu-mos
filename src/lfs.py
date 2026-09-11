#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PKG_ROOT = ROOT / "src/packages"
WORK = ROOT / ".workspace"
SOURCES = WORK / "sources"
SYSROOT = WORK / "sysroot"
IMAGE = WORK / "qemu-hd/lfs.img"

def run(*cmd: str, cwd: Path | None = None, env: dict[str, str] | None = None) -> None:
    print("+", " ".join(cmd)); subprocess.run(cmd, cwd=cwd, env=env, check=True)

def sudo_run(*cmd: str) -> None:
    run(*(cmd if os.geteuid() == 0 else ("sudo", *cmd)))

def setup_workspace() -> None:
    for path in (WORK, SOURCES, WORK / "build", WORK / "logs", SYSROOT, IMAGE.parent): path.mkdir(parents=True, exist_ok=True)
    for path in ("boot", "dev", "etc", "home", "proc", "root", "run", "sys", "tmp", "usr/bin", "usr/sbin", "usr/lib", "var/log"):
        (SYSROOT / path).mkdir(parents=True, exist_ok=True)
    for name, target in (("bin", "usr/bin"), ("sbin", "usr/sbin"), ("lib", "usr/lib")):
        link = SYSROOT / name
        if not link.exists(): link.symlink_to(target)
    init = SYSROOT / "sbin/init"
    if not init.exists():
        init.write_text("#!/bin/sh\nmount -a || true\nexec /bin/sh\n")
        init.chmod(0o755)
    shell = SYSROOT / "usr/bin/sh"
    if not shell.exists():
        shell.symlink_to("bash")

def package_dirs() -> list[Path]:
    return [path.parent for path in PKG_ROOT.glob("*/package.json")]


def metadata(directory: Path) -> dict: return json.loads((directory / "package.json").read_text())
def artifact(directory: Path, info: dict) -> Path: return WORK / info.get("artifact", f"artifacts/{info['name']}.done")

def package_state(directory: Path, info: dict) -> str:
    if artifact(directory, info).exists(): return "built"
    if info.get("source") == "git" and (SOURCES / info["name"]).exists(): return "fetched"
    if info.get("source") == "archive" and (SOURCES / info["archive"]).exists(): return "fetched"
    if info.get("source") == "meta": return "empty"
    return "empty"

def status() -> None:
    rows = []
    for directory in sorted(package_dirs(), key=lambda p: metadata(p).get("order", 9999)):
        info = metadata(directory); rows.append({"name": info["name"], "version": info["version"], "status": package_state(directory, info)})
    done = sum(row["status"] == "built" for row in rows)
    total = len(rows)
    width = 28
    filled = int(width * done / total) if total else 0
    color = sys.stdout.isatty() and not os.environ.get("NO_COLOR")
    reset = "\033[0m" if color else ""
    cyan, green, yellow, dim = (("\033[36m", "\033[32m", "\033[33m", "\033[2m") if color else ("", "", "", ""))
    print(f"{cyan}LFS / MOS{reset} {dim}build status{reset}")
    print(f"{dim}{'─' * 72}{reset}")
    print(f"{dim}workspace{reset}  {WORK}")
    print(f"{dim}image{reset}      {(green + 'ready' + reset) if IMAGE.exists() else (yellow + 'pending' + reset):16} {IMAGE}")
    print(f"{dim}packages{reset}   {cyan}[{('#' * filled) + ('.' * (width - filled))}]{reset} {done}/{total}")
    print(f"{dim}{'─' * 72}{reset}")
    print(f"{dim}{'PACKAGE':20} {'VERSION':18} STATUS{reset}")
    print(f"{dim}{'─' * 72}{reset}")
    for row in rows:
        state = green + "built" + reset if row["status"] == "built" else (cyan + "fetched" + reset if row["status"] == "fetched" else yellow + "empty" + reset)
        print(f"{row['name'][:20]:20} {row['version'][:18]:18} {state}")

def fetch_package(info: dict) -> None:
    if info.get("source") == "git":
        checkout = SOURCES / info["name"]
        if not checkout.exists(): run("git", "clone", "--depth", "1", "--branch", info["version"], info["git"], str(checkout))
    elif info.get("source") == "archive":
        if not info.get("url") or not info.get("archive"): raise SystemExit(f"invalid source definition for {info['name']}")
        archive = SOURCES / info["archive"]
        if not archive.exists():
            temporary = archive.with_suffix(archive.suffix + ".part")
            print(f"download {info['name']} {info['version']}")
            try:
                urllib.request.urlretrieve(info["url"].format(version=info["version"]), temporary)
                temporary.replace(archive)
            finally:
                temporary.unlink(missing_ok=True)
    elif info.get("source") != "meta":
        raise SystemExit(f"invalid source type for {info['name']}")

def build_package(directory: Path, continue_mode: bool) -> None:
    info = metadata(directory); done = artifact(directory, info)
    if continue_mode and done.exists(): print(f"skip {info['name']} (artifact exists)"); return
    fetch_package(info)
    script = directory / "build.py"
    if not script.exists(): raise SystemExit(f"package {info['name']} has no build.py")
    if info.get("source") == "archive" and not (SOURCES / info["archive"]).exists():
        raise SystemExit(f"source missing for {info['name']}; build cannot continue for {info['name']}")
    if info.get("source") == "git" and not (SOURCES / info["name"]).exists():
        raise SystemExit(f"source missing for {info['name']}; build cannot continue for {info['name']}")
    env = os.environ.copy()
    env.update({
        "LFS_WORKSPACE": str(WORK),
        "LFS_SYSROOT": str(SYSROOT),
        "LFS_SOURCES": str(SOURCES),
        "LFS_TARGET": "i686-lfs-linux-gnu",
        "PATH": f"{WORK / 'tools/bin'}:{SYSROOT / 'usr/bin'}:{env['PATH']}",
        "PYTHONDONTWRITEBYTECODE": "1",
    })
    run(sys.executable, "-B", str(script), cwd=directory, env=env)
    done.parent.mkdir(parents=True, exist_ok=True)
    done.write_text(json.dumps({"name": info["name"], "version": info["version"]}) + "\n")

def build(continue_mode: bool, all_mode: bool) -> None:
    setup_workspace(); directories = sorted(package_dirs(), key=lambda p: metadata(p).get("order", 9999))
    for directory in directories:
        info = metadata(directory)
        if continue_mode and package_state(directory, info) == "built":
            continue
        build_package(directory, continue_mode)
        if not all_mode:
            return

def setup() -> None:
    setup_workspace()
    create_image()

def create_image() -> None:
    if IMAGE.exists():
        image_size = None
    else:
        image_size = os.environ.get("LFS_IMAGE_SIZE", "8G")
        run("qemu-img", "create", "-f", "raw", str(IMAGE), image_size)
        run("bash", "-c", f"printf 'label: dos\\n, start=2048, type=83, bootable\\n' | sfdisk {IMAGE}")
    loop = subprocess.check_output(["sudo", "losetup", "--find", "--show", "--partscan", str(IMAGE)], text=True).strip()
    mountpoint = WORK / "mount"
    mountpoint.mkdir(exist_ok=True)
    mounted = False
    try:
        if image_size is not None:
            sudo_run("mkfs.ext4", "-F", loop + "p1")
        sudo_run("mount", loop + "p1", str(mountpoint))
        mounted = True
        sudo_run("cp", "-a", str(SYSROOT) + "/.", str(mountpoint) + "/")
        sudo_run("mkdir", "-p", str(mountpoint / "boot/grub"))
        grub_cfg = "set timeout=3\nset default=0\nmenuentry 'LFS on MOS' {\n    multiboot /boot/kernel\n    boot\n}\n"
        (WORK / "grub.cfg").write_text(grub_cfg)
        sudo_run("cp", str(WORK / "grub.cfg"), str(mountpoint / "boot/grub/grub.cfg"))
        sudo_run("grub-install", "--target=i386-pc", "--boot-directory=" + str(mountpoint / "boot"), "--modules=normal part_msdos ext2 multiboot", loop)
        sudo_run("sync")
    finally:
        if mounted: sudo_run("umount", str(mountpoint))
        sudo_run("losetup", "-d", loop)

def qemu(extra: list[str]) -> None:
    if not IMAGE.exists(): raise SystemExit("run requires ./lfs setup")
    run("qemu-system-i386", "-m", os.environ.get("LFS_RAM", "2048"), "-drive", f"file={IMAGE},format=raw,if=ide,index=0,media=disk", "-serial", "stdio", *extra)

def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="lfs")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("setup", help="copy built artifacts into lfs.img")
    build_parser = commands.add_parser("build", help="fetch and build packages in order")
    build_parser.add_argument("--continue", action="store_true", dest="continue_mode", help="start at the first package not built")
    build_parser.add_argument("--all", action="store_true", dest="all_mode", help="process all selected packages")
    run_parser = commands.add_parser("run", help="boot MOS and lfs.img with QEMU")
    run_parser.add_argument("args", nargs=argparse.REMAINDER)
    commands.add_parser("status", help="show package and image state")
    ns = parser.parse_args(argv)
    if ns.command == "setup": setup()
    elif ns.command == "build": build(ns.continue_mode, ns.all_mode)
    elif ns.command == "run": qemu(ns.args)
    elif ns.command == "status": status()
    return 0
if __name__ == "__main__": raise SystemExit(main(sys.argv[1:]))
