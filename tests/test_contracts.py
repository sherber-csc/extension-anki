from __future__ import annotations

import unittest
from pathlib import Path

from backend.contracts import render_extension_protocol_js


class ContractsSyncTestCase(unittest.TestCase):
    def test_extension_protocol_is_generated_from_backend_truth(self) -> None:
        protocol_path = Path("extension/protocol.js")
        self.assertTrue(protocol_path.exists())
        self.assertEqual(render_extension_protocol_js(), protocol_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
