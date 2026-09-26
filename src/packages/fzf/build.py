import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import archive_source

source = archive_source("fzf", "fzf-0.65.2.tar.gz", "fzf-0.65.2")
workspace = Path(os.environ["LFS_WORKSPACE"])
sysroot = Path(os.environ["LFS_SYSROOT"])
target = sysroot / "usr/bin/fzf"
target.parent.mkdir(parents=True, exist_ok=True)
env = os.environ.copy()
env.update(
    {
        "GOOS": "linux",
        "GOARCH": "386",
        "CGO_ENABLED": "0",
        "GOTOOLCHAIN": "local",
        "GOPROXY": "https://goproxy.cn,direct",
        "GOPATH": str(workspace / "go-path"),
        "GOCACHE": str(workspace / "go-cache"),
    }
)
subprocess.run(
    [str(workspace / "tools/go/bin/go"), "build", "-o", str(target), "."],
    cwd=source,
    env=env,
    check=True,
)
shell_dir = sysroot / "usr/share/fzf"
shell_dir.mkdir(parents=True, exist_ok=True)
for name in ("completion.bash", "key-bindings.bash"):
    (shell_dir / name).write_bytes((source / "shell" / name).read_bytes())
