import os, sys, subprocess
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import archive_source

prefix = str(Path(os.environ["LFS_WORKSPACE"]) / "tools")
source = archive_source("mpfr", "mpfr-4.2.2.tar.xz", "mpfr-4.2.2")
env = os.environ.copy()
env.update({"CC": "gcc", "CFLAGS": "-std=gnu89", "LDFLAGS": ""})
subprocess.run(
    [
        str(source / "configure"),
        "--prefix=" + prefix,
        "--disable-shared",
        "--with-gmp=" + prefix,
    ],
    cwd=source,
    env=env,
    check=True,
)
subprocess.run(["make", "-j4"], cwd=source, env=env, check=True)
subprocess.run(["make", "install"], cwd=source, env=env, check=True)
