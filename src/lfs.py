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
from contextlib import contextmanager
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PKG_ROOT = ROOT / "src/packages"
WORK = ROOT / ".workspace"
SOURCES = WORK / "sources"
SYSROOT = WORK / "sysroot"
IMAGE = WORK / "qemu-hd/lfs.img"
BASE_WORK = WORK
NO_GUI = False
TTY = sys.stdout.isatty() and not os.environ.get("NO_COLOR")
RESET = "\033[0m" if TTY else ""
CYAN = "\033[36m" if TTY else ""
GREEN = "\033[32m" if TTY else ""
YELLOW = "\033[33m" if TTY else ""
RED = "\033[31m" if TTY else ""
BLUE = "\033[34m" if TTY else ""
DIM = "\033[2m" if TTY else ""


def progress(
    label: str, current: int, total: int, width: int = 28, newline: bool = False
) -> None:
    ratio = current / total if total else 0
    filled = min(width, int(width * ratio))
    print(
        f"\r{label:24} [{('#' * filled) + ('.' * (width - filled))}] {ratio * 100:6.2f}%",
        end="",
        flush=True,
    )
    if newline or (total and current >= total):
        print()


def download_progress(name: str):
    def report(blocks: int, block_size: int, total: int) -> None:
        progress(f"download {name}", min(blocks * block_size, total), total)

    return report


