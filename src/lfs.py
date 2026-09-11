#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tarfile
import urllib.request
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PKG_ROOT = ROOT / "src/packages"
WORK = ROOT / ".workspace"
SOURCES = WORK / "sources"
SYSROOT = WORK / "sysroot"
IMAGE = WORK / "qemu-hd/lfs.img"
TTY = sys.stdout.isatty() and not os.environ.get("NO_COLOR")
RESET = "\033[0m" if TTY else ""
CYAN = "\033[36m" if TTY else ""
GREEN = "\033[32m" if TTY else ""
YELLOW = "\033[33m" if TTY else ""
RED = "\033[31m" if TTY else ""
BLUE = "\033[34m" if TTY else ""
DIM = "\033[2m" if TTY else ""

def progress(label: str, current: int, total: int, width: int = 28, newline: bool = False) -> None:
    ratio = current / total if total else 0
    filled = min(width, int(width * ratio))
    print(f"\r{label:24} [{('#' * filled) + ('.' * (width - filled))}] {ratio * 100:6.2f}%", end="", flush=True)
    if newline or (total and current >= total): print()

def download_progress(name: str):
    def report(blocks: int, block_size: int, total: int) -> None:
        progress(f"download {name}", min(blocks * block_size, total), total)
    return report

def run(*cmd: str, cwd: Path | None = None, env: dict[str, str] | None = None, log_path: Path | None = None) -> None:
    print(f"{BLUE}→{RESET} " + " ".join(cmd))
    if log_path is None:
        subprocess.run(cmd, cwd=cwd, env=env, check=True)
        return
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8", errors="replace") as log:
        process = subprocess.Popen(cmd, cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
        assert process.stdout is not None
        for line in process.stdout:
            print(line, end="")
            log.write(line)
            log.flush()
        result = process.wait()
    if result:
        raise subprocess.CalledProcessError(result, cmd)

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
    if shell.is_symlink() and shell.readlink() != Path("bash"):
        shell.unlink()
    if not shell.exists() and not shell.is_symlink():
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
                urllib.request.urlretrieve(info["url"].format(version=info["version"]), temporary, reporthook=download_progress(info["name"]))
                temporary.replace(archive)
            finally:
                temporary.unlink(missing_ok=True)
    elif info.get("source") != "meta":
        raise SystemExit(f"invalid source type for {info['name']}")

def ensure_archive(info: dict) -> None:
    if info.get("source") != "archive":
        return
    archive = SOURCES / info["archive"]
    fetch_package(info)
    try:
        with tarfile.open(archive):
            pass
    except (OSError, tarfile.TarError) as error:
        print(f"{YELLOW}warning{RESET}: invalid archive for {info['name']}: {error}")
        archive.unlink(missing_ok=True)
        fetch_package(info)

def reset_archive_sources(info: dict) -> None:
    if info.get("source") != "archive":
        return
    archive = SOURCES / info["archive"]
    with tarfile.open(archive) as package:
        roots = {Path(member.name).parts[0] for member in package.getmembers() if member.name}
    for root in roots:
        extracted = WORK / "build" / root
        if extracted.is_symlink():
            extracted.unlink()
        elif extracted.exists():
            shutil.rmtree(extracted)

def build_package(directory: Path) -> None:
    info = metadata(directory); done = artifact(directory, info)
    ensure_archive(info)
    if info.get("source") != "archive":
        fetch_package(info)
    reset_archive_sources(info)
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
    print(f"{CYAN}build{RESET} {info['name']} {DIM}({info['version']}){RESET}")
    log_path = WORK / "logs" / f"{info['name']}.log"
    entry = ROOT / "src/package_entry.py"
    log_path.write_text(f"$ {sys.executable} -B {entry} {script}\n", encoding="utf-8")
    run(sys.executable, "-B", str(entry), str(script), cwd=directory, env=env, log_path=log_path)
    done.parent.mkdir(parents=True, exist_ok=True)
    done.write_text(json.dumps({"name": info["name"], "version": info["version"]}) + "\n")

def reset_build_state() -> None:
    print(f"{YELLOW}warning{RESET}: --rebuild removes built package state and compiled files.")
    print(f"{DIM}downloaded archives and Git checkouts in {SOURCES} are preserved.{RESET}")
    answer = input("Continue? [y/N] ").strip().lower()
    if answer not in ("y", "yes"):
        print("rebuild cancelled")
        return False
    shutil.rmtree(WORK / "build", ignore_errors=True)
    shutil.rmtree(WORK / "artifacts", ignore_errors=True)
    shutil.rmtree(SYSROOT, ignore_errors=True)
    setup_workspace()
    return True

def build(all_mode: bool, rebuild_mode: bool = False) -> None:
    if rebuild_mode and not reset_build_state():
        return
    setup_workspace(); directories = sorted(package_dirs(), key=lambda p: metadata(p).get("order", 9999))
    pending = [directory for directory in directories if package_state(directory, metadata(directory)) != "built"]
    total = len(pending)
    for index, directory in enumerate(pending, 1):
        info = metadata(directory)
        print(f"{YELLOW}package {index}/{total}{RESET} {info['name']}")
        build_package(directory)
        progress("build packages", index, total, newline=True)
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
    build_parser.add_argument("--all", action="store_true", dest="all_mode", help="process all selected packages")
    build_parser.add_argument("--rebuild", "-r", action="store_true", dest="rebuild_mode", help="clear built state but preserve downloaded sources")
    run_parser = commands.add_parser("run", help="boot MOS and lfs.img with QEMU")
    run_parser.add_argument("args", nargs=argparse.REMAINDER)
    commands.add_parser("status", help="show package and image state")
    ns = parser.parse_args(argv)
    if ns.command == "setup": setup()
    elif ns.command == "build": build(ns.all_mode, ns.rebuild_mode)
    elif ns.command == "run": qemu(ns.args)
    elif ns.command == "status": status()
    return 0
if __name__ == "__main__":
    try:
        raise SystemExit(main(sys.argv[1:]))
    except KeyboardInterrupt:
        print(f"\n{YELLOW}interrupted{RESET}", file=sys.stderr)
        raise SystemExit(130)
    except subprocess.CalledProcessError as error:
        command = " ".join(str(part) for part in error.cmd)
        print(f"{RED}error{RESET}: command failed ({error.returncode}): {command}", file=sys.stderr)
        raise SystemExit(error.returncode or 1)
    except Exception as error:
        print(f"{RED}error{RESET}: {error}", file=sys.stderr)
        raise SystemExit(1)
