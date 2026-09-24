import os, sys, subprocess
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import archive_source

prefix = str(Path(os.environ["LFS_WORKSPACE"]) / "tools")
source = archive_source("gmp", "gmp-6.3.0.tar.xz", "gmp-6.3.0")
env = os.environ.copy()
env.update({"CC": "gcc", "CFLAGS": "-std=gnu17", "LDFLAGS": ""})
subprocess.run(
    [str(source / "configure"), "--prefix=" + prefix, "--disable-shared"],
    cwd=source,
    env=env,
    check=True,
)
subprocess.run(
    ["make", "-j" + str(os.cpu_count() or 1)], cwd=source, env=env, check=True
)
subprocess.run(["make", "install"], cwd=source, env=env, check=True)
