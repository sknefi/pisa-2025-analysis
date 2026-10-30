"""Kontrola vernosti prevodu vrátane kódov, identifikátorov a opakovaného spustenia."""

from pathlib import Path
import json
import sys
import tempfile
import unittest

import pandas as pd
import pyarrow.parquet as pq
import pyreadstat

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from prepare_data import build_dataset


class PrepareDataTest(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.root = Path(self.directory.name)
        self.source = self.root / "sample.sav"
        self.output = self.root / "sample.parquet"
        self.frame = pd.DataFrame({
            "ID": ["0001", "0002", "0003", "0004", "0005"],
            "AI": [1.0, 5.0, 99.0, float("nan"), 4.0],
            "LATE_DATA": [float("nan"), float("nan"), 1.25, 2.5, 3.75],
        })
        pyreadstat.write_sav(
            self.frame, self.source,
            column_labels={"ID": "Identifikátor", "AI": "Používanie AI", "LATE_DATA": "Číslo"},
            variable_value_labels={"AI": {1.0: "Nikdy", 5.0: "Denne", 99.0: "Bez odpovede"}},
            missing_ranges={"AI": [99.0]},
        )

    def tearDown(self):
        self.directory.cleanup()

    def test_all_values_columns_and_metadata_survive_multiple_chunks(self):
        info = build_dataset(self.source, self.output, chunk_size=2)
        expected, _ = pyreadstat.read_sav(self.source, user_missing=True, disable_datetime_conversion=True)
        actual = pd.read_parquet(self.output)
        pd.testing.assert_frame_equal(actual, expected)
        self.assertEqual(actual.loc[0, "ID"], "0001")
        self.assertEqual(actual.loc[2, "AI"], 99.0)
        self.assertEqual(info["rows"], 5)
        self.assertEqual(len(info["columns"]), 3)
        sidecar = json.loads(self.output.with_name("sample_metadata.json").read_text())
        embedded = json.loads(pq.read_schema(self.output).metadata[b"pisa_metadata"])
        self.assertEqual(sidecar, embedded)
        self.assertEqual(sidecar["columns"][1]["value_labels"][1], {"value": 5.0, "label": "Denne"})
        self.assertTrue(sidecar["columns"][1]["missing_ranges"])

    def test_repeated_run_reuses_file_and_changed_input_requires_force(self):
        first = build_dataset(self.source, self.output, chunk_size=2)
        before = self.output.stat().st_mtime_ns
        second = build_dataset(self.source, self.output, chunk_size=3)
        self.assertEqual(first["build_id"], second["build_id"])
        self.assertEqual(before, self.output.stat().st_mtime_ns)
        self.frame.loc[0, "AI"] = 2.0
        pyreadstat.write_sav(self.frame, self.source)
        with self.assertRaisesRegex(ValueError, "--force"):
            build_dataset(self.source, self.output)
        self.assertEqual(before, self.output.stat().st_mtime_ns)
        rebuilt = build_dataset(self.source, self.output, force=True)
        self.assertNotEqual(first["build_id"], rebuilt["build_id"])
        self.assertEqual(pd.read_parquet(self.output).loc[0, "AI"], 2.0)

    def test_mismatched_sidecar_is_not_silently_accepted(self):
        build_dataset(self.source, self.output, chunk_size=2)
        path = self.output.with_name("sample_metadata.json")
        metadata = json.loads(path.read_text())
        metadata["build_id"] = "incomplete-copy"
        path.write_text(json.dumps(metadata))
        with self.assertRaisesRegex(ValueError, "--force"):
            build_dataset(self.source, self.output)


if __name__ == "__main__":
    unittest.main()
