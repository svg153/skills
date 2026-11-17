from __future__ import annotations

import contextlib
import importlib.util
import io
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

distribution_spec = importlib.util.spec_from_file_location("generate_distribution", SCRIPTS / "generate-distribution.py")
generate_distribution = importlib.util.module_from_spec(distribution_spec)
sys.modules["generate_distribution"] = generate_distribution
assert distribution_spec.loader is not None
distribution_spec.loader.exec_module(generate_distribution)

capability_spec = importlib.util.spec_from_file_location("generate_capability_plugin", SCRIPTS / "generate-capability-plugin.py")
generate_capability_plugin = importlib.util.module_from_spec(capability_spec)
sys.modules["generate_capability_plugin"] = generate_capability_plugin
assert capability_spec.loader is not None
capability_spec.loader.exec_module(generate_capability_plugin)

EXPECTED = '{\n  "name": "fixture"\n}\n'


class DistributionCheckLineEndingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.root, True)
        self.outputs = {Path("plugin.json"): EXPECTED}
        patcher = mock.patch.object(generate_distribution, "ROOT", self.root)
        patcher.start()
        self.addCleanup(patcher.stop)

    def run_check(self) -> tuple[int, str]:
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr), contextlib.redirect_stdout(io.StringIO()):
            code = generate_distribution.check(self.outputs)
        return code, stderr.getvalue()

    def test_lf_copy_passes_check(self) -> None:
        (self.root / "plugin.json").write_bytes(EXPECTED.encode("utf-8"))
        code, _ = self.run_check()
        self.assertEqual(code, 0)

    def test_crlf_copy_fails_check_as_line_ending_drift(self) -> None:
        (self.root / "plugin.json").write_bytes(EXPECTED.replace("\n", "\r\n").encode("utf-8"))
        code, stderr = self.run_check()
        self.assertEqual(code, 1)
        self.assertIn("plugin.json", stderr)
        self.assertIn("line-ending", stderr)


class CapabilityCheckLineEndingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.package_root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.package_root, True)
        self.outputs = {Path("plugin.json"): EXPECTED}

    def run_check(self) -> tuple[int, str]:
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr), contextlib.redirect_stdout(io.StringIO()):
            code = generate_capability_plugin.check(self.package_root, self.outputs)
        return code, stderr.getvalue()

    def test_lf_copy_passes_check(self) -> None:
        (self.package_root / "plugin.json").write_bytes(EXPECTED.encode("utf-8"))
        code, _ = self.run_check()
        self.assertEqual(code, 0)

    def test_crlf_copy_fails_check_as_line_ending_drift(self) -> None:
        (self.package_root / "plugin.json").write_bytes(EXPECTED.replace("\n", "\r\n").encode("utf-8"))
        code, stderr = self.run_check()
        self.assertEqual(code, 1)
        self.assertIn("plugin.json", stderr)
        self.assertIn("line-ending", stderr)


if __name__ == "__main__":
    unittest.main()
