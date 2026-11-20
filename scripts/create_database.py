import argparse
import sqlite3
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATABASE_DIR = PROJECT_ROOT / "data"
DATABASE_PATH = DATABASE_DIR / "clinicalflow.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS patients (
    patient_id TEXT PRIMARY KEY,
    age INTEGER,
    sex TEXT,
    enrollment_date TEXT
);

CREATE TABLE IF NOT EXISTS laboratory (
    lab_id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id TEXT NOT NULL,
    measurement_date TEXT,
    haemoglobin REAL,
    creatinine REAL,
    total_cholesterol REAL,
    FOREIGN KEY (patient_id)
        REFERENCES patients(patient_id)
);

CREATE TABLE IF NOT EXISTS diagnoses (
    diagnosis_id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id TEXT NOT NULL,
    diagnosis_code TEXT,
    diagnosis_description TEXT,
    diagnosis_date TEXT,
    FOREIGN KEY (patient_id)
        REFERENCES patients(patient_id)
);

CREATE INDEX IF NOT EXISTS idx_laboratory_patient_id
    ON laboratory(patient_id);

CREATE INDEX IF NOT EXISTS idx_laboratory_measurement_date
    ON laboratory(measurement_date);

CREATE INDEX IF NOT EXISTS idx_diagnoses_patient_id
    ON diagnoses(patient_id);

CREATE INDEX IF NOT EXISTS idx_diagnoses_date
    ON diagnoses(diagnosis_date);
"""


def create_database(database_path=DATABASE_PATH):
    database_path.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(database_path)

    try:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.executescript(SCHEMA)
        connection.commit()

        print("SQLite database created successfully.")
        print(f"Database location: {database_path}")

        tables = connection.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
            AND name NOT LIKE 'sqlite_%'
            ORDER BY name;
            """
        ).fetchall()

        print("\nTables created:")
        for table in tables:
            print(f"- {table[0]}")

    finally:
        connection.close()


def main():
    parser = argparse.ArgumentParser(
        description="Create the ClinicalFlow SQLite database"
    )
    parser.add_argument(
        "--database",
        type=Path,
        default=DATABASE_PATH,
    )

    args = parser.parse_args()
    create_database(args.database)


if __name__ == "__main__":
    main()
