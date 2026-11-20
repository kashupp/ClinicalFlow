import sqlite3
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
PROCESSED_DIR = DATA_DIR / "processed"
DATABASE_PATH = DATA_DIR / "clinicalflow.db"

DATASETS = {
    "patients": PROCESSED_DIR / "patients_clean.csv",
    "laboratory": PROCESSED_DIR / "laboratory_clean.csv",
    "diagnoses": PROCESSED_DIR / "diagnoses_clean.csv",
}


def load_csv(connection, table_name, file_path):
    df = pd.read_csv(file_path)

    df.to_sql(
        table_name,
        connection,
        if_exists="append",
        index=False,
    )
    return len(df)


def load_database():
    connection = sqlite3.connect(DATABASE_PATH)
    try:
        connection.execute("PRAGMA foreign_keys = ON")

        with connection:
            for table_name, file_path in DATASETS.items():
                if not file_path.exists():
                    raise FileNotFoundError(f"Dataset not found: {file_path}")

                count = load_csv(
                    connection,
                    table_name,
                    file_path,
                )

                print(f"{table_name}: {count} records loaded")

        print("\nDatabase loading completed successfully.")

    except Exception:
        print("\nDatabase loading failed. Transaction rolled back.")
        raise

    finally:
        connection.close()


if __name__ == "__main__":
    load_database()
