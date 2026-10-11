"""Validate MOS detection and bounded terminal traversal without compilation."""

import hashlib
import json
from pathlib import Path
import subprocess
import tarfile
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "src/packages/neofetch"


class NeofetchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        info = json.loads((PACKAGE / "package.json").read_text())
        archive = ROOT / ".workspace/sources" / info["archive"]
        if not archive.exists():
            raise unittest.SkipTest("Configured neofetch source archive is not cached")
        if hashlib.sha256(archive.read_bytes()).hexdigest() != info["sha256"]:
            raise AssertionError("Neofetch source archive checksum mismatch")
        cls.temporary = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.temporary.cleanup)
        with tarfile.open(archive) as source:
            source.extractall(cls.temporary.name, filter="data")
        directory = Path(cls.temporary.name) / ("neofetch-" + info["version"])
        command = ["patch", "--batch", "-p1", "-i", str(PACKAGE / "mos-kernel.patch")]
        subprocess.run(command + ["--dry-run"], cwd=directory, check=True,
                       capture_output=True)
        subprocess.run(command, cwd=directory, check=True, capture_output=True)
        script = directory / "neofetch"
        subprocess.run(["bash", "-n", str(script)], check=True)
        cls.functions = directory / "functions.sh"
        cls.functions.write_text(script.read_text().removesuffix('main "$@"\n'))

    def run_shell(self, commands):
        subprocess.run(
            ["bash", "-c", 'source "$1"\n' + commands,
             "neofetch-test", str(self.functions)],
            check=True, capture_output=True, timeout=5,
        )

    def test_mos_distribution_and_logo(self):
        self.run_shell('''
kernel_name=MOS
kernel_machine=x86_64
os_arch=on
ascii_distro=auto
get_os
get_distro
[[ $os == Linux && $distro == "MOS x86_64" ]] || exit 1
[[ $ascii_distro == "MOS x86_64" ]] || exit 2
get_distro_ascii
sys_locale=C
image_source=auto
print_ascii >/dev/null
[[ $lines -gt 1 && $ascii_len -gt 0 ]] || exit 3
unset distro
os_arch=off
ascii_distro=auto
get_distro
[[ $distro == MOS && $ascii_distro == MOS ]] || exit 4
''')

    def test_unsupported_logo_falls_back(self):
        self.run_shell('''
kernel_name=MOS
ascii_distro=unsupported
get_distro_ascii
[[ $ascii_distro == MOS && -n $ascii_data ]] || exit 1
sys_locale=C
image_source=auto
print_ascii >/dev/null
[[ $lines -gt 1 ]] || exit 2
''')

    def test_terminal_traversal_stops_at_zero_and_cycles(self):
        for traversal in (
            'printf 0',
            'printf 42',
            'case $1 in 42) printf 43 ;; *) printf 42 ;; esac',
        ):
            with self.subTest(traversal=traversal):
                self.run_shell('''
unset TERM_PROGRAM SSH_CONNECTION SSH_TTY WT_SESSION term
TERM=dumb
os=Linux
get_ppid() { ''' + traversal + '''; }
get_process_name() { printf bash; }
get_term
[[ $term == dumb && $term_run == 1 ]] || exit 1
''')


if __name__ == "__main__":
    unittest.main()
