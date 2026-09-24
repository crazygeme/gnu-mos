import os, subprocess, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import archive_source

source = archive_source("gawk", "gawk-5.3.2.tar.xz", "gawk-5.3.2")
prefix = str(Path(os.environ["LFS_WORKSPACE"]) / "tools")
env = os.environ.copy()
env.update({"CC": "gcc", "CFLAGS": "-std=gnu17", "LDFLAGS": ""})
subprocess.run(
    [str(source / "configure"), "--prefix=" + prefix, "--without-mpfr"],
    cwd=source,
    env=env,
    check=True,
)
subprocess.run(
    ["make", "-j" + str(os.cpu_count() or 1)], cwd=source, env=env, check=True
)
subprocess.run(["make", "install"], cwd=source, env=env, check=True)
