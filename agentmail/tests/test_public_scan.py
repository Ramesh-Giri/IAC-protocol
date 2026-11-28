import pathlib, subprocess, sys, unittest
ROOT = pathlib.Path(__file__).resolve().parents[2]

class PublicScanTest(unittest.TestCase):
    def test_tracked_files_hold_no_private_names_or_home_paths(self):
        r = subprocess.run([sys.executable, str(ROOT / 'agentmail/bin/public-scan')], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

if __name__ == '__main__':
    unittest.main()
