import csv
import shutil
import sqlite3
import subprocess
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw"


@pytest.mark.integration
def test_complete_nextflow_pipeline(tmp_path):
    """Run the complete Nextflow pipeline and verify its outputs."""

    nextflow = shutil.which("nextflow")

    if nextflow is None:
        pytest.skip("Nextflow is not installed.")

    output_dir = tmp_path / "results"
    work_dir = tmp_path / "work"

    command = [
        nextflow,
        "run",
        "main.nf",
        "--raw_dir",
        str(RAW_DIR),
        "--outdir",
        str(output_dir),
        "-work-dir",
        str(work_dir),
        "-ansi-log",
        "false",
    ]

    result = subprocess.run(
        command,
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=600,
        check=False,
    )

    assert result.returncode == 0, (
        f"Nextflow pipeline failed.\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
    )

    # Verify expected output files.
    expected_files = [
        output_dir / "qc" / "qc_report.csv",
        output_dir / "processed" / "patients_clean.csv",
        output_dir / "processed" / "laboratory_clean.csv",
        output_dir / "processed" / "diagnoses_clean.csv",
        output_dir / "cleaning" / "cleaning_report.csv",
        output_dir / "database" / "clinicalflow.db",
    ]

    for file_path in expected_files:
        assert file_path.is_file(), f"Missing output: {file_path}"

    # Verify QC results.
    with open(
        output_dir / "qc" / "qc_report.csv",
        newline="",
    ) as handle:
        qc_rows = list(csv.DictReader(handle))

    assert len(qc_rows) == 24
    assert all(row["status"] == "PASS" for row in qc_rows)

    # Verify SQLite database contents.
    database_path = output_dir / "database" / "clinicalflow.db"

    with sqlite3.connect(database_path) as connection:
        expected_counts = {
            "patients": 1000,
            "laboratory": 1979,
            "diagnoses": 1510,
        }

        for table, expected_count in expected_counts.items():
            actual_count = connection.execute(
                f"SELECT COUNT(*) FROM {table}"
            ).fetchone()[0]

            assert actual_count == expected_count, (
                f"{table}: expected {expected_count}, found {actual_count}"
            )
