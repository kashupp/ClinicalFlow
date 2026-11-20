import sqlite3

import pytest

from scripts.create_database import SCHEMA


@pytest.fixture
def connection():
    conn = sqlite3.connect(":memory:")
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(SCHEMA)

    yield conn

    conn.close()


def insert_patient(conn, patient_id="PAT0001"):
    conn.execute(
        """
        INSERT INTO patients
        (patient_id, age, sex, enrollment_date)
        VALUES (?, ?, ?, ?)
        """,
        (patient_id, 45, "Male", "2025-01-01"),
    )


def test_database_tables_exist(connection):
    tables = {
        row[0]
        for row in connection.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
            """
        )
    }

    assert {"patients", "laboratory", "diagnoses"} <= tables


def test_insert_patient(connection):
    insert_patient(connection)

    result = connection.execute("SELECT patient_id, age, sex FROM patients").fetchone()

    assert result == ("PAT0001", 45, "Male")


def test_duplicate_patient_id_rejected(connection):
    insert_patient(connection)

    with pytest.raises(sqlite3.IntegrityError):
        insert_patient(connection)


def test_laboratory_record_requires_valid_patient(connection):
    with pytest.raises(sqlite3.IntegrityError):
        connection.execute(
            """
            INSERT INTO laboratory
            (patient_id, measurement_date, haemoglobin)
            VALUES (?, ?, ?)
            """,
            ("PAT9999", "2025-01-01", 130.0),
        )


def test_diagnosis_record_requires_valid_patient(connection):
    with pytest.raises(sqlite3.IntegrityError):
        connection.execute(
            """
            INSERT INTO diagnoses
            (patient_id, diagnosis_code, diagnosis_date)
            VALUES (?, ?, ?)
            """,
            ("PAT9999", "I10", "2025-01-01"),
        )


def test_patient_can_have_multiple_laboratory_records(connection):
    insert_patient(connection)

    for date, haemoglobin in [
        ("2025-01-01", 130.0),
        ("2025-02-01", 135.0),
    ]:
        connection.execute(
            """
            INSERT INTO laboratory
            (patient_id, measurement_date, haemoglobin)
            VALUES (?, ?, ?)
            """,
            ("PAT0001", date, haemoglobin),
        )

    count = connection.execute(
        """
        SELECT COUNT(*)
        FROM laboratory
        WHERE patient_id = ?
        """,
        ("PAT0001",),
    ).fetchone()[0]

    assert count == 2


def test_patient_can_have_multiple_diagnoses(connection):
    insert_patient(connection)

    for code in ["I10", "I25.1"]:
        connection.execute(
            """
            INSERT INTO diagnoses
            (patient_id, diagnosis_code, diagnosis_date)
            VALUES (?, ?, ?)
            """,
            ("PAT0001", code, "2025-01-01"),
        )

    count = connection.execute(
        """
        SELECT COUNT(*)
        FROM diagnoses
        WHERE patient_id = ?
        """,
        ("PAT0001",),
    ).fetchone()[0]

    assert count == 2


def test_foreign_key_check(connection):
    violations = connection.execute("PRAGMA foreign_key_check").fetchall()

    assert violations == []
