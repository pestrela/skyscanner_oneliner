import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from main import parse

RUNS_DIR = Path(__file__).parent / "runs"


class TestIntegration(unittest.TestCase):
    pass


def _make_test(in_path, out_path):
    def test(self):
        text = in_path.read_text(encoding="utf-8")
        expected = out_path.read_text(encoding="utf-8").splitlines()
        self.assertEqual(parse(text), expected)
    return test


for _in_path in sorted(RUNS_DIR.glob("*.in")):
    _out_path = _in_path.with_suffix(".out")
    if _out_path.exists():
        setattr(TestIntegration, f"test_{_in_path.stem}", _make_test(_in_path, _out_path))


if __name__ == "__main__":
    unittest.main()
