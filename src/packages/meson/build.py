import os
import shutil
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import archive_source

source = archive_source("meson", "meson-1.8.3.tar.gz", "meson-1.8.3")
tools = Path(os.environ["LFS_WORKSPACE"]) / "tools"
module_dir = tools / "lib/meson"
module_dir.mkdir(parents=True, exist_ok=True)
for item in (source / "mesonbuild",):
    destination = module_dir / item.name
    if destination.exists():
        shutil.rmtree(destination)
    shutil.copytree(item, destination)
launcher = tools / "bin/meson"
launcher.parent.mkdir(parents=True, exist_ok=True)
launcher.write_text(
    "#!/usr/bin/env python3.13\n"
    "import sys\n"
    "sys.path.insert(0, " + repr(str(module_dir)) + ")\n"
    "from mesonbuild.mesonmain import main\n"
    "raise SystemExit(main())\n",
    encoding="utf-8",
)
launcher.chmod(0o755)
