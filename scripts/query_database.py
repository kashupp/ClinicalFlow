import sqlite3
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATABASE_PATH = PROJECT_ROOT / "data" / "clinicalflow.db"

PATIENT_COUNTS_QUERY = """
SELECT sex, COUNT(*) AS patient_count
FROM patients
GROUP BY sex
ORDER BY sex
"""

AGE_SUMMARY_QUERY = """
SELECT
    COUNT(*) AS total_patients,
    ROUND(AVG(age), 1) AS average_age,
    MIN(age) AS minimum_age,
    MAX(age) AS maximum_age
FROM patients
"""

LAB_HISTORY_QUERY = """
SELECT
    patient_id,
    measurement_date,
    haemoglobin,
    creatinine,
    total_cholesterol
FROM laboratory
WHERE patient_id = ?
ORDER BY measurement_date
"""

PATIENT_DIAGNOSES_QUERY = """
SELECT
    p.patient_id,
    p.age,
    p.sex,
    d.diagnosis_code,
    d.diagnosis_description,
    d.diagnosis_date
FROM patients AS p
INNER JOIN diagnoses AS d
    ON p.patient_id = d.patient_id
ORDER BY p.patient_id
LIMIT ?
"""

ELEVATED_CREATININE_QUERY = """
SELECT
    patient_id,
    measurement_date,
    creatinine
FROM laboratory
WHERE creatinine > ?
ORDER BY creatinine DESC
"""


def execute_query(
    connection: sqlite3.Connection,
    query: str,
    params: tuple = (),
) -> pd.DataFrame:
    """Execute an SQL query and return the results as a DataFrame."""
    return pd.read_sql_query(query, connection, params=params)


def run_query(
    connection: sqlite3.Connection,
    title: str,
    query: str,
    params: tuple = (),
) -> None:
    """Execute and display an SQL query."""
    print(f"\n========== {title} ==========")
    result = execute_query(connection, query, params)
    print(result.to_string(index=False))


def main() -> None:
    if not DATABASE_PATH.exists():
        raise FileNotFoundError(
            f"Database not found: {DATABASE_PATH}. "
            "Run create_database.py and load_database.py first."
        )

    with sqlite3.connect(DATABASE_PATH) as connection:
        run_query(
            connection,
            "PATIENT COUNTS BY SEX",
            PATIENT_COUNTS_QUERY,
        )

        run_query(
            connection,
            "PATIENT AGE SUMMARY",
            AGE_SUMMARY_QUERY,
        )

        run_query(
            connection,
            "LABORATORY HISTORY FOR PAT0002",
            LAB_HISTORY_QUERY,
            ("PAT0002",),
        )

        run_query(
            connection,
            "PATIENTS AND DIAGNOSES",
            PATIENT_DIAGNOSES_QUERY,
            (10,),
        )

        run_query(
            connection,
            "PATIENTS WITH CREATININE ABOVE 100",
            ELEVATED_CREATININE_QUERY,
            (100,),
        )


if __name__ == "__main__":
    main()
