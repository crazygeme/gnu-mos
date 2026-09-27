import os, shutil, subprocess, tarfile
from pathlib import Path

mos = Path(os.environ["LFS_SOURCES"]) / "mos"
if not (mos / "Makefile").exists():
    raise SystemExit(f"MOS checkout missing: {mos}; run ./lfs fetch")
build = Path(os.environ["LFS_WORKSPACE"]) / "build/mos"
archive = build.parent / "mos-source.tar"
if build.exists():
    shutil.rmtree(build)
build.mkdir(parents=True)
with archive.open("wb") as output:
    subprocess.run(
        ["git", "-C", str(mos), "archive", "--format=tar", "HEAD"],
        stdout=output,
        check=True,
    )
with tarfile.open(archive) as source:
    source.extractall(build, filter="data")
patch = str(Path(__file__).with_name("meminfo-cache-accounting.patch").resolve())
patch_command = ["patch", "-p1", "--forward", "--batch", "-i", patch]
subprocess.run([*patch_command, "--dry-run"], cwd=build, check=True)
subprocess.run(patch_command, cwd=build, check=True)
subprocess.run(
    ["make", "-j4", "ARCH=x86", "BUILD=release"],
    cwd=build,
    check=True,
)
target = Path(os.environ["LFS_SYSROOT"]) / "boot/kernel"
target.parent.mkdir(parents=True, exist_ok=True)
shutil.copy2(build / "out/x86/release/kernel", target)
