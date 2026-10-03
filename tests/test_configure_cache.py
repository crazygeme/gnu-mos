"""Validate configuration cache persistence without compiling packages."""

import importlib.util
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("package_lib", ROOT / "src/package_lib.py")
package_lib = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(package_lib)


class ConfigureCache(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.package = self.root / "packages/example"
        self.package.mkdir(parents=True)
        (self.package / "build.py").write_text("# Package recipe.\n")
        self.workspace = self.root / "workspace"
        self.build = self.workspace / "build/example"
        self.build.mkdir(parents=True)
        self.script = self.root / "source/configure"
        self.script.parent.mkdir()
        # The fixture implements a shell cache and records executed probes.
        self.script.write_text('''#!/bin/sh
for arg in "$@"; do
    case "$arg" in --cache-file=*) cache=${arg#--cache-file=} ;; esac
done
test -n "$cache" || exit 2
test ! -f "$cache" || . "$cache"
if test -z "$example_cv_probe"; then
    echo probe >> "$PROBE_LOG"
    example_cv_probe=yes
fi
echo 'example_cv_probe=yes' > "$cache"
echo configured > config.status
test ! -f "$FAIL_FILE" || exit 1
''')
        self.script.chmod(0o755)
        self.probes = self.root / "probes"
        self.env = {
            "PATH": "/usr/bin:/bin",
            "LFS_WORKSPACE": str(self.workspace),
            "LFS_PACKAGE_DIR": str(self.package),
            "PROBE_LOG": str(self.probes),
            "FAIL_FILE": str(self.root / "fail"),
        }

    def configure(self, *options, env=None, cwd=None):
        return package_lib.run_configure(
            [str(self.script), *options], cwd=cwd or self.build,
            env=self.env if env is None else env,
        )

    def count(self):
        return len(self.probes.read_text().splitlines())

    def test_cache_survives_empty_build_tree_and_regenerates_output(self):
        self.configure()
        shutil.rmtree(self.workspace / "build")
        self.build.mkdir(parents=True)
        self.configure()
        self.assertEqual(self.count(), 1)
        self.assertEqual((self.build / "config.status").read_text(), "configured\n")

    def test_native_and_cross_options_are_isolated(self):
        self.configure("--host=native")
        self.configure("--host=target")
        self.configure("--host=native")
        self.assertEqual(self.count(), 2)

    def test_build_directories_are_isolated(self):
        other = self.workspace / "build/other"
        other.mkdir()
        self.configure()
        self.configure(cwd=other)
        self.configure()
        self.assertEqual(self.count(), 2)

    def test_environment_recipe_and_script_changes_invalidate_cache(self):
        self.configure()
        env = dict(self.env, CFLAGS="-m32")
        self.configure(env=env)
        (self.package / "build.py").write_text("# Different recipe.\n")
        self.configure(env=env)
        self.script.write_text(self.script.read_text() + "# Different script.\n")
        self.configure(env=env)
        self.assertEqual(self.count(), 4)

    def test_site_contents_and_installed_dependencies_invalidate_cache(self):
        site = self.root / "config.site"
        site.write_text("example_cv_setting=yes\n")
        env = dict(self.env, CONFIG_SITE=str(site))
        self.configure(env=env)
        site.write_text("example_cv_setting=no\n")
        self.configure(env=env)
        artifacts = self.workspace / "artifacts"
        artifacts.mkdir()
        dependency = artifacts / "dependency.done"
        dependency.write_text('{"version": 1}\n')
        self.configure(env=env)
        dependency.write_text('{"version": 2}\n')
        self.configure(env=env)
        self.assertEqual(self.count(), 4)

    def test_own_completion_record_does_not_invalidate_cache(self):
        self.configure()
        artifacts = self.workspace / "artifacts"
        artifacts.mkdir()
        (artifacts / "example.done").write_text('{"version": 1}\n')
        self.configure()
        self.assertEqual(self.count(), 1)

    def test_failure_does_not_publish_cache(self):
        failure = Path(self.env["FAIL_FILE"])
        failure.touch()
        with self.assertRaises(subprocess.CalledProcessError):
            self.configure()
        self.assertFalse(list((self.workspace / "configure-cache").rglob("config.cache")))
        failure.unlink()
        self.configure()
        self.assertEqual(self.count(), 2)

    def test_failure_preserves_successful_persistent_cache(self):
        self.configure()
        saved = next((self.workspace / "configure-cache").rglob("config.cache"))
        original = saved.read_bytes()
        failure = Path(self.env["FAIL_FILE"])
        failure.touch()
        with self.assertRaises(subprocess.CalledProcessError):
            self.configure()
        self.assertEqual(saved.read_bytes(), original)
        failure.unlink()
        self.configure()
        self.assertEqual(self.count(), 1)

    def test_explicit_cache_argument_is_preserved(self):
        cache = self.root / "custom.cache"
        self.configure("--cache-file=" + str(cache))
        self.configure("--cache-file=" + str(cache))
        self.assertEqual(self.count(), 1)
        self.assertFalse((self.workspace / "configure-cache").exists())

    def test_changed_compiler_metadata_invalidates_cache(self):
        compiler = self.root / "cc"
        compiler.write_text("#!/bin/sh\nexit 0\n")
        compiler.chmod(0o755)
        env = dict(self.env, CC=str(compiler))
        self.configure(env=env)
        compiler.write_text("#!/bin/sh\n# Compiler update.\nexit 0\n")
        self.configure(env=env)
        self.assertEqual(self.count(), 2)


if __name__ == "__main__":
    unittest.main()
