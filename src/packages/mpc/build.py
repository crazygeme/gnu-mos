import os, sys, subprocess
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import archive_source

prefix = str(Path(os.environ["LFS_WORKSPACE"]) / "tools")
source = archive_source("mpc", "mpc-1.3.1.tar.gz", "mpc-1.3.1")
env = os.environ.copy()
env.update({"CC": "gcc", "CFLAGS": "-std=gnu89", "LDFLAGS": ""})
subprocess.run(
    [
        str(source / "configure"),
        "--prefix=" + prefix,
        "--disable-shared",
        "--with-gmp=" + prefix,
        "--with-mpfr=" + prefix,
    ],
    cwd=source,
    env=env,
    check=True,
)
subprocess.run(
    ["make", "-j" + str(os.cpu_count() or 1)], cwd=source, env=env, check=True
)
subprocess.run(["make", "install"], cwd=source, env=env, check=True)
