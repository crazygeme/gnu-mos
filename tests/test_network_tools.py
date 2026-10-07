"""Validate network-tool and guest build-tool package selection."""

import importlib.util
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

SPEC = importlib.util.spec_from_file_location("network_lfs", ROOT / "src/lfs.py")
lfs = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(lfs)


class NetworkTools(unittest.TestCase):
    def test_dependencies_precede_tools_in_both_architectures_and_profiles(self):
        names = ("libunistring", "libidn2", "libpsl", "ca-certificates", "wget", "make")
        for arch in ("x86", "x64"):
            for console in (False, True):
                with patch.object(lfs, "ARCH", arch):
                    selected = [path.name for path in lfs.selected_packages(console)]
                for name in names:
                    info = json.loads((ROOT / "src/packages" / name / "package.json").read_text())
                    self.assertIn(name, selected)
                    for dependency in info["dependencies"]:
                        self.assertLess(selected.index(dependency), selected.index(name))

if __name__ == "__main__":
    unittest.main()
