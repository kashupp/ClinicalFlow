import sqlite3

import pytest

from scripts.create_database import SCHEMA
from scripts.query_database import (
    AGE_SUMMARY_QUERY,
    ELEVATED_CREATININE_QUERY,
    LAB_HISTORY_QUERY,
    PATIENT_COUNTS_QUERY,
    PATIENT_DIAGNOSES_QUERY,
    execute_query,
)


@pytest.fixture
def database():
    """Create an isolated in-memory database for query testing."""
    connection = sqlite3.connect(":memory:")
    connection.execute("PRAGMA foreign_keys = ON")
    connection.executescript(SCHEMA)

    patients = [
        ("PAT0001", 45, "Female", "2025-01-01"),
        ("PAT0002", 60, "Male", "2025-02-01"),
        ("PAT0003", 75, "Female", "2025-03-01"),
    ]

    connection.executemany(
        """
        INSERT INTO patients
        (patient_id, age, sex, enrollment_date)
        VALUES (?, ?, ?, ?)
        """,
        patients,
    )

    laboratory = [
        ("PAT0001", "2025-04-01", 130.0, 70.0, 5.0),
        ("PAT0002", "2025-04-02", 145.0, 120.0, 6.0),
        ("PAT0003", "2025-04-03", 125.0, 90.0, 4.5),
    ]

    connection.executemany(
        """
        INSERT INTO laboratory
        (patient_id, measurement_date, haemoglobin,
         creatinine, total_cholesterol)
        VALUES (?, ?, ?, ?, ?)
        """,
        laboratory,
    )

    diagnoses = [
        ("PAT0001", "I10", "Hypertension", "2025-04-01"),
        ("PAT0002", "I25.1", "Heart disease", "2025-04-02"),
    ]

    connection.executemany(
        """
        INSERT INTO diagnoses
        (patient_id, diagnosis_code, diagnosis_description,
         diagnosis_date)
        VALUES (?, ?, ?, ?)
        """,
        diagnoses,
    )

    yield connection
    connection.close()


def test_patient_counts_by_sex(database):
    result = execute_query(database, PATIENT_COUNTS_QUERY)

    counts = dict(zip(result["sex"], result["patient_count"]))

    assert counts == {"Female": 2, "Male": 1}


def test_patient_age_summary(database):
    result = execute_query(database, AGE_SUMMARY_QUERY)

    assert result.loc[0, "total_patients"] == 3
    assert result.loc[0, "average_age"] == 60.0
    assert result.loc[0, "minimum_age"] == 45
    assert result.loc[0, "maximum_age"] == 75


def test_laboratory_history_for_patient(database):
    result = execute_query(
        database,
        LAB_HISTORY_QUERY,
        ("PAT0002",),
    )

    assert len(result) == 1
    assert result.loc[0, "patient_id"] == "PAT0002"
    assert result.loc[0, "creatinine"] == 120.0


def test_patient_diagnoses_join(database):
    result = execute_query(
        database,
        PATIENT_DIAGNOSES_QUERY,
        (10,),
    )

    assert len(result) == 2
    assert "patient_id" in result.columns
    assert "diagnosis_code" in result.columns
    assert set(result["patient_id"]) == {"PAT0001", "PAT0002"}


def test_elevated_creatinine_query(database):
    result = execute_query(
        database,
        ELEVATED_CREATININE_QUERY,
        (100,),
    )

    assert len(result) == 1
    assert result.loc[0, "patient_id"] == "PAT0002"
    assert result.loc[0, "creatinine"] == 120.0


def test_creatinine_query_returns_no_results_above_threshold(database):
    result = execute_query(
        database,
        ELEVATED_CREATININE_QUERY,
        (200,),
    )

    assert result.empty