def run(
    *cmd: str,
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
    log_path: Path | None = None,
) -> None:
    print(f"{BLUE}→{RESET} " + " ".join(cmd))
    if log_path is None:
        subprocess.run(cmd, cwd=cwd, env=env, check=True)
        return
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8", errors="replace") as log:
        process = subprocess.Popen(
            cmd,
            cwd=cwd,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
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


def select_workspace(no_gui: bool) -> None:
    global WORK, SOURCES, SYSROOT, IMAGE, NO_GUI
    NO_GUI = no_gui
    WORK = BASE_WORK
    SOURCES = BASE_WORK / "sources"
    SYSROOT = WORK / "sysroot"
    IMAGE = WORK / "qemu-hd/lfs.img"


def selected_packages(no_gui: bool) -> list[Path]:
    directories = sorted(
        package_dirs(), key=lambda p: (metadata(p).get("order", 9999), p.name)
    )
    if no_gui:
        directories = [
            p for p in directories if "gui" not in metadata(p).get("profiles", [])
        ]
    return directories


def setup_workspace() -> None:
    for path in (WORK, SOURCES, WORK / "build", WORK / "logs", SYSROOT, IMAGE.parent):
        path.mkdir(parents=True, exist_ok=True)
    for path in (
        "boot",
        "dev",
        "dev/pts",
        "dev/shm",
        "etc",
        "home",
        "proc",
        "root",
        "run",
        "sys",
        "tmp",
        "usr/bin",
        "usr/sbin",
        "usr/lib",
        "var/log",
        "var/run",
    ):
        (SYSROOT / path).mkdir(parents=True, exist_ok=True)
    for name, target in (("bin", "usr/bin"), ("sbin", "usr/sbin"), ("lib", "usr/lib")):
        link = SYSROOT / name
        if not link.exists():
            link.symlink_to(target)
    shell = SYSROOT / "usr/bin/sh"
    if shell.is_symlink() and shell.readlink() != Path("bash"):
        shell.unlink()
    if not shell.exists() and not shell.is_symlink():
        shell.symlink_to("bash")


def package_dirs() -> list[Path]:
    return [path.parent for path in PKG_ROOT.glob("*/package.json")]


def metadata(directory: Path) -> dict:
    return json.loads((directory / "package.json").read_text())


def artifact(directory: Path, info: dict) -> Path:
    return WORK / info.get("artifact", f"artifacts/{info['name']}.done")


def build_version(directory: Path) -> int:
    version = int((directory / "version").read_text().strip())
    if version < 1:
        raise ValueError(f"invalid build version for {directory.name}: {version}")
    return version


def artifact_current(directory: Path, info: dict) -> bool:
    version = build_version(directory)
    done = artifact(directory, info)
    if not done.exists():
        return False
    content = done.read_text()
    record = json.loads(content) if content.strip() else {}
    if "version" not in record:
        record.update(name=info["name"], version=version)
        done.write_text(json.dumps(record) + "\n")
    recorded_version = record["version"]
    if type(recorded_version) is not int or recorded_version < 1:
        raise ValueError(f"invalid build version in {done}: {recorded_version!r}")
    return recorded_version >= version


def package_state(directory: Path, info: dict) -> str:
    if artifact_current(directory, info):
        return "built"
    if info.get("source") == "git" and (SOURCES / info["name"]).exists():
        return "fetched"
    if info.get("source") == "archive" and (SOURCES / info["archive"]).exists():
        return "fetched"
    if info.get("source") == "meta":
        return "empty"
    return "empty"


def status(no_gui: bool = False) -> None:
    rows = []
    for directory in selected_packages(no_gui):
        info = metadata(directory)
        rows.append(
            {
                "name": info["name"],
                "version": info["version"],
                "status": package_state(directory, info),
            }
        )
    done = sum(row["status"] == "built" for row in rows)
    total = len(rows)
    width = 28
    filled = int(width * done / total) if total else 0
    color = sys.stdout.isatty() and not os.environ.get("NO_COLOR")
    reset = "\033[0m" if color else ""
    cyan, green, yellow, dim = (
        ("\033[36m", "\033[32m", "\033[33m", "\033[2m") if color else ("", "", "", "")
    )
    print(f"{cyan}LFS / MOS{reset} {dim}build status{reset}")
    print(f"{dim}{'─' * 72}{reset}")
    print(f"{dim}workspace{reset}  {WORK}")
    print(
        f"{dim}image{reset}      {(green + 'ready' + reset) if IMAGE.exists() else (yellow + 'pending' + reset):16} {IMAGE}"
    )
    print(
        f"{dim}packages{reset}   {cyan}[{('#' * filled) + ('.' * (width - filled))}]{reset} {done}/{total}"
    )
    print(f"{dim}{'─' * 72}{reset}")
    print(f"{dim}{'PACKAGE':20} {'VERSION':18} STATUS{reset}")
    print(f"{dim}{'─' * 72}{reset}")
    for row in rows:
        state = (
            green + "built" + reset
            if row["status"] == "built"
            else (
                cyan + "fetched" + reset
                if row["status"] == "fetched"
                else yellow + "empty" + reset
            )
        )
        print(f"{row['name'][:20]:20} {row['version'][:18]:18} {state}")


def fetch_package(info: dict) -> None:
    if info.get("source") == "git":
        checkout = SOURCES / info["name"]
        if not checkout.exists():
            run(
                "git",
                "clone",
                "--depth",
                "1",
                "--branch",
                info["version"],
                info["git"],
                str(checkout),
            )
    elif info.get("source") == "archive":
        if not info.get("url") or not info.get("archive"):
            raise SystemExit(f"invalid source definition for {info['name']}")
        archive = SOURCES / info["archive"]
        if not archive.exists():
            temporary = archive.with_suffix(archive.suffix + ".part")
            print(f"download {info['name']} {info['version']}")
            try:
                urllib.request.urlretrieve(
                    info["url"].format(version=info["version"]),
                    temporary,
                    reporthook=download_progress(info["name"]),
                )
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
        roots = {
            Path(member.name).parts[0] for member in package.getmembers() if member.name
        }
    for root in roots:
        extracted = WORK / "build" / root
        if extracted.is_symlink():
            extracted.unlink()
        elif extracted.exists():
            shutil.rmtree(extracted)


def ensure_host_packages(info: dict) -> None:
    packages = info.get("host-packages", {}).get("apt", [])
    if not packages:
        return
    apt = shutil.which("apt-get", path="/usr/bin:/bin")
    dpkg = shutil.which("dpkg-query", path="/usr/bin:/bin")
    if not apt or not dpkg:
        raise SystemExit(
            f"host dependencies for {info['name']} require an APT-based host; "
            f"install equivalent native development packages: {' '.join(packages)}"
        )
    missing = []
    for package in packages:
        result = subprocess.run(
            [dpkg, "-W", "-f=${Status}", package],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode or result.stdout.strip() != "install ok installed":
            missing.append(package)
    if missing:
        print(f"{CYAN}host dependencies{RESET} {info['name']}: {' '.join(missing)}")
        sudo_run(apt, "install", "--yes", *missing)


def build_package(directory: Path) -> None:
    info = metadata(directory)
    ensure_host_packages(info)
    done = artifact(directory, info)
    # Package builds always start from an empty build tree. Downloaded source
    # archives, installed tools, the sysroot, and package artifacts are kept.
    shutil.rmtree(WORK / "build", ignore_errors=True)
    (WORK / "build").mkdir(parents=True, exist_ok=True)
    ensure_archive(info)
    if info.get("source") != "archive":
        fetch_package(info)
    reset_archive_sources(info)
    script = directory / "build.py"
    if not script.exists():
        raise SystemExit(f"package {info['name']} has no build.py")
    if info.get("source") == "archive" and not (SOURCES / info["archive"]).exists():
        raise SystemExit(
            f"source missing for {info['name']}; build cannot continue for {info['name']}"
        )
    if info.get("source") == "git" and not (SOURCES / info["name"]).exists():
        raise SystemExit(
            f"source missing for {info['name']}; build cannot continue for {info['name']}"
        )
    env = os.environ.copy()
    env.update(
        {
            "LFS_WORKSPACE": str(WORK),
            "LFS_SYSROOT": str(SYSROOT),
            "LFS_SOURCES": str(SOURCES),
            "LFS_TARGET": "i686-lfs-linux-gnu",
            "LFS_PACKAGE_DIR": str(directory.resolve()),
            # Host utilities must precede target binaries.  Target programs in the
            # sysroot are not runnable on the build host and must never satisfy
            # commands such as sh, install, or sed during package builds.
            "PATH": f"{WORK / 'tools/bin'}:/usr/bin:/bin:{SYSROOT / 'usr/bin'}:{env['PATH']}",
            "PYTHONDONTWRITEBYTECODE": "1",
        }
    )
    print(f"{CYAN}build{RESET} {info['name']} {DIM}({info['version']}){RESET}")
    log_path = WORK / "logs" / f"{info['name']}.log"
    entry = ROOT / "src/package_entry.py"
    log_path.write_text(f"$ {sys.executable} -B {entry} {script}\n", encoding="utf-8")
    run(
        sys.executable,
        "-B",
        str(entry),
        str(script),
        cwd=directory,
        env=env,
        log_path=log_path,
    )
    done.parent.mkdir(parents=True, exist_ok=True)
    done.write_text(
        json.dumps(
            {
                "name": info["name"],
                "version": build_version(directory),
                "source_version": info["version"],
            }
        )
        + "\n"
    )


def run_postscripts() -> None:
    scripts = []
    for directory in sorted(
        package_dirs(), key=lambda path: (metadata(path).get("order", 9999), path.name)
    ):
        info = metadata(directory)
        script = directory / "postscript.py"
        if package_state(directory, info) == "built" and script.is_file():
            scripts.append(script)
    env = os.environ.copy()
    env.update(
        {
            "LFS_WORKSPACE": str(WORK),
            "LFS_SYSROOT": str(SYSROOT),
            "LFS_SOURCES": str(SOURCES),
            "LFS_TARGET": "i686-lfs-linux-gnu",
            "LFS_NO_GUI": "1" if NO_GUI else "0",
        }
    )
    entry = ROOT / "src/package_entry.py"
    for script in scripts:
        print(f"{CYAN}postscript{RESET} {script.name}")
        run(sys.executable, "-B", str(entry), str(script), env=env)


def reset_build_state() -> None:
    for done in (WORK / "artifacts").rglob("*.done"):
        if done.is_file() or done.is_symlink():
            done.unlink()


def build(all_mode: bool, rebuild_mode: bool = False, no_gui: bool = False) -> None:
    if rebuild_mode:
        reset_build_state()
    setup_workspace()
    directories = selected_packages(no_gui)
    pending = [
        directory
        for directory in directories
        if package_state(directory, metadata(directory)) != "built"
    ]
    total = len(pending)
    for index, directory in enumerate(pending, 1):
        info = metadata(directory)
        print(f"{YELLOW}package {index}/{total}{RESET} {info['name']}")
        build_package(directory)
        progress("build packages", index, total, newline=True)
        if not (all_mode or no_gui):
            sync_sysroot()
            return
    sync_sysroot()


def sync_sysroot() -> None:
    source_root = ROOT / "src/sysroot"
    SYSROOT.mkdir(parents=True, exist_ok=True)
    run("cp", "-af", str(source_root) + "/.", str(SYSROOT))


def setup(no_gui: bool = False) -> None:
    setup_workspace()
    sync_sysroot()
    run_postscripts()
    create_image()


def create_image() -> None:
    image_root = SYSROOT
    grub_install = SYSROOT / "usr/sbin/grub-install"
    grub_modules = SYSROOT / "usr/lib/grub/i386-pc"
    grub_env = os.environ.copy()
    grub_env["GRUB_LIBDIR"] = str(SYSROOT / "usr/lib/grub")
    grub_env["PATH"] = (
        str(SYSROOT / "usr/sbin") + ":/usr/sbin:/usr/bin:/bin:" + grub_env["PATH"]
    )
    new_image = not IMAGE.exists()
    if new_image:
        image_size = os.environ.get("LFS_IMAGE_SIZE", "8G")
        run("qemu-img", "create", "-f", "raw", str(IMAGE), image_size)
    partition_info = subprocess.run(
        ["sfdisk", "--json", str(IMAGE)], capture_output=True, text=True
    )
    with IMAGE.open("rb") as image_file:
        empty_mbr = image_file.read(512) == b"\0" * 512
    if partition_info.returncode and (new_image or empty_mbr):
        # Use the positional sfdisk partition format accepted by util-linux
        # versions used by the build host.
        run(
            "bash",
            "-c",
            f"printf 'label: dos\\nunit: sectors\\n\\n2048,,83,*\\n' | sfdisk {IMAGE}",
        )
        partition_info = subprocess.run(
            ["sfdisk", "--json", str(IMAGE)], capture_output=True, text=True
        )
    if partition_info.returncode:
        raise SystemExit(f"image has no partition table: {IMAGE}")
    partition_table = json.loads(partition_info.stdout)["partitiontable"]
    partitions = partition_table.get("partitions", [])
    if len(partitions) != 1:
        raise SystemExit(f"setup requires one image partition: {IMAGE}")
    sector_size = partition_table.get("sectorsize", 512)
    offset = partitions[0]["start"] * sector_size
    size = partitions[0]["size"] * sector_size
    loop = subprocess.check_output(
        ["sudo", "losetup", "--find", "--show", str(IMAGE)], text=True
    ).strip()
    try:
        partition = subprocess.check_output(
            [
                "sudo",
                "losetup",
                "--find",
                "--show",
                "--offset",
                str(offset),
                "--sizelimit",
                str(size),
                str(IMAGE),
            ],
            text=True,
        ).strip()
    except Exception:
        sudo_run("losetup", "-d", loop)
        raise
    mountpoint = WORK / "mount"
    mountpoint.mkdir(exist_ok=True)
    mounted = False
    try:
        if new_image or empty_mbr or NO_GUI:
            sudo_run("mkfs.ext3", "-F", partition)
        sudo_run("mount", partition, str(mountpoint))
        mounted = True
        sudo_run("cp", "-a", str(image_root) + "/.", str(mountpoint) + "/")
        command = [
            str(grub_install),
            "--target=i386-pc",
            "--directory=" + str(grub_modules),
            "--boot-directory=" + str(mountpoint / "boot"),
            "--modules=normal part_msdos ext2 multiboot",
            loop,
        ]
        if os.geteuid() != 0:
            command = ["sudo", "-E", *command]
        run(*command, env=grub_env)
        sudo_run("sync")
    finally:
        if mounted:
            sudo_run("umount", str(mountpoint))
        subprocess.run(["sudo", "losetup", "-d", partition], check=False)
        subprocess.run(["sudo", "losetup", "-d", loop], check=False)


def qemu(extra: list[str]) -> None:
    if not IMAGE.exists():
        raise SystemExit("run requires ./lfs setup")
    serial = "file:" + str(WORK / "krn.log")
    qemu_extra = list(extra)
    executable = str(WORK / "tools/qemu/bin/qemu-system-x86_64")
    if not Path(executable).is_file():
        raise SystemExit(
            "desktop QEMU is missing; run ./lfs build --all to build qemu-host"
        )
    command = [
        executable,
        "-enable-kvm",
        "-cpu",
        "host",
        "-m",
        os.environ.get("LFS_RAM", "4096"),
        "-smp",
        "2",
        # The i686 kernel maps PCI MMIO only below 4 GiB.
        "-fw_cfg",
        "name=opt/org.seabios/pci64,string=0",
        "-drive",
        f"file={IMAGE},format=raw,if=ide,index=0,media=disk",
        "-netdev",
        "tap,id=net0,ifname=lfs-tap0,script=no,downscript=no",
        "-device",
        "e1000,netdev=net0,mac=52:54:00:12:34:56",
    ]
    if "-audiodev" not in qemu_extra and "-audio" not in qemu_extra:
        audio_backend = os.environ.get("MOS_AUDIO_BACKEND", "sdl")
        command.extend(
            [
                "-audiodev",
                f"{audio_backend},id=audio0",
                "-device",
                "AC97,audiodev=audio0",
            ]
        )
    if not NO_GUI:
        command.extend(["-vga", "none", "-device", "virtio-vga-gl,xres=2560,yres=1440"])
        if "-display" not in qemu_extra:
            command.extend(["-display", "sdl,gl=on,full-screen=on"])
    command.extend(["-serial", serial])
    command.extend(qemu_extra)
    with qemu_network():
        run(*command)


@contextmanager
def qemu_network():
    interface = "lfs-tap0"
    gateway = "10.0.6.1"
    subnet = "10.0.6.0/24"
    pid_file = WORK / "lfs-dnsmasq.pid"
    tap_created = False
    nat_added = False
    forward_out_added = False
    forward_in_added = False
    dnsmasq_started = False
    forwarding = None
    try:
        sudo_run(
            "ip",
            "tuntap",
            "add",
            "dev",
            interface,
            "mode",
            "tap",
            "user",
            str(os.getuid()),
        )
        tap_created = True
        sudo_run("ip", "addr", "add", gateway + "/24", "dev", interface)
        sudo_run("ip", "link", "set", interface, "up")
        forwarding = subprocess.check_output(
            ["sysctl", "-n", "net.ipv4.ip_forward"], text=True
        ).strip()
        if forwarding != "1":
            sudo_run("sysctl", "-qw", "net.ipv4.ip_forward=1")
        sudo_run(
            "iptables",
            "-t",
            "nat",
            "-A",
            "POSTROUTING",
            "-s",
            subnet,
            "-j",
            "MASQUERADE",
        )
        nat_added = True
        sudo_run("iptables", "-A", "FORWARD", "-i", interface, "-j", "ACCEPT")
        forward_out_added = True
        sudo_run(
            "iptables",
            "-A",
            "FORWARD",
            "-o",
            interface,
            "-m",
            "conntrack",
            "--ctstate",
            "ESTABLISHED,RELATED",
            "-j",
            "ACCEPT",
        )
        forward_in_added = True
        sudo_run(
            "dnsmasq",
            "--conf-file=/dev/null",
            "--interface=" + interface,
            "--bind-interfaces",
            "--except-interface=lo",
            "--listen-address=" + gateway,
            "--dhcp-range=10.0.6.2,10.0.6.20,1h",
            "--dhcp-option=option:router," + gateway,
            "--dhcp-option=option:dns-server," + gateway,
            "--pid-file=" + str(pid_file),
            "--log-facility=/dev/null",
        )
        dnsmasq_started = True
        yield
    finally:
        if dnsmasq_started:
            pid = pid_file.read_text().strip() if pid_file.exists() else ""
            if pid.isdecimal():
                cleanup_network("kill", pid)
            pid_file.unlink(missing_ok=True)
        if forward_in_added:
            cleanup_network(
                "iptables",
                "-D",
                "FORWARD",
                "-o",
                interface,
                "-m",
                "conntrack",
                "--ctstate",
                "ESTABLISHED,RELATED",
                "-j",
                "ACCEPT",
            )
        if forward_out_added:
            cleanup_network(
                "iptables", "-D", "FORWARD", "-i", interface, "-j", "ACCEPT"
            )
        if nat_added:
            cleanup_network(
                "iptables",
                "-t",
                "nat",
                "-D",
                "POSTROUTING",
                "-s",
                subnet,
                "-j",
                "MASQUERADE",
            )
        if forwarding not in (None, "1"):
            cleanup_network("sysctl", "-qw", "net.ipv4.ip_forward=" + forwarding)
        if tap_created:
            cleanup_network("ip", "tuntap", "del", "dev", interface, "mode", "tap")


def cleanup_network(*command: str) -> None:
    result = subprocess.run(
        command if os.geteuid() == 0 else ("sudo", *command),
        capture_output=True,
        text=True,
    )
    if result.returncode:
        print(
            f"network cleanup failed: {' '.join(command)}: {result.stderr.strip()}",
            file=sys.stderr,
        )


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="lfs")
    commands = parser.add_subparsers(dest="command", required=True)
    setup_parser = commands.add_parser(
        "setup", help="install the built system into a bootable image"
    )
    setup_parser.add_argument(
        "--no-gui", action="store_true", help="install the console system image"
    )
    build_parser = commands.add_parser(
        "build", help="fetch and build packages in order"
    )
    build_parser.add_argument(
        "--all",
        action="store_true",
        dest="all_mode",
        help="process all selected packages",
    )
    build_parser.add_argument(
        "--rebuild",
        "-r",
        action="store_true",
        dest="rebuild_mode",
        help="delete all .done markers and continue the normal build",
    )
    build_parser.add_argument(
        "--no-gui",
        action="store_true",
        help="build missing console packages using shared artifacts",
    )
    run_parser = commands.add_parser("run", help="boot MOS and lfs.img with QEMU")
    run_parser.add_argument(
        "--no-gui", action="store_true", help="boot the console system image"
    )
    run_parser.add_argument(
        "args",
        nargs=argparse.REMAINDER,
        help="additional QEMU arguments",
    )
    status_parser = commands.add_parser("status", help="show package and image state")
    status_parser.add_argument(
        "--no-gui", action="store_true", help="show console packages and image"
    )
    ns = parser.parse_args(argv)
    select_workspace(getattr(ns, "no_gui", False))
    if ns.command == "setup":
        setup(ns.no_gui)
    elif ns.command == "build":
        build(ns.all_mode, ns.rebuild_mode, ns.no_gui)
    elif ns.command == "run":
        qemu(ns.args[1:] if ns.args[:1] == ["--"] else ns.args)
    elif ns.command == "status":
        status(ns.no_gui)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main(sys.argv[1:]))
    except KeyboardInterrupt:
        print(f"\n{YELLOW}interrupted{RESET}", file=sys.stderr)
        raise SystemExit(130)
    except subprocess.CalledProcessError as error:
        command = " ".join(str(part) for part in error.cmd)
        print(
            f"{RED}error{RESET}: command failed ({error.returncode}): {command}",
            file=sys.stderr,
        )
        raise SystemExit(error.returncode or 1)
    except Exception as error:
        print(f"{RED}error{RESET}: {error}", file=sys.stderr)
        raise SystemExit(1)
